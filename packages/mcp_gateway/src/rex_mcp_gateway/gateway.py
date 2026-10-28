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


_DESTRUCTIVE_KEYS = ("archived", "in_trash", "trash", "delete")


def _is_destructive(args: dict[str, Any]) -> bool:
    """True if args ask the tool to archive/trash/delete something (truthy flag, any nesting level one deep)."""
    for k, v in args.items():
        if k in _DESTRUCTIVE_KEYS and v not in (False, None, "", "false", 0):
            return True
        if isinstance(v, dict) and _is_destructive(v):
            return True
    return False


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
        self._tools: dict[str, list[Any]] = {}  # server -> MCP tool list, fetched once (saves a round trip per call)
        self._pending: dict[str, PendingAction] = {}
        self._undo_history: dict[str, dict[str, Any]] = {}
        self._undo_order: list[str] = []

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
            except Exception as exc:
                logger.warning("could not connect MCP server %s (skipping): %s", name, exc)
        return self

    async def __aexit__(self, *exc: object) -> None:
        self._clients.clear()
        self._tools.clear()
        await self._stack.__aexit__(*exc)

    def connected(self) -> list[str]:
        return list(self._clients)

    async def _client(self, server: str) -> Client:
        try:
            return self._clients[server]
        except KeyError:
            raise ToolDenied(f"server {server!r} is not connected") from None

    async def _server_tools(self, server: str) -> list[Any]:
        if server not in self._tools:
            self._tools[server] = (await (await self._client(server)).list_tools()).tools
        return self._tools[server]

    # ---------- discovery ----------
    async def list_tools(self, specialist: str) -> list[ToolInfo]:
        out: list[ToolInfo] = []
        for server in self.connected():
            if not self.registry.allowed(specialist, server):
                continue
            try:
                listed = await self._server_tools(server)
            except Exception:
                logger.exception("could not list tools for %s", server)
                continue
            for t in listed:
                if not self.registry.exposes(specialist, server, t.name):
                    continue
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
        known = {t.name for t in await self._server_tools(server)}
        if tool not in known:
            raise ToolDenied(f"unknown tool {qualified_tool!r}")
        if not self.registry.exposes(specialist, server, tool):
            raise ToolDenied(f"{specialist!r} may not use {qualified_tool!r}")

        summary = summary or f"{qualified_tool} {json.dumps(args, ensure_ascii=False)[:120]}"
        tier = self.registry.tier_for(server, tool)
        if _is_destructive(args):
            tier = "A"  # e.g. notion patch-page with archived/in_trash: a W tool must not delete without approval
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

    async def undo(self, action_id: str | None = None) -> ToolOutcome:
        """Reverse a previous Tier W action using its compensating undo tool."""
        if action_id is not None:
            if action_id not in self._undo_history:
                raise KeyError(f"no undo available for action {action_id!r}")
            key = action_id
        else:
            if not self._undo_order:
                raise RuntimeError("Nothing to undo.")
            key = self._undo_order[-1]

        undo_spec = self._undo_history.pop(key)
        if key in self._undo_order:
            self._undo_order.remove(key)

        undo_tool = undo_spec["tool"]
        undo_args = undo_spec["args"]
        server, _, tool = undo_tool.partition(".")

        client = await self._client(server)
        policy = self.registry.servers[server].policy(tool)
        res = await asyncio.wait_for(client.call_tool(tool, undo_args), timeout=policy.timeout_s)
        text = "\n".join(getattr(c, "text", "") for c in res.content if getattr(c, "text", None))

        await self._emit(
            tool=undo_tool,
            tier="W",
            status="undone",
            summary=f"Reverted action via {undo_tool}",
            args=undo_args,
            result={"text": text[:500]},
            action_id=key,
        )
        return ToolOutcome(ok=True, text=f"Undone: reverted {undo_tool}.", raw=res, action_id=key)

    async def _execute(
        self, qualified_tool: str, tier: Tier, args: dict[str, Any], summary: str, action_id: str | None = None
    ) -> ToolOutcome:
        server, _, tool = qualified_tool.partition(".")
        policy = self.registry.servers[server].policy(tool)
        call_id = action_id or uuid.uuid4().hex[:10]
        await self._emit(qualified_tool, tier, "started", summary, args, action_id=call_id)
        last_err = ""
        # Retry only reads: a timed-out write may already have run, and repeating it would duplicate it.
        for attempt in range(2 if tier == "R" else 1):
            try:
                client = await self._client(server)
                res = await asyncio.wait_for(client.call_tool(tool, args), timeout=policy.timeout_s)
                text = "\n".join(getattr(c, "text", "") for c in res.content if getattr(c, "text", None))
                if res.is_error:
                    await self._emit(
                        qualified_tool, tier, "failed", summary, args, result={"error": text}, action_id=call_id
                    )
                    return ToolOutcome(ok=False, text=f"The tool failed: {text}", raw=res, action_id=call_id)

                undo_spec = None
                if policy.undo:
                    undo_tool = f"{server}.{policy.undo}"
                    undo_args: dict[str, Any] = {}
                    parsed = None
                    try:
                        parsed = json.loads(text) if text else None
                    except Exception:
                        pass
                    if isinstance(parsed, dict) and "id" in parsed:
                        item_id = str(parsed["id"])
                        if "delete_event" in policy.undo:
                            undo_args = {"event_id": item_id}
                        elif "delete" in policy.undo or "archive" in policy.undo:
                            undo_args = {"event_id": item_id} if "event_id" in policy.undo else {"id": item_id}
                        else:
                            undo_args = {"id": item_id}
                    elif "id" in args:
                        undo_args = {"id": str(args["id"])}
                    elif "event_id" in args:
                        undo_args = {"event_id": str(args["event_id"])}

                    if undo_args:
                        undo_spec = {"tool": undo_tool, "args": undo_args}
                        self._undo_history[call_id] = undo_spec
                        self._undo_order.append(call_id)

                await self._emit(
                    qualified_tool,
                    tier,
                    "succeeded",
                    summary,
                    args,
                    result={"text": text[:500]},
                    action_id=call_id,
                    undo=undo_spec,
                    undo_available=bool(undo_spec),
                )
                return ToolOutcome(ok=True, text=wrap_untrusted(qualified_tool, text), raw=res, action_id=call_id)
            except (TimeoutError, ConnectionError, OSError, ToolDenied) as exc:
                last_err = f"{type(exc).__name__}: {exc}"
                logger.warning("tool %s attempt %d failed: %s", qualified_tool, attempt + 1, last_err)
        await self._emit(qualified_tool, tier, "failed", summary, args, result={"error": last_err}, action_id=call_id)
        return ToolOutcome(ok=False, text=f"The tool failed: {last_err}", action_id=call_id)

    async def _emit(
        self,
        tool: str,
        tier: Tier,
        status: str,
        summary: str,
        args: dict[str, Any],
        result: dict[str, Any] | None = None,
        action_id: str | None = None,
        undo: dict[str, Any] | None = None,
        undo_available: bool = False,
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
            undo=undo,
            undo_available=undo_available,
            trace_id=action_id,
        )
        try:
            await self._on_event(ev)
        except Exception:
            logger.exception("event sink failed")
