"""Live multi-step workflow tests (W-1 standup notes & W-2 travel block).

Uses real LLM + multi-tool coordination through the gateway.
"""

import pytest

from rex_agent.main import load_runtime_registry
from rex_agent.testing import rex_session


def multistep_registry():
    reg = load_runtime_registry()
    reg.allowlists["rex"] = {"location", "calendar", "slack", "notion"}
    return reg


@pytest.mark.asyncio
async def test_travel_time_and_calendar_block_w2():
    """W-2: Calculate travel time from Koramangala to Indiranagar and block calendar slot."""
    events = []
    async with rex_session(events, registry=multistep_registry()) as (session, _gw):
        prompt = (
            "How long from Koramangala to Indiranagar, and block that travel time on my calendar "
            "before my 5 pm meeting tomorrow"
        )
        result = await session.run(user_input=prompt)
        # Should call location travel_time first
        result.expect.contains_function_call(name="location__travel_time")
        # And should call calendar create_event
        result.expect.contains_function_call(name="calendar__create_event")


@pytest.mark.asyncio
async def test_standup_notes_and_slack_post_w1():
    """W-1: Create standup notes in Notion and post link to Slack (requires approval for Slack post)."""
    events = []
    async with rex_session(events, registry=multistep_registry()) as (session, _gw):
        prompt = (
            "Make today's standup notes in Notion — Johny did the voice loop, Shanky the gateway — "
            "and post the link in #rex-test"
        )
        _r1 = await session.run(user_input=prompt)
        # Verify notion create page or slack post was initiated
        assert any(e.tool.startswith("notion.") or e.tool.startswith("slack.") for e in events)

        # If approval requested for Slack post, confirm
        if any(e.status == "awaiting_approval" for e in events):
            r2 = await session.run(user_input="yes, post the link")
            r2.expect.contains_function_call(name="approve_action")
            assert events[-1].status == "succeeded"
