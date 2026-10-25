"""Timeline and approvals router."""

from __future__ import annotations

import uuid
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from rex_api.auth import get_current_user
from rex_shared.schemas import ActionEvent, User

router = APIRouter(prefix="/v1", tags=["timeline"])

# In-memory action events store
_TIMELINE_EVENTS: list[ActionEvent] = []
_PENDING_APPROVALS: dict[str, dict] = {}


def record_action_event(event: ActionEvent) -> None:
    _TIMELINE_EVENTS.insert(0, event)


class ApprovalDecision(BaseModel):
    decision: Literal["approve", "deny"]


@router.get("/timeline", response_model=list[ActionEvent])
async def get_timeline(
    limit: int = 50,
    user: Annotated[User, Depends(get_current_user)] = None,  # type: ignore[assignment]
) -> list[ActionEvent]:
    """Get the recent timeline of tool actions."""
    return _TIMELINE_EVENTS[:limit]


@router.post("/approvals/{action_id}")
async def decide_approval(
    action_id: str, body: ApprovalDecision, user: Annotated[User, Depends(get_current_user)]
) -> dict[str, str]:
    """Approve or deny a pending Tier A action from the dashboard."""
    # Find matching event in timeline and update status
    found = False
    for ev in _TIMELINE_EVENTS:
        if str(ev.id) == action_id or ev.args_redacted.get("action_id") == action_id:
            new_status = "succeeded" if body.decision == "approve" else "denied"
            # Update status
            ev_data = ev.model_dump()
            ev_data["status"] = new_status
            idx = _TIMELINE_EVENTS.index(ev)
            _TIMELINE_EVENTS[idx] = ActionEvent(**ev_data)
            found = True
            break

    return {"action_id": action_id, "decision": body.decision, "recorded": str(found)}


@router.post("/actions/{action_id}/undo")
async def undo_action(action_id: uuid.UUID, user: Annotated[User, Depends(get_current_user)]) -> dict[str, str]:
    """Trigger a compensating action for a Tier W event."""
    for idx, ev in enumerate(_TIMELINE_EVENTS):
        if ev.id == action_id:
            if not ev.undo_available:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail="Undo not available for this action"
                )
            ev_data = ev.model_dump()
            ev_data["status"] = "undone"
            ev_data["undo_available"] = False
            _TIMELINE_EVENTS[idx] = ActionEvent(**ev_data)
            return {"action_id": str(action_id), "status": "undone"}

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Action not found")
