"""Unit tests for Meeting Minutes MCP Server (T-35)."""

from __future__ import annotations

import json
from datetime import date
from unittest.mock import AsyncMock

import pytest

from rex_llm_router.client import Attempt, Completion, LLMClient
from rex_llm_router.models import ModelSpec
from rex_mcp_servers.minutes import (
    build_server,
    minutes_to_notion_blocks,
    minutes_to_slack_mrkdwn,
)
from rex_shared.schemas import ActionItem, Minutes


def test_minutes_to_notion_blocks_structure():
    m = Minutes(
        summary="Sprint planning meeting discussing Voice loop and MCP gateway.",
        decisions=["Ship Phase 2 by Thursday", "Keep Gnani in the voice loop"],
        action_items=[
            ActionItem(text="Wire Slack MCP server", owner="Shanky", due=date(2026, 10, 28)),
            ActionItem(text="Test LiveKit SIP trunk", owner="Johny"),
        ],
        open_questions=["Which AWS region for deployment?"],
    )

    blocks = minutes_to_notion_blocks(m, title="Sprint 4 Standup")
    assert len(blocks) >= 6
    assert blocks[0]["type"] == "heading_1"
    assert blocks[0]["heading_1"]["rich_text"][0]["text"]["content"] == "Sprint 4 Standup"
    assert blocks[1]["type"] == "callout"
    assert "Sprint planning meeting" in blocks[1]["callout"]["rich_text"][0]["text"]["content"]

    # Check to-do items
    todos = [b for b in blocks if b["type"] == "to_do"]
    assert len(todos) == 2
    assert "@Shanky" in todos[0]["to_do"]["rich_text"][0]["text"]["content"]
    assert "2026-10-28" in todos[0]["to_do"]["rich_text"][0]["text"]["content"]


def test_minutes_to_slack_mrkdwn_formatting():
    m = Minutes(
        summary="Weekly check-in on Rex milestones.",
        decisions=["All tools go through MCP gateway"],
        action_items=[ActionItem(text="Run eval set", owner="Shanky", due=date(2026, 10, 30))],
        open_questions=[],
    )

    mrkdwn = minutes_to_slack_mrkdwn(m, title="Weekly Sync", notion_url="https://notion.so/rex/sync-1")
    assert ":memo: *Weekly Sync*" in mrkdwn
    assert "*Summary:*\nWeekly check-in on Rex milestones." in mrkdwn
    assert "• All tools go through MCP gateway" in mrkdwn
    assert "• [ ] Run eval set (`@Shanky`) *[Due 2026-10-30]*" in mrkdwn
    assert "https://notion.so/rex/sync-1" in mrkdwn


@pytest.mark.asyncio
async def test_generate_minutes_tool_with_mock_llm():
    dummy_model = ModelSpec(
        alias="mistral_small",
        provider="mistral",
        name="mistral-small-latest",
        vision=False,
    )
    mock_payload = {
        "summary": "Team aligned on G2 exit criteria.",
        "decisions": ["Freeze tool tiers"],
        "action_items": [{"text": "Write minutes server", "owner": "Shanky", "due": "2026-10-25"}],
        "open_questions": [],
    }
    mock_completion = Completion(
        text=f"```json\n{json.dumps(mock_payload)}\n```",
        model=dummy_model,
        attempts=[Attempt(dummy_model, "ok")],
    )

    fake_client = AsyncMock(spec=LLMClient)
    fake_client.complete.return_value = mock_completion

    server = build_server(llm_client=fake_client)
    tools = await server.list_tools()
    tool_names = {t.name for t in tools}
    assert {"generate_minutes", "format_notion_blocks", "format_slack_summary"} <= tool_names

    res = await server.call_tool(
        "generate_minutes",
        {"transcript": "Johny: We need to freeze tiers.\nShanky: Agreed, I will write minutes."},
    )
    assert not res.is_error
    result_text = res.content[0].text
    parsed = Minutes.model_validate_json(result_text)
    assert parsed.summary == "Team aligned on G2 exit criteria."
    assert parsed.action_items[0].owner == "Shanky"
    assert parsed.action_items[0].due == date(2026, 10, 25)
