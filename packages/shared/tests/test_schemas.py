from datetime import UTC, date, datetime, timedelta
from uuid import uuid4

import pytest
from pydantic import ValidationError

from rex_shared.schemas import (
    ActionEvent,
    ActionItem,
    ApprovalRequest,
    CallOutcome,
    Minutes,
)


def _event(**kw):
    base = dict(
        id=uuid4(),
        ts=datetime(2026, 10, 25, 10, 0, tzinfo=UTC),
        tool="calendar.create_event",
        tier="W",
        status="succeeded",
        summary="Meeting kal 4 baje rakh di",
    )
    base.update(kw)
    return ActionEvent(**base)


def test_tier_accepts_only_r_w_a():
    assert _event(tier="A").tier == "A"
    with pytest.raises(ValidationError):
        _event(tier="X")


def test_action_event_round_trips_json_and_defaults():
    ev = _event()
    again = ActionEvent.model_validate_json(ev.model_dump_json())
    assert again == ev
    assert ev.undo_available is False
    assert ev.job_id is None
    assert ev.args_redacted == {}


def test_booked_call_outcome_requires_slot():
    with pytest.raises(ValidationError):
        CallOutcome(status="booked", notes="ok")
    ok = CallOutcome(status="booked", slot=datetime(2026, 11, 7, 18, 0, tzinfo=UTC), notes="Saturday 6 PM")
    assert ok.slot.hour == 18
    assert CallOutcome(status="no_answer", notes="").slot is None


def test_minutes_hold_action_items_with_optional_due():
    m = Minutes(
        summary="Standup",
        decisions=["Ship voice loop by Monday"],
        action_items=[
            ActionItem(text="Set up Twilio trunk", owner="Johny", due=date(2026, 11, 1)),
            ActionItem(text="Write gateway", owner="Shanky"),
        ],
        open_questions=[],
    )
    assert m.action_items[1].due is None


def test_approval_request_expiry():
    now = datetime(2026, 11, 2, 12, 0, tzinfo=UTC)
    req = ApprovalRequest(
        id=uuid4(), tool="call_tool.start_call", summary="Call the clinic?", expires_at=now + timedelta(seconds=30)
    )
    assert not req.is_expired(now)
    assert req.is_expired(now + timedelta(seconds=31))
