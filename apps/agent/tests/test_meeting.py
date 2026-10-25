"""Unit tests for Meeting specialist executor (T-33 / T-35)."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock

import pytest

from rex_agent.brain.meeting import MeetingSpecialist
from rex_llm_router.client import Attempt, Completion, LLMClient
from rex_llm_router.models import ModelSpec
from rex_mcp_servers.vexa import VexaClient


@pytest.mark.asyncio
async def test_meeting_specialist_runs_end_to_end():
    dummy_model = ModelSpec(
        alias="mistral_small",
        provider="mistral",
        name="mistral-small-latest",
        vision=False,
    )
    mock_minutes = {
        "summary": "Team aligned on shipping Phase 2.",
        "decisions": ["Keep Gnani in the voice loop"],
        "action_items": [{"text": "Ship minutes server", "owner": "Shanky", "due": "2026-10-25"}],
        "open_questions": [],
    }
    mock_completion = Completion(
        text=f"```json\n{json.dumps(mock_minutes)}\n```",
        model=dummy_model,
        attempts=[Attempt(dummy_model, "ok")],
    )

    fake_client = AsyncMock(spec=LLMClient)
    fake_client.complete.return_value = mock_completion

    vexa = VexaClient()
    specialist = MeetingSpecialist(vexa_client=vexa, llm_client=fake_client)

    res = await specialist.run("Join https://meet.google.com/test-meet-123 and take notes for the team")

    assert res.ok is True
    assert "joined the meeting, generated the minutes" in res.summary
    assert res.data["url"] == "https://meet.google.com/test-meet-123"
    assert "Standup" in res.data["slack_summary"]
    # Check meeting status is left/completed
    meeting_id = res.data["meeting_id"]
    st = vexa.get_status(meeting_id)
    assert st["status"] == "completed"
