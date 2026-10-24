from mcp.server.mcpserver import MCPServer

from rex_agent.tools_bridge import build_tools, livekit_name, qualified_name
from rex_mcp_gateway.gateway import Gateway
from rex_mcp_gateway.registry import Registry, ServerSpec, ToolPolicy


def _registry():
    srv = MCPServer("demo")
    sent = []

    @srv.tool()
    def lookup(q: str) -> str:
        """Look up."""
        return f"found {q}"

    @srv.tool()
    def send(to: str) -> str:
        """Send to someone."""
        sent.append(to)
        return "sent"

    reg = Registry(
        servers={
            "demo": ServerSpec(name="demo", inprocess=srv, tools={"lookup": ToolPolicy("R"), "send": ToolPolicy("A")})
        },
        allowlists={"rex": {"demo"}},
    )
    return reg, sent


def test_names_round_trip():
    assert livekit_name("location.find_place") == "location__find_place"
    assert qualified_name("location__find_place") == "location.find_place"


async def test_build_tools_exposes_schema_and_calls_gateway():
    reg, sent = _registry()
    async with Gateway(reg) as gw:
        tools = await build_tools(gw, "rex")
        by_name = {t.info.name: t for t in tools}
        assert set(by_name) == {"demo__lookup", "demo__send"}
        schema = by_name["demo__lookup"].info.raw_schema
        assert schema["parameters"]["properties"]["q"]
        assert "needs the user's approval" in by_name["demo__send"].info.raw_schema["description"]

        out = await by_name["demo__lookup"]._func(raw_arguments={"q": "pune"})
        assert "found pune" in out

        out = await by_name["demo__send"]._func(raw_arguments={"to": "shanky"})
        assert "approve_action" in out and sent == []
        action_id = gw.pending()[0].action_id
        done = await gw.approve(action_id)
        assert done.ok and sent == ["shanky"]
