"""Expose gateway (MCP) tools to the LiveKit agent as function tools with their real JSON schemas.

Every call still goes through the gateway, so allow-lists, tiers, approvals and audit events apply.
"""

from __future__ import annotations

import json
from typing import Any

from livekit.agents import function_tool
from livekit.agents.llm import RawFunctionTool

from rex_mcp_gateway.gateway import Gateway, ToolInfo

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


def _make_tool(gw: Gateway, specialist: str, info: ToolInfo) -> RawFunctionTool:
    async def handler(raw_arguments: dict[str, object]) -> str:
        out = await gw.call(specialist, info.qualified_name, dict(raw_arguments), summary=_summary(info, raw_arguments))
        return out.text

    schema = {
        "name": livekit_name(info.qualified_name),
        "description": f"{info.description.strip()} [{_TIER_HINT[info.tier]}]",
        "parameters": info.input_schema or {"type": "object", "properties": {}},
    }
    return function_tool(handler, raw_schema=schema)


async def build_tools(gw: Gateway, specialist: str = "rex") -> list[RawFunctionTool]:
    return [_make_tool(gw, specialist, info) for info in await gw.list_tools(specialist)]
