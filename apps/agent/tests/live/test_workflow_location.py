"""Example workflow test (template for calendar / slack / notion workflows)."""

from rex_agent.testing import rex_session


async def test_travel_time_question_calls_location_tool_and_answers():
    events = []
    async with rex_session(events) as (session, _gw):
        result = await session.run(user_input="How long does it take to drive from Koramangala to Indiranagar?")
        result.expect.contains_function_call(name="location__travel_time")
        result.expect.contains_function_call_output()
        msg = result.expect[-1].event().item
        assert "minute" in msg.text_content.lower()
    assert [e.status for e in events if e.tool == "location.travel_time"][-1] == "succeeded"


async def test_small_talk_does_not_call_tools():
    async with rex_session() as (session, _gw):
        result = await session.run(user_input="Hi Rex, how are you?")
        result.expect.next_event().is_message(role="assistant")
        result.expect.no_more_events()
