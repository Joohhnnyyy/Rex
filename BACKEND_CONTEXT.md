# Backend Context

Owner: **Shanky**. Covers `apps/api`, `apps/agent/brain`, `packages/mcp_gateway`, `packages/llm_router`, `packages/shared`.

## Stack

| Concern | Choice |
|---|---|
| Language | Python 3.12, `uv` workspace |
| Web framework | FastAPI + Uvicorn |
| ORM / migrations | SQLAlchemy 2 (async) + Alembic |
| DB | Postgres 16 + pgvector |
| Cache / queue / pub-sub | Redis 7 (`arq` for jobs, pub/sub for timeline fan-out) |
| Agent orchestration | LangGraph |
| MCP | official `mcp` Python SDK (client in gateway, server for our tools) |
| Validation | Pydantic v2 (schemas in `packages/shared`) |
| Logging / tracing | structlog + Langfuse + OpenTelemetry |
| Tests | pytest, pytest-asyncio, respx (HTTP fakes), fake MCP servers |

## Process layout

```
┌──────────────┐   jobs (arq)   ┌──────────────┐
│ agent worker │ ─────────────► │ job worker   │  (slow specialists: Caller, Meeting, Coder)
│ voice + sup. │ ◄── pub/sub ── │              │
└──────┬───────┘                └──────┬───────┘
       │ MCP gateway (in-process lib)  │
       ▼                               ▼
┌──────────────────────────────────────────────┐
│ apps/api  — REST + SSE + webhooks            │
└──────────────────────┬───────────────────────┘
                       ▼
               Postgres · Redis
```

- The **gateway is a library** used by both the agent worker and the job worker; it writes events via the API's service layer (direct DB access through shared repository code, not HTTP, to save latency).
- The **API** is the only public HTTP surface (behind Caddy).

## Code layout (`apps/api`)

```
apps/api/
├── main.py                # app factory, routers, middleware
├── settings.py            # pydantic-settings, reads .env
├── deps.py                # DB session, current_user, rate limiter
├── routers/               # auth, sessions, livekit, connections, jobs, timeline, approvals, tools, webhooks
├── services/              # business logic, one module per router
├── repositories/          # DB access (SQLAlchemy)
├── models/                # ORM models (see DATABASE.md)
├── security/              # token crypto, OAuth helpers, signature checks
└── migrations/            # alembic
```

## Key flows

**Job lifecycle**: `queued → running → (awaiting_approval) → succeeded | failed | cancelled`. Every transition writes an `action_events` row and publishes to `timeline:{user_id}`.

**Approval**: gateway hits a Tier A tool → creates `approvals` row (`pending`, expires in 30 s) → publishes event → waits on Redis key `approval:{id}` → user approves by voice (agent writes) or dashboard (API writes) → gateway proceeds or raises `ApprovalDenied`.

**Undo**: Tier W tools register a compensating call (`calendar.create` → `calendar.delete(event_id)`) stored in `action_events.undo`. `POST /v1/actions/{id}/undo` runs it through the gateway.

## Conventions

- Async everywhere; no blocking I/O in request handlers.
- Services raise domain errors (`NotFound`, `Forbidden`, `ApprovalDenied`, `ToolTimeout`) → mapped to HTTP problems in one handler.
- IDs: UUIDv7 (time-ordered). Timestamps: `timestamptz`, UTC in DB, Asia/Kolkata in UX.
- Every public function in `services/` has a docstring and a test.
- Settings never read `os.environ` directly outside `settings.py`.

## Environment variables (see `.env.example`)

`DATABASE_URL`, `REDIS_URL`, `LIVEKIT_URL`, `LIVEKIT_API_KEY`, `LIVEKIT_API_SECRET`, `GNANI_API_KEY`, `GEMINI_API_KEY`, `MISTRAL_API_KEY`, `OPENROUTER_API_KEY`, `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_NUMBER`, `LIVEKIT_SIP_TRUNK_ID`, `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_MAPS_API_KEY`, `SLACK_BOT_TOKEN`, `NOTION_TOKEN`, `GITHUB_TOKEN`, `VEXA_API_KEY`, `TOKEN_ENC_KEY`, `SESSION_SECRET`, `LANGFUSE_*`.
