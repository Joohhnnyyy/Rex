"""Cross-boundary data contracts for Rex.

This module is the single source of truth: the API, the agent worker, the MCP
gateway and (via generated TypeScript types) the dashboard all use these shapes.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

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
    undo_available: bool = False
    trace_id: str | None = None


class ApprovalRequest(_Model):
    """A Tier A action waiting for the user's 'yes'."""

    id: UUID
    tool: str
    summary: str
    expires_at: datetime

    def is_expired(self, now: datetime) -> bool:
        return now > self.expires_at


class CallOutcome(_Model):
    """Structured result of an outbound call placed by the Caller specialist."""

    status: Literal["booked", "declined", "no_answer", "failed", "needs_user"]
    slot: datetime | None = None
    notes: str = ""
    transcript_id: UUID | None = None

    @model_validator(mode="after")
    def _booked_needs_slot(self) -> CallOutcome:
        if self.status == "booked" and self.slot is None:
            raise ValueError("a booked call must include the booked slot")
        return self


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


class Turn(_Model):
    """One spoken turn with latency metrics (ms)."""

    role: Literal["user", "assistant"]
    text: str
    lang: str = Field(description="BCP-47, e.g. 'hi-IN'")
    stt_ms: int | None = None
    llm_ms: int | None = None
    tts_ms: int | None = None
    total_ms: int | None = None
    fallback_used: bool = False
