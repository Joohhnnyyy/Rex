from contextlib import asynccontextmanager

import pytest

from rex_mcp_gateway.gateway import Gateway, NeedsApproval, ToolDenied


@asynccontextmanager
async def open_gw(registry):
    events = []

    async def sink(ev):
        events.append(ev)

    async with Gateway(registry, on_event=sink) as g:
        g.events = events  # type: ignore[attr-defined]
        yield g


async def test_lists_namespaced_tools_with_tiers(registry):
    async with open_gw(registry) as gw:
        tools = await gw.list_tools("rex")
        names = {t.qualified_name: t.tier for t in tools}
        assert names["demo.lookup"] == "R"
        assert names["demo.post_message"] == "A"
        assert "q" in next(t for t in tools if t.qualified_name == "demo.lookup").input_schema["properties"]


async def test_specialist_without_access_is_denied(registry):
    async with open_gw(registry) as gw:
        with pytest.raises(ToolDenied):
            await gw.call("calendar", "demo.lookup", {"q": "x"})


async def test_read_tool_runs_and_is_wrapped_as_untrusted(registry):
    async with open_gw(registry) as gw:
        out = await gw.call("rex", "demo.lookup", {"q": "pune"})
        assert out.ok
        assert out.text.startswith('<untrusted_data source="demo.lookup">')
        assert "result for pune" in out.text
        statuses = [(e.tool, e.status) for e in gw.events]
        assert statuses == [("demo.lookup", "started"), ("demo.lookup", "succeeded")]


async def test_write_tool_runs_without_approval(registry):
    async with open_gw(registry) as gw:
        out = await gw.call("rex", "demo.create_note", {"text": "buy milk"})
        assert out.ok and "n1" in out.text


async def test_act_tool_needs_approval_then_runs(registry, demo_server):
    async with open_gw(registry) as gw:
        out = await gw.call(
            "rex", "demo.post_message", {"channel": "#general", "text": "hi"}, summary="Post 'hi' to #general"
        )
        assert isinstance(out, NeedsApproval)
        assert demo_server.state["posted"] == []
        assert gw.events[-1].status == "awaiting_approval"
        assert gw.pending()[0].summary == "Post 'hi' to #general"

        done = await gw.approve(out.action_id)
        assert done.ok
        assert demo_server.state["posted"] == [("#general", "hi")]
        assert gw.events[-1].status == "succeeded"
        assert gw.pending() == []


async def test_denied_action_never_runs(registry, demo_server):
    async with open_gw(registry) as gw:
        out = await gw.call("rex", "demo.post_message", {"channel": "#x", "text": "no"})
        await gw.deny(out.action_id)
        assert demo_server.state["posted"] == []
        assert gw.events[-1].status == "denied"
        with pytest.raises(KeyError):
            await gw.approve(out.action_id)


async def test_tool_error_is_reported_not_raised(registry):
    async with open_gw(registry) as gw:
        out = await gw.call("rex", "demo.flaky", {})
        assert not out.ok
        assert gw.events[-1].status == "failed"


async def test_unknown_tool_raises(registry):
    async with open_gw(registry) as gw:
        with pytest.raises(ToolDenied):
            await gw.call("rex", "demo.nope", {})


async def test_calls_from_other_tasks_work(registry):
    import asyncio

    async with open_gw(registry) as gw:
        results = await asyncio.gather(
            *[asyncio.create_task(gw.call("rex", "demo.lookup", {"q": f"q{i}"})) for i in range(5)]
        )
        assert all(r.ok for r in results)


async def test_hostile_tool_output_stays_inside_untrusted_wrapper(registry):
    async with open_gw(registry) as gw:
        out = await gw.call("rex", "demo.injected", {})
        assert out.text.startswith("<untrusted_data")
        assert out.text.rstrip().endswith("</untrusted_data>")
