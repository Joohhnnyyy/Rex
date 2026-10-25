"""Tools router: inspect available MCP tools, servers, and permission tiers."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from rex_agent.main import load_runtime_registry
from rex_mcp_gateway.registry import Tier

router = APIRouter(prefix="/v1/tools", tags=["tools"])


class ToolSummary(BaseModel):
    qualified_name: str
    server: str
    name: str
    tier: Tier
    description: str
    enabled: bool = True
    undo_tool: str | None = None


class ServerToggle(BaseModel):
    enabled: bool


# Runtime state overrides for server enablement
_SERVER_OVERRIDES: dict[str, bool] = {}


@router.get("", response_model=list[ToolSummary])
async def list_tools() -> list[ToolSummary]:
    """List all runtime MCP tools registered with the Rex gateway, along with their tiers."""
    reg = load_runtime_registry()
    summaries: list[ToolSummary] = []

    for server_name, server_spec in reg.servers.items():
        is_enabled = _SERVER_OVERRIDES.get(server_name, True)
        for tool_name, policy in server_spec.tools.items():
            summaries.append(
                ToolSummary(
                    qualified_name=f"{server_name}.{tool_name}",
                    server=server_name,
                    name=tool_name,
                    tier=policy.tier,
                    description=f"{server_name} tool: {tool_name}",
                    enabled=is_enabled,
                    undo_tool=f"{server_name}.{policy.undo}" if policy.undo else None,
                )
            )
    return summaries


@router.patch("/{server_name}", response_model=dict[str, Any])
async def toggle_server(server_name: str, body: ServerToggle) -> dict[str, Any]:
    """Enable or disable a specific MCP server/skill."""
    _SERVER_OVERRIDES[server_name] = body.enabled
    return {"server": server_name, "enabled": body.enabled}
