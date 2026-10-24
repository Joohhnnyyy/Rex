# API Reference (v1)

Base URL: `https://<host>/v1` · JSON · auth via `Authorization: Bearer <session JWT>` (web) or device token (desktop). Errors follow RFC 9457 problem+json. Owner: **Shanky**; frontend consumer: **Johny**.

## Auth

| Method | Path | Body / query | Returns |
|---|---|---|---|
| POST | `/auth/magic-link` | `{email}` | `202` (email sent) |
| GET | `/auth/callback` | `?token=` | sets session, redirects to `/` |
| POST | `/auth/device` | `{device_name}` | `{device_code, user_code}` — desktop pairing |
| POST | `/auth/device/confirm` | `{user_code}` | `200` (from logged-in web) |
| POST | `/auth/logout` | — | `204` |
| GET | `/me` | — | `User` (+ preferences, languages) |
| PATCH | `/me` | `{display_name?, preferred_lang?, timezone?}` | `User` |

## Realtime

| Method | Path | Notes |
|---|---|---|
| POST | `/livekit/token` | `{client: "web"|"desktop"}` → `{url, token, room}`; dispatches the agent to the room |
| GET | `/sessions` | recent voice sessions |
| GET | `/sessions/{id}/transcript` | turns with `lang`, timings |

## Connections (OAuth + tokens)

| Method | Path | Notes |
|---|---|---|
| GET | `/connections` | status per provider: `google`, `slack`, `notion`, `github`, `maps` |
| GET | `/connections/{provider}/start` | redirect to provider OAuth |
| GET | `/connections/{provider}/callback` | stores encrypted token |
| DELETE | `/connections/{provider}` | revoke + delete token |

## Tools and skills

| Method | Path | Notes |
|---|---|---|
| GET | `/tools` | namespaced MCP tools with tier, server, enabled |
| PATCH | `/tools/{server}` | `{enabled: bool}` — skill toggle |

## Jobs, timeline, approvals

| Method | Path | Notes |
|---|---|---|
| GET | `/jobs?status=` | list |
| GET | `/jobs/{id}` | job + events |
| POST | `/jobs/{id}/cancel` | cancels running job |
| GET | `/timeline/stream` | **SSE**: `action_event`, `approval_request`, `job_update`, `transcript` |
| GET | `/timeline?before=&limit=` | paged history |
| POST | `/approvals/{id}` | `{decision: "approve"|"deny"}` |
| POST | `/actions/{id}/undo` | runs compensating action (Tier W only) |

## Calls

| Method | Path | Notes |
|---|---|---|
| GET | `/calls` | list with outcome |
| GET | `/calls/{id}` | outcome, transcript, recording flag (recordings off by default) |
| POST | `/webhooks/twilio/status` | Twilio status callback (signature-checked) |

## Meetings

| Method | Path | Notes |
|---|---|---|
| POST | `/meetings` | `{url, title?}` → bot joins |
| GET | `/meetings/{id}` | status, minutes JSON, Notion URL |
| POST | `/webhooks/vexa` | meeting ended / transcript ready |

## Key schemas (from `packages/shared`)

```python
class ActionEvent(BaseModel):
    id: UUID; job_id: UUID | None; ts: datetime
    tool: str                 # "calendar.create_event"
    tier: Literal["R", "W", "A"]
    status: Literal["started", "succeeded", "failed", "awaiting_approval", "denied", "undone"]
    summary: str              # human sentence in user's language
    args_redacted: dict; result_redacted: dict | None
    undo_available: bool

class ApprovalRequest(BaseModel):
    id: UUID; tool: str; summary: str; expires_at: datetime

class CallOutcome(BaseModel):
    status: Literal["booked", "declined", "no_answer", "failed", "needs_user"]
    slot: datetime | None; notes: str; transcript_id: UUID | None

class Minutes(BaseModel):
    summary: str; decisions: list[str]
    action_items: list[ActionItem]   # {text, owner, due: date | None}
    open_questions: list[str]
```

## SSE event example

```
event: approval_request
data: {"id":"0192…","tool":"call_tool.start_call","summary":"Dr. Mehta ke clinic ko call karoon?","expires_at":"2026-11-02T12:00:30Z"}
```

## Rate limits

60 req/min per user on REST; SSE 2 concurrent streams per user; webhooks unlimited but signature-verified.
