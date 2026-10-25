"""Sessions router: view recent voice sessions and conversation transcripts."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from rex_api.auth import get_current_user
from rex_shared.schemas import Turn, User, VoiceSession

router = APIRouter(prefix="/v1/sessions", tags=["sessions"])

# In-memory store for sessions and transcripts
_SESSIONS: dict[uuid.UUID, VoiceSession] = {}


def record_session(
    user_id: uuid.UUID,
    room: str,
    client: str = "web",
    session_id: uuid.UUID | None = None,
) -> VoiceSession:
    sid = session_id or uuid.uuid4()
    session = VoiceSession(
        id=sid,
        user_id=user_id,
        client=client,  # type: ignore[arg-type]
        room=room,
        started_at=datetime.now(UTC),
        turns=[],
    )
    _SESSIONS[sid] = session
    return session


def record_turn(session_id: uuid.UUID, turn: Turn) -> None:
    if session_id in _SESSIONS:
        _SESSIONS[session_id].turns.append(turn)


@router.get("", response_model=list[VoiceSession])
async def list_sessions(user: Annotated[User, Depends(get_current_user)]) -> list[VoiceSession]:
    """List recent voice sessions for the logged-in user."""
    user_sessions = [s for s in _SESSIONS.values() if s.user_id == user.id]
    user_sessions.sort(key=lambda s: s.started_at, reverse=True)
    return user_sessions


@router.get("/{session_id}/transcript", response_model=list[Turn])
async def get_session_transcript(session_id: uuid.UUID, user: Annotated[User, Depends(get_current_user)]) -> list[Turn]:
    """Get the turn-by-turn transcript and latency metrics for a voice session."""
    session = _SESSIONS.get(session_id)
    if not session or session.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    return session.turns
