"""Gateway spawns the real location MCP server over stdio (no network calls made)."""

from rex_agent.main import load_runtime_registry
from rex_agent.tools_bridge import build_tools
from rex_mcp_gateway.gateway import Gateway


async def test_location_server_over_stdio():
    async with Gateway(load_runtime_registry()) as gw:
        assert "location" in gw.connected()
        names = set(t.info.name for t in await build_tools(gw, "rex"))
        assert {"location__find_place", "location__map_link", "location__travel_time"}.issubset(names)
