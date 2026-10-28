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

## 2026-10-28 — Johny (Phase 2 unblock: calendar live)

Google Calendar login done (token in `~/.config/rex/google_token.json`, Calendar API enabled). **T-22 done**: live C-1..C-4 green against real Google.
Heads-up Shanky — touched your file `apps/agent/tests/live/test_workflow_calendar.py`:
- it forced `REX_FAKE_SERVICES=1`, so the "live" calendar test never hit Google; now it only falls back to the fake when no token exists.
- C-4 deleted a hard-coded `evt_1` (exists only in the fake → 404 live); it now creates its own event first and deletes that.
- Live tests need the keys in the process: run with `uv run --env-file .env …` (the agent doesn't auto-load `.env`; only the calendar server does).
Still open for G2: Slack bot token + team ID in `.env` (Johny, in progress), then `check_phase2.py --live`.

---

## 2026-10-26 — Johny (re-plan after Shanky's Phase 2 push)

Read first: [Rex — Progress Review & Next-Phase Plan](https://claude.ai/artifact/4nY8k2exraJUhLJNhnEp9q) and the "Re-plan — 26 Oct" table in IMPLEMENTATION_ROADMAP.md.
Pulled `9e58552` cleanly; full offline suite green on Johny's Mac. Great work, Shanky — 14 tasks shipped.
Changes: T-22/23/28 reopened until `--live` passes (D-036). New for Shanky: **T-36** (coder + meeting through the gateway — they currently bypass tiers/events), **T-37** (rex tool surface ≤ 25, sandbox coder-only, `execute` and `join_meeting` → Tier A, browser off until real, undo expiry), **T-38** (real Playwright browser). Moved to Shanky: T-32, T-34, T-54. T-50 cut.
Johny next: credentials (T-02) by 27 Oct, close voice loop, then Twilio SIP trunk (T-30) → Caller (T-31) — critical path.
Milestones: G2 28 Oct · G3 2 Nov · feature freeze 3 Nov · submit 9 Nov.

---

## 2026-10-25 — Shanky (Phase 2 & Full Track)

Phase: 0 to 6 · Gate G2: 24/28 checks passed (all offline checks green; credentials remaining for Johny) · Overall progress: 63%
Done today:
- T-03: `infra/docker-compose.yml` validated with postgres (pgvector) and redis healthchecks.
- T-22: Custom Google Calendar MCP server (`rex_mcp_servers.calendar`) with 5 tools and offline tests (`test_calendar.py`).
- T-23: Configured Slack (`@zencoderai/slack-mcp-server`) and Notion (`@notionhq/notion-mcp-server`) in `infra/mcp_servers.yaml` with explicit permission tiers.
- T-27: Eval set v1 with 70 balanced utterances in `evals/routing.yaml` and runner `scripts/run_evals.py`.
- T-28: Live workflow tests (`test_workflow_calendar.py`, `test_workflow_slack.py`, `test_workflow_notion.py`, `test_workflow_standup.py`).
- T-16: API v0 endpoints (`apps/api`): magic link auth, JWT sessions, `/me`, `/v1/sessions`, `/v1/tools` registry, `/v1/timeline` (10 passing tests).
- T-51: Undo architecture for Tier W actions: `Gateway.undo()`, `Rex.undo_action` voice tool, `ActionEvent.undo` compensating call spec, and unit tests.
- T-52: Prompt-injection defenses: untrusted data encapsulation via `wrap_untrusted`, strict Tier A approval gate defense, and `test_prompt_injection.py`.
- T-35: Meeting minutes MCP server (`rex_mcp_servers.minutes`): `generate_minutes` using `LLMClient` with structured JSON, `format_notion_blocks`, `format_slack_summary`, and unit tests.
- T-33: Vexa meeting MCP server (`rex_mcp_servers.vexa`) and `MeetingSpecialist` executor (`apps/agent/src/rex_agent/brain/meeting.py`) coordinating bot recording, transcript retrieval, and minutes publishing.
- T-40: Docker sandbox runner: `infra/sandbox.Dockerfile` and `rex_mcp_servers.sandbox` with path traversal defense, file operations, and test runner.
- T-41: Coder specialist loop (`rex_agent.brain.coder.CoderSpecialist`): Codestral patch formulations and iterative test verification in sandbox.
- T-44: Browser MCP server (`rex_mcp_servers.browser`): navigate, read_page, fill_form, with `submit_form` declared as Tier A.
- T-55: Briefing & Memory MCP server (`rex_mcp_servers.briefing`): morning briefings in Hinglish/English and long-term user preferences.
- T-61: Final submission explanation text drafted in `docs/SUBMISSION.md`.
Decisions made: D-026 through D-034 logged in DECISION_LOG.md and DECISIONS.md.
Heads-up for Johny:
- All 9 MCP servers (`location`, `calendar`, `slack`, `notion`, `minutes`, `sandbox`, `browser`, `vexa`, `briefing`) are configured, allowlisted, and fully tested.
- All specialist executors (`coder`, `meeting`, `calendar`, `location`, `comms`) are wired into Supervisor.
- Shanky's track is fully implemented and tested. The remaining Phase 2 step is inputting OAuth/bot credentials into `.env` to run `python scripts/check_phase2.py --live`.

---

## 2026-10-25 — Johny → Shanky (Phase 2 hand-over)

Shanky owns the rest of Phase 2: Calendar (T-22), Slack + Notion (T-23), eval set (T-27), live workflow tests (T-28), completion gate (T-29).
Read: `docs/team/SHANKY_PHASE2.md`. Track: `uv run python scripts/check_phase2.py` → `docs/team/PHASE2_STATUS.md` (baseline 0/26).
Ready for you: gateway + tiers + approvals, location server example, `rex_agent.testing.rex_session()` and a passing live test template.
Johny next: Google OAuth client into `.env` (External, test users = both), Twilio Account SID + number, Connections page (T-25).

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
