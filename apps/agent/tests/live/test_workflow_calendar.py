"""Live workflow tests for Google Calendar (C-1 through C-4).

Uses real LLM + Calendar MCP tools through the gateway.
"""

import os

import pytest

from rex_agent.main import load_runtime_registry
from rex_agent.testing import rex_session

# Enable test service if real OAuth credentials are not logged in yet
os.environ.setdefault("REX_FAKE_SERVICES", "1")


def calendar_registry():
    reg = load_runtime_registry()
    reg.allowlists["rex"] = {"calendar", "location"}
    return reg


@pytest.mark.asyncio
async def test_calendar_list_events_c1():
    """C-1: What's on my calendar tomorrow? -> calls calendar__list_events without approval."""
    events = []
    async with rex_session(events, registry=calendar_registry()) as (session, _gw):
        result = await session.run(user_input="What's on my calendar tomorrow?")
        result.expect.contains_function_call(name="calendar__list_events")
        result.expect.contains_function_call_output()
        # Verify no approval was requested (Tier R)
        assert not any(e.status == "awaiting_approval" for e in events)


@pytest.mark.asyncio
async def test_calendar_create_event_c2():
    """C-2: Book 30 minutes with Johny tomorrow at 4 pm about the demo -> calls calendar__create_event."""
    events = []
    async with rex_session(events, registry=calendar_registry()) as (session, _gw):
        result = await session.run(user_input="Book 30 minutes with Johny tomorrow at 4 pm about the demo")
        result.expect.contains_function_call(name="calendar__create_event")
        result.expect.contains_function_call_output()
        cal_events = [e for e in events if e.tool == "calendar.create_event"]
        assert cal_events, "calendar.create_event should be emitted"
        assert cal_events[-1].status == "succeeded"
        assert not any(e.status == "awaiting_approval" for e in events)


@pytest.mark.asyncio
async def test_calendar_find_free_slots_c3():
    """C-3: When am I free on Monday afternoon for an hour? -> calls calendar__find_free_slots."""
    events = []
    async with rex_session(events, registry=calendar_registry()) as (session, _gw):
        result = await session.run(user_input="When am I free on Monday afternoon for an hour?")
        result.expect.contains_function_call(name="calendar__find_free_slots")
        result.expect.contains_function_call_output()


@pytest.mark.asyncio
async def test_calendar_delete_event_approval_c4():
    """C-4: Delete the [Rex test] demo event -> Tier A requires approval, then approves."""
    events = []
    async with rex_session(events, registry=calendar_registry()) as (session, _gw):
        r1 = await session.run(user_input="Delete the [Rex test] demo event with id evt_1")
        r1.expect.contains_function_call(name="calendar__delete_event")
        assert any(e.status == "awaiting_approval" for e in events)

        # Second turn: user confirms
        r2 = await session.run(user_input="yes, delete it")
        r2.expect.contains_function_call(name="approve_action")
        assert events[-1].status == "succeeded"
