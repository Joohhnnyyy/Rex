from datetime import datetime
from zoneinfo import ZoneInfo

from rex_agent.prompts import CALL_GREETING, system_prompt


def test_system_prompt_has_identity_time_and_language_rules():
    now = datetime(2026, 10, 25, 16, 5, tzinfo=ZoneInfo("Asia/Kolkata"))
    p = system_prompt(user_name="Johny", now=now)
    assert "Rex" in p and "Johny" in p
    assert "2026-10-25" in p and "Asia/Kolkata" in p
    assert "same language" in p.lower()
    assert "never claim to be human" in p.lower()


def test_call_greeting_is_english_and_discloses_ai():
    g = CALL_GREETING.format(user="Johny")
    assert g == "Hello, this is Rex, Johny's AI assistant, calling on their behalf."


def test_system_prompt_lists_specialists_and_delegate_tool():
    now = datetime(2026, 10, 25, 16, 5, tzinfo=ZoneInfo("Asia/Kolkata"))
    p = system_prompt(user_name="Johny", now=now)
    assert "delegate_task" in p
    for name in ("calendar", "caller", "coder", "meeting"):
        assert name in p


def test_english_only_prompt_forces_english_replies():
    now = datetime(2026, 10, 25, 16, 5, tzinfo=ZoneInfo("Asia/Kolkata"))
    p = system_prompt(user_name="Johny", now=now, english_only=True)
    assert "always reply in english" in p.lower()
    assert "same language" not in p.lower()
