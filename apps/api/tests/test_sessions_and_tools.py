import uuid
from datetime import UTC, datetime

import pytest
from httpx import ASGITransport, AsyncClient

from rex_api.auth import get_or_create_user
from rex_api.main import create_app
from rex_api.sessions import record_session, record_turn
from rex_api.settings import Settings
from rex_api.timeline import record_action_event
from rex_shared.schemas import ActionEvent, Turn


@pytest.fixture
def client():
    app = create_app(Settings(dev_auth=True))
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


@pytest.mark.asyncio
async def test_sessions_and_transcripts(client: AsyncClient):
    user = get_or_create_user("dev@rex.internal")
    sid = uuid.uuid4()
    record_session(user_id=user.id, room="room-123", session_id=sid)
    record_turn(sid, Turn(role="user", text="hello", lang="en-IN"))
    record_turn(sid, Turn(role="assistant", text="hi there", lang="en-IN"))

    # List sessions
    r_list = await client.get("/v1/sessions")
    assert r_list.status_code == 200
    sessions = r_list.json()
    assert any(s["room"] == "room-123" for s in sessions)

    # Transcript
    r_tr = await client.get(f"/v1/sessions/{sid}/transcript")
    assert r_tr.status_code == 200
    turns = r_tr.json()
    assert len(turns) == 2
    assert turns[0]["text"] == "hello"


@pytest.mark.asyncio
async def test_tools_listing_and_toggle(client: AsyncClient):
    r = await client.get("/v1/tools")
    assert r.status_code == 200
    tools = r.json()
    names = [t["qualified_name"] for t in tools]
    assert "location.find_place" in names
    assert "calendar.create_event" in names

    # Toggle a server
    r_patch = await client.patch("/v1/tools/calendar", json={"enabled": False})
    assert r_patch.status_code == 200
    assert r_patch.json()["enabled"] is False


@pytest.mark.asyncio
async def test_timeline_approvals_and_undo(client: AsyncClient):
    action_id = uuid.uuid4()
    ev = ActionEvent(
        id=action_id,
        ts=datetime.now(UTC),
        tool="calendar.create_event",
        tier="W",
        status="succeeded",
        summary="Created demo meeting",
        undo_available=True,
    )
    record_action_event(ev)

    # Check timeline
    r_tl = await client.get("/v1/timeline")
    assert r_tl.status_code == 200
    timeline = r_tl.json()
    assert any(str(action_id) == e["id"] for e in timeline)

    # Undo action
    r_undo = await client.post(f"/v1/actions/{action_id}/undo")
    assert r_undo.status_code == 200
    assert r_undo.json()["status"] == "undone"
