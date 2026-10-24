"""The one door every tool call goes through.

- Specialist allow-lists: a specialist can only reach the servers it is allowed to.
- Permission tiers: R and W run; A (affects other people / irreversible) returns
  NeedsApproval and only runs after approve(action_id).
- Every call emits ActionEvents (started / awaiting_approval / succeeded / failed / denied).
- Tool output is wrapped as untrusted data before it reaches an LLM.
"""

from __future__ import annotations

import asyncio
import json
import logging
import uuid
from collections.abc import Awaitable, Callable
from contextlib import AsyncExitStack
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any

from mcp import Client, StdioServerParameters

from rex_mcp_gateway.registry import Registry, Tier
from rex_shared.schemas import ActionEvent

logger = logging.getLogger("rex.gateway")
EventSink = Callable[[ActionEvent], Awaitable[None]]


class ToolDenied(Exception):
    """Specialist not allowed to use this server, or the tool doesn't exist."""


@dataclass
class ToolInfo:
    qualified_name: str  # "server.tool"
    server: str
    name: str
    description: str
    input_schema: dict[str, Any]
    tier: Tier


@dataclass
class ToolOutcome:
    ok: bool
    text: str
    raw: Any = None
    action_id: str | None = None


@dataclass
class NeedsApproval:
    action_id: str
    summary: str
    tool: str
    ok: bool = False
    text: str = ""

    def __post_init__(self) -> None:
        self.text = (
            f"This action needs the user's approval: {self.summary}. Ask the user to confirm. "
            f"If they say yes, call approve_action with action_id='{self.action_id}'; if no, call deny_action."
        )


@dataclass
class PendingAction:
    action_id: str
    specialist: str
    tool: str
    args: dict[str, Any]
    summary: str
    expires_at: datetime
    event_ts: datetime = field(default_factory=lambda: datetime.now(UTC))


def wrap_untrusted(source: str, text: str) -> str:
    return f'<untrusted_data source="{source}">\n{text}\n</untrusted_data>'


