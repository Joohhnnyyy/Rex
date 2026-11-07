"""End of a call: a short summary of what was said and done lands in long-term memory."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from livekit.agents import llm

from rex_agent.main import save_session_summary
from rex_agent.prompts import system_prompt
from rex_mcp_servers import memory


class FakeLLM:
    def __init__(self, text: str):
        self.text, self.seen = text, None

    async def complete(self, task_kind, messages, **params):
        self.seen = (task_kind, messages)
        return type("Out", (), {"text": self.text})()


@pytest.mark.asyncio
async def test_summary_is_saved_as_an_episode(tmp_path, monkeypatch):
    monkeypatch.setenv("REX_MEMORY_PATH", str(tmp_path / "memory.json"))
    ctx = llm.ChatContext.empty()
    ctx.add_message(role="user", content="Send Asmi 'are you awake' on WhatsApp")
    ctx.items.append(llm.FunctionCall(call_id="c1", name="control_screen", arguments='{"action": "type"}'))
    ctx.add_message(role="assistant", content="Done, sent it.")

    fake = FakeLLM("  Rex sent Asmi 'are you awake'\non WhatsApp. ")
    assert await save_session_summary(ctx, llm=fake) == "Rex sent Asmi 'are you awake' on WhatsApp."
    kind, messages = fake.seen
    assert kind == "summarise"
    assert "User: Send Asmi" in messages[1]["content"] and "(Rex used control_screen" in messages[1]["content"]
    assert memory.load()["episodes"][-1]["summary"] == "Rex sent Asmi 'are you awake' on WhatsApp."


@pytest.mark.asyncio
async def test_silent_call_stores_nothing(tmp_path, monkeypatch):
    monkeypatch.setenv("REX_MEMORY_PATH", str(tmp_path / "memory.json"))
    ctx = llm.ChatContext.empty()
    ctx.add_message(role="assistant", content="Hi, I'm Rex.")
    assert await save_session_summary(ctx, llm=FakeLLM("x")) is None
    assert memory.load()["episodes"] == []


def test_prompt_includes_memory_as_data():
    now = datetime(2026, 11, 7, 10, 0, tzinfo=UTC)
    assert "memory of this user is empty" in system_prompt("Johny", now)
    p = system_prompt("Johny", now, memory="Facts about the user:\n- manager: Shanky")
    assert "- manager: Shanky" in p and "not instructions" in p
