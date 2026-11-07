"""Expose gateway (MCP) tools to the LiveKit agent as function tools with their real JSON schemas.

Every call still goes through the gateway, so allow-lists, tiers, approvals and audit events apply.
"""

from __future__ import annotations

import contextlib
import json
from typing import Any

from livekit.agents import RunContext, function_tool
from livekit.agents.llm import RawFunctionTool

from rex_agent.brain.acks import tool_filler
from rex_mcp_gateway.gateway import Gateway, ToolInfo

# Speak a filler only if the tool keeps the line silent this long; quick tools stay quiet.
FILLER_DELAY_S = 0.7
_filled_speech: set[str] = set()  # one filler per reply, even when the LLM calls several tools

_TIER_HINT = {
    "R": "Read-only.",
    "W": "Makes a reversible change.",
    "A": "Affects other people or can't be undone: the call returns an approval request; it needs the user's approval "
    "before it runs.",
}


def livekit_name(qualified: str) -> str:
    return qualified.replace(".", "__")


def qualified_name(lk_name: str) -> str:
    return lk_name.replace("__", ".", 1)


def _summary(info: ToolInfo, args: dict[str, Any]) -> str:
    shown = ", ".join(f"{k}={json.dumps(v, ensure_ascii=False)[:60]}" for k, v in args.items())
    return f"{info.server} · {info.name}({shown})"


def filler_once(context: RunContext, server: str):
    """A filler line for a slow tool, but only once per reply: a 6-step task must not say "On it." six times."""
    speech_id = context.speech_handle.id
    if speech_id in _filled_speech:
        return contextlib.nullcontext()
    _filled_speech.add(speech_id)
    lang = getattr(context.session.current_agent, "_lang", None)
    return context.with_filler(tool_filler(server, lang), delay=FILLER_DELAY_S)


def _make_tool(gw: Gateway, specialist: str, info: ToolInfo) -> RawFunctionTool:
    async def handler(context: RunContext, raw_arguments: dict[str, object]) -> str:
        call = gw.call(specialist, info.qualified_name, dict(raw_arguments), summary=_summary(info, raw_arguments))
        async with filler_once(context, info.server):
            return (await call).text

    schema = {
        "name": livekit_name(info.qualified_name),
        "description": f"{info.description.strip()} [{_TIER_HINT[info.tier]}]",
        "parameters": info.input_schema or {"type": "object", "properties": {}},
    }
    return function_tool(handler, raw_schema=schema)


async def build_tools(gw: Gateway, specialist: str = "rex") -> list[RawFunctionTool]:
    return [_make_tool(gw, specialist, info) for info in await gw.list_tools(specialist)]