class Gateway:
    def __init__(
        self,
        registry: Registry,
        on_event: EventSink | None = None,
        approval_ttl_s: float = 120.0,
    ) -> None:
        self.registry = registry
        self._on_event = on_event
        self._ttl = timedelta(seconds=approval_ttl_s)
        self._stack = AsyncExitStack()
        self._clients: dict[str, Client] = {}
        self._pending: dict[str, PendingAction] = {}

    # ---------- connections ----------
    # MCP clients run on anyio task groups, so they must be opened and closed in the same task.
    # Use the gateway as `async with Gateway(...) as gw:` in one long-lived task (the agent entrypoint).
    async def __aenter__(self) -> Gateway:
        await self._stack.__aenter__()
        for name, spec in self.registry.servers.items():
            try:
                if spec.inprocess is not None:
                    target: Any = spec.inprocess
                elif spec.command:
                    target = StdioServerParameters(command=spec.command[0], args=spec.command[1:], env=spec.env or None)
                elif spec.url:
                    target = spec.url
                else:
                    raise ValueError("no transport configured")
                self._clients[name] = await self._stack.enter_async_context(Client(target))
                logger.info("connected MCP server %s", name)
            except Exception:
                logger.exception("could not connect MCP server %s (skipping)", name)
        return self

    async def __aexit__(self, *exc: object) -> None:
        self._clients.clear()
        await self._stack.__aexit__(*exc)

    def connected(self) -> list[str]:
        return list(self._clients)

    async def _client(self, server: str) -> Client:
        try:
            return self._clients[server]
        except KeyError:
            raise ToolDenied(f"server {server!r} is not connected") from None

    # ---------- discovery ----------
    async def list_tools(self, specialist: str) -> list[ToolInfo]:
        out: list[ToolInfo] = []
        for server in self.connected():
            if not self.registry.allowed(specialist, server):
                continue
            try:
                client = await self._client(server)
                listed = await client.list_tools()
            except Exception:
                logger.exception("could not list tools for %s", server)
                continue
            for t in listed.tools:
                out.append(
                    ToolInfo(
                        qualified_name=f"{server}.{t.name}",
                        server=server,
                        name=t.name,
                        description=t.description or "",
                        input_schema=dict(t.input_schema or {"type": "object", "properties": {}}),
                        tier=self.registry.tier_for(server, t.name),
                    )
                )
        return out

    # ---------- calls ----------
    async def call(
        self, specialist: str, qualified_tool: str, args: dict[str, Any], summary: str | None = None
    ) -> ToolOutcome | NeedsApproval:
        server, _, tool = qualified_tool.partition(".")
        if server not in self.registry.servers or not tool:
            raise ToolDenied(f"unknown tool {qualified_tool!r}")
        if not self.registry.allowed(specialist, server):
            raise ToolDenied(f"{specialist!r} may not use {server!r}")
        known = {t.name for t in (await (await self._client(server)).list_tools()).tools}
        if tool not in known:
            raise ToolDenied(f"unknown tool {qualified_tool!r}")

        summary = summary or f"{qualified_tool} {json.dumps(args, ensure_ascii=False)[:120]}"
        tier = self.registry.tier_for(server, tool)
        if tier == "A":
            action_id = uuid.uuid4().hex[:10]
            self._pending[action_id] = PendingAction(
                action_id, specialist, qualified_tool, args, summary, datetime.now(UTC) + self._ttl
            )
            await self._emit(qualified_tool, tier, "awaiting_approval", summary, args, action_id=action_id)
            return NeedsApproval(action_id=action_id, summary=summary, tool=qualified_tool)
        return await self._execute(qualified_tool, tier, args, summary)

    def pending(self) -> list[PendingAction]:
        now = datetime.now(UTC)
        for k in [k for k, p in self._pending.items() if p.expires_at < now]:
            self._pending.pop(k)
        return list(self._pending.values())

    async def approve(self, action_id: str) -> ToolOutcome:
        self.pending()  # drop expired
        p = self._pending.pop(action_id)  # KeyError if unknown / expired / already handled
        return await self._execute(p.tool, "A", p.args, p.summary, action_id=action_id)

    async def deny(self, action_id: str) -> None:
        p = self._pending.pop(action_id)
        await self._emit(p.tool, "A", "denied", p.summary, p.args, action_id=action_id)

    async def _execute(
        self, qualified_tool: str, tier: Tier, args: dict[str, Any], summary: str, action_id: str | None = None
    ) -> ToolOutcome:
        server, _, tool = qualified_tool.partition(".")
        policy = self.registry.servers[server].policy(tool)
        await self._emit(qualified_tool, tier, "started", summary, args, action_id=action_id)
        last_err = ""
        for attempt in range(2):  # one retry on exceptions / timeouts
            try:
                client = await self._client(server)
                res = await asyncio.wait_for(client.call_tool(tool, args), timeout=policy.timeout_s)
                text = "\n".join(getattr(c, "text", "") for c in res.content if getattr(c, "text", None))
                if res.is_error:
                    await self._emit(qualified_tool, tier, "failed", summary, args, result={"error": text})
                    return ToolOutcome(ok=False, text=f"The tool failed: {text}", raw=res, action_id=action_id)
                await self._emit(
                    qualified_tool, tier, "succeeded", summary, args, result={"text": text[:500]}, action_id=action_id
                )
                return ToolOutcome(ok=True, text=wrap_untrusted(qualified_tool, text), raw=res, action_id=action_id)
            except (TimeoutError, ConnectionError, OSError, ToolDenied) as exc:
                last_err = f"{type(exc).__name__}: {exc}"
                logger.warning("tool %s attempt %d failed: %s", qualified_tool, attempt + 1, last_err)
        await self._emit(qualified_tool, tier, "failed", summary, args, result={"error": last_err})
        return ToolOutcome(ok=False, text=f"The tool failed: {last_err}", action_id=action_id)

    async def _emit(
        self,
        tool: str,
        tier: Tier,
        status: str,
        summary: str,
        args: dict[str, Any],
        result: dict[str, Any] | None = None,
        action_id: str | None = None,
    ) -> None:
        if self._on_event is None:
            return
        ev = ActionEvent(
            id=uuid.uuid4(),
            ts=datetime.now(UTC),
            tool=tool,
            tier=tier,
            status=status,  # type: ignore[arg-type]
            summary=summary,
            args_redacted={k: (v if len(str(v)) < 200 else str(v)[:200] + "…") for k, v in args.items()},
            result_redacted=result,
            trace_id=action_id,
        )
        try:
            await self._on_event(ev)
        except Exception:
            logger.exception("event sink failed")
