# Handoff

Daily handoff between **Johny** and **Shanky** (and any AI agent picking up work). Newest entry on top. Write it at 22:00 IST; read it at 10:00 IST. Progress numbers come from [PROGRESS.md](PROGRESS.md).

## Entry template

```
## YYYY-MM-DD — <name>
Phase: <n> · Gate: <G-n status>
Done today: T-xx (PR #), T-yy
In progress: T-zz — <where it stands, next step>
Blocked: <what / who can unblock>
Decisions made: D-0xx (logged)
Heads-up for teammate: <files you touched in their track, env changes, new keys>
Tomorrow: T-…
```

---

## 2026-10-24 (late) — Claude for Johny (Phase 02 part 1)

Done: MCP gateway with tiers + approvals (T-20/21), voice approvals (T-26), location tools on OpenStreetMap (T-24), dashboard Actions timeline with Approve/Deny (T-25 partial). 83 tests green. Services running on Johny's Mac (API :8000, web :3000, agent).
Try: "How long will it take to drive from Koramangala to Indiranagar?" / "Find a dental clinic in HSR Layout".
Next: Calendar (Google OAuth client), Slack (bot token), Notion (integration token) — add to `infra/mcp_servers.yaml`. Twilio still needs Account SID (AC…) + number.

---

## 2026-10-24 (night) — Claude for Johny (T-14 supervisor, T-15 dashboard)

Phase: 1 · Gate G1: all code in place, needs one live run

Done: T-14 supervisor (`delegate_task` tool, 7 specialists, fast acks, background jobs) · T-15 dashboard v0 (`apps/web`) · token dispatches the `rex` agent. 56 Python tests + web typecheck/lint/build green.
How to run everything locally (3 terminals, repo root):
1. `uv run --env-file .env uvicorn rex_api.main:app --port 8000`
2. `uv run --env-file .env python -m rex_agent dev`
3. `cd apps/web && npm install && npm run dev` → http://localhost:3000 → Talk to Rex
Decision: D-021 — LiveKit function tools instead of LangGraph for v1.
Heads-up for Shanky: Phase 02 = give specialists real executors. Pass them in `Rex.__init__` → `Supervisor(executors={...})`; each executor is `async (request, lang) -> ExecResult` and should call tools through the MCP gateway (T-20).

---

## 2026-10-24 (evening) — Claude for Johny (Phase 01 voice loop)

Phase: 1 · Gate G1 (Hindi answer < 2 s): code ready, live check pending

Done: keys in `.env` (Gnani, Gemini, Mistral, Groq, Twilio API key pair, LiveKit). Groq added to router (D-020). `POST /v1/livekit/token`. `apps/agent` voice worker (Prisma STT → Gemini/Groq/Mistral → Timbre TTS). 42 tests green.
In progress: T-10/T-11/T-12 — need the first live run on a Mac (steps in `apps/agent/README.md`).
Blocked: Remote session can't reach Gnani/LiveKit/LLM/Hugging Face (network allowlist). Twilio still needs Account SID (AC…) + number.
Heads-up for Shanky: `rex_agent.models.build_llm()` is the LLM entry point for the voice session; the supervisor graph (T-14) should plug in as the Agent's LLM node or tools.
Next: Johny → live-test the agent, tune VAD/turn delay, then T-15 dashboard v0. Shanky → T-14 supervisor, T-16 auth.

---

## 2026-10-24 — Claude for Johny (Phase 00 build)

Phase: 0 · Gate G0: partially met

Done today: T-01 workspace scaffold, T-05 shared schemas, T-13 LLM router (17 tests green on Johny's laptop).
In progress: T-02 accounts, T-03 compose (file ready, needs `make infra-up`), T-04 memory setup (needs `cp mcp.json.example .mcp.json` + claude-mem install).
Blocked: nothing.
Decisions: D-019 name = Rex; calls open in English ("Hello, this is Rex, Johny's AI assistant").
Heads-up for Shanky: Makefile/CI/pre-commit are templates in `setup/` — copy them once (see `setup/README.md`). T-14 Supervisor is ready to start; use `rex_llm_router.LLMClient().complete("supervise", messages)`.
Tomorrow: Johny → T-02 keys, T-10 Prisma STT. Shanky → T-03 infra-up, T-14 supervisor, T-16 API v0.

---

## 2026-10-24 — Johny (kick-off)

Phase: 0 · Gate: G0 not started

Done today:
- Planning finished: master plan doc, docs pack (this repo), project graph seeded.
- Decisions D-001 … D-018 logged.

In progress:
- T-02 accounts: Twilio trial — verify both phones next; Gnani key in hand.

Blocked:
- Nothing.

Heads-up for Shanky:
- Start T-01 (monorepo scaffold) and T-03 (docker-compose) tomorrow morning.
- Please install claude-mem and approve the `project-graph` MCP server when Claude Code asks (see CLAUDE.md).

Tomorrow:
- Johny: T-02, T-04, then T-10 (Prisma STT in LiveKit).
- Shanky: T-01, T-03, T-13 (LLM router).
