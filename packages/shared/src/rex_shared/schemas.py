"""Cross-boundary data contracts for Rex.

The agent worker, the MCP gateway and the MCP servers share these shapes.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

Tier = Literal["R", "W", "A"]
"""Permission tier: R = read, W = write (reversible), A = act (external / irreversible)."""

ActionStatus = Literal["started", "succeeded", "failed", "awaiting_approval", "denied", "undone"]


class _Model(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ActionEvent(_Model):
    """One tool call as shown on the user's timeline."""

    id: UUID
    ts: datetime
    tool: str = Field(description="Namespaced MCP tool, e.g. 'calendar.create_event'")
    tier: Tier
    status: ActionStatus
    summary: str = Field(description="Human sentence in the user's language")
    job_id: UUID | None = None
    args_redacted: dict[str, Any] = Field(default_factory=dict)
    result_redacted: dict[str, Any] | None = None
    undo: dict[str, Any] | None = Field(default=None, description="Compensating call spec {tool, args}")
    undo_available: bool = False
    trace_id: str | None = None


class ActionItem(_Model):
    text: str
    owner: str | None = None
    due: date | None = None


class Minutes(_Model):
    """Meeting minutes produced by the Meeting specialist."""

    summary: str
    decisions: list[str] = Field(default_factory=list)
    action_items: list[ActionItem] = Field(default_factory=list)
    open_questions: list[str] = Field(default_factory=list)
