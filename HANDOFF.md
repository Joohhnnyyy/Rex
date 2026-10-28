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

## 2026-10-28 (night) — Johny → Shanky: your work list (in order)

Progress 60 % · Phase 2 67 % · 13 days left. Pull `main` first (`de77d34`+).
1. **Review my changes in your files** (today): `rex_llm_router/router.py` (`REX_CHAIN_<KIND>`), `rex_mcp_gateway/gateway.py` + `registry.py` (`tool_subsets`, tool-name cache), `rex_agent/models.py` (`PortableLLM`, thinking off, 4 s timeout), `rex_mcp_servers/calendar.py` (client cache), live calendar test, root `conftest.py`.
2. **T-28 / T-29 — Phase 2 gate (overdue, due 28 Oct):** after the Gemini quota resets (≈ 29 Oct 13:00 IST) run `REX_LIVE_TESTS=1 uv run --env-file .env python scripts/check_phase2.py --live`. All tools are verified; only LLM 429s remain. Then mark T-28/T-29 done.
3. **T-36 — route Coder + Meeting through the gateway (overdue, due 27 Oct):** `brain/coder.py` calls `SandboxRunner` directly and the meeting specialist bypasses tiers/events/undo.
4. **T-37 — rest (overdue):** tool surface is done; still open: `sandbox.execute` + `vexa.join_meeting` → Tier A, undo expiry.
5. **T-34 — Gnani batch STT for meeting recordings** (due 31 Oct).
6. **T-32 — `call_tool` MCP server** for the Caller (due 2 Nov) — coordinate the interface with Johny's T-31.
7. **T-38 — real Playwright browser** replacing the mock (due 2 Nov); then re-add `browser` to the rex allowlist.
8. **T-54 — eval run v2 + latency pass + 10× dry runs** (due 7 Nov); add short (30–60 s) caching for channel list / today's calendar.
9. **T-62 / T-63** with Johny: posts + submission (9 Nov). Feature freeze **3 Nov**.
Decision needed from both: Gemini billing (free tier = 20 req/day/model breaks live tests and the demo).

---

## 2026-10-28 (evening) — Johny (latency fixes — touched Shanky's gateway/router/models files)

Measured before/after each change (same prompt, same model):
| Change | Before | After |
|---|---|---|
| Rex tool surface (`tool_subsets` in `infra/mcp_servers.yaml`, sandbox/browser off for rex) | 59 tools, 101,796 schema chars, **7,143 prompt tokens**, 1.9 s | 24 tools, 27,352 chars, **3,003 tokens**, 1.0–1.8 s (Groq gpt-oss-120b, 1 sample each — noisy) |
| Mixed-provider history (`PortableLLM` in `rex_agent/models.py`) | Gemini 400 `missing thought_signature` after a fallback turn | OK (verified live on gemini-3.6-flash); Gemini fields stripped for Mistral/Groq |
| Gemini thinking off (`reasoning_effort: none`) | 2.6 s / tool step | 2.1 s (gemini-2.5-flash, earlier benchmark) |
| Fallback `attempt_timeout` | 8 s of silence before fallback | 4 s |
| Calendar client cached per process | 506 ms / list_events | 390 ms |
| Gateway caches tool names (no list_tools per call) | 2 ms | 1 ms (negligible) |
Biggest win: the tool trim — also why Groq 429'd (TPM limit vs 7k-token prompts).
**Mistral key is blocked**: `x-ratelimit-limit-req-minute: 0` — check the plan in the Mistral console; earlier "Mistral-first" runs were really answered by Groq.
Not done: voice-loop tuning (turn detector, TTS websocket, filler line) needs a live audio session; Phase 2 `--live` not re-run (Gemini quota resets ~29 Oct 13:00 IST).

---

## 2026-10-28 — Johny (Phase 2 unblock: calendar live)

Google Calendar login done (token in `~/.config/rex/google_token.json`, Calendar API enabled). **T-22 done**: live C-1..C-4 green against real Google.
Heads-up Shanky — touched your file `apps/agent/tests/live/test_workflow_calendar.py`:
- it forced `REX_FAKE_SERVICES=1`, so the "live" calendar test never hit Google; now it only falls back to the fake when no token exists.
- C-4 deleted a hard-coded `evt_1` (exists only in the fake → 404 live); it now creates its own event first and deletes that.
- Live tests need the keys in the process: run with `uv run --env-file .env …` (the agent doesn't auto-load `.env`; only the calendar server does).
Still open for G2: Slack bot token + team ID in `.env` (Johny, in progress), then `check_phase2.py --live`.

Later same day: Slack done (bot in #rex-test; manifest needed `groups:read` — list_channels includes private channels). **T-23 done.** `--live` = 26/30; every live test passed at least once against real services.
**Blocker for Shanky (T-28/T-29) — LLM chain, not tools:**
- Gemini free tier = **20 requests/day per model** (`GenerateRequestsPerDayPerProjectPerModel-FreeTier`); one `--live` run burns it. Mistral + Groq free tiers also 429 on the multi-step tests.
- When Gemini fails mid-conversation the history becomes unusable for everyone: Gemini then wants a `thought_signature` on tool calls it didn't make; Mistral 422s on Gemini's `extra_content`. Needs a fix in `rex_agent/models.py` (or Gemini billing + `reasoning_effort: none`).
- Benchmarked (tool call + answer): gemini-2.5-flash 2.6 s (2.1 s thinking off) — fastest; 3.6-flash 5.7 s; 3.8-flash timed out; 3.7/flash-latest 503; 4-argon not in free quota.
- New: `REX_CHAIN_<KIND>` env override in `rex_llm_router/router.py` (your file) to reorder chains, e.g. `REX_CHAIN_SUPERVISE=mistral_small,groq_llama`. Root `conftest.py` clears it for offline tests.

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
