"""Helpers for live workflow tests (real LLM + real MCP servers, text mode, no audio)."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from livekit.agents import AgentSession

from rex_agent.config import AgentConfig
from rex_agent.main import Rex, load_runtime_registry
from rex_agent.models import build_llm
from rex_agent.tools_bridge import build_tools
from rex_mcp_gateway.gateway import Gateway
from rex_mcp_gateway.registry import Registry
from rex_shared.schemas import ActionEvent


@asynccontextmanager
async def rex_session(
    events: list[ActionEvent] | None = None, registry: Registry | None = None
) -> AsyncIterator[tuple[AgentSession, Gateway]]:
    """Yield (session, gateway) with Rex running in text mode against the runtime MCP servers.

    Usage:
        async with rex_session(events) as (session, gw):
            result = await session.run(user_input="...")
            result.expect.contains_function_call(name="calendar__create_event")
    """

    async def sink(ev: ActionEvent) -> None:
        if events is not None:
            events.append(ev)

    async with Gateway(registry or load_runtime_registry(), on_event=sink) as gw:
        tools = await build_tools(gw, "rex")
        async with AgentSession(llm=build_llm()) as session:
            await session.start(Rex(AgentConfig.from_env(), gateway=gw, tools=tools))
            yield session, gw
