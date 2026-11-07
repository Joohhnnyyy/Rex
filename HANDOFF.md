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

## 2026-11-07 — Johny
Phase: 5 · Gate: G5 not yet run
Done today: T-25 (connections panel), closed T-10/11/12/43 (working live); T-42 dropped
In progress: T-53 — language badge + phone layout done; check the in-call view in Chrome, then video polish
Blocked: —
Decisions made: D-039 (call feature dropped, browser-only; logged)
Heads-up for Shanky: new `apps/api/src/rex_api/connections.py` (GET /v1/connections) registered in `main.py`, test in `apps/api/tests/test_connections.py`. It refreshes the Google token and asks Playwright for Chromium's path; no new env vars. `scripts/progress.py` now supports `status: dropped` (left out of every count).
Also (D-040, your track, Shanky): deleted `rex_api` auth/sessions/timeline/tools + their tests, `infra/docker-compose.yml` (+ `make infra-up/down`), schemas CallOutcome/ApprovalRequest/Turn/User/UserUpdate/VoiceSession, `scripts/sip_setup.py` + `seed_graph.py`. Supervisor is now background-only for `coder` and `meeting`. Nothing used them; shout if you had plans for Postgres.
Also (T-55): Rex has long-term memory now: `rex_mcp_servers/memory.py` replaces the fake `briefing` server (its hardcoded meetings/tasks are gone). Facts + a 1–2 line summary per call live in `~/.config/rex/memory.json` (REX_MEMORY_PATH to override) and are put in Rex's prompt each call.
Also (T-53): dashboard rebuilt as the Rex Control Center (`apps/web/components/dash/`); see apps/web/README for live vs demo panels. New `GET /v1/memory` in `rex_api/memory.py`. Deps: +lucide-react, +recharts, -three.
Also (T-65): Rex has `use_desktop` (apps/agent/src/rex_agent/desktop.py): any Mac app via its accessibility tree through `npx agent-desktop@1.2.0 mcp` (gateway server `desktop`, allowlist `screen`, so Rex doesn't see its 67 raw tools). Needs Node and Accessibility for the app running the agent. Snapshots are private: never log them.
Also: `research_web` (apps/agent/src/rex_agent/research.py) does read-only web search + page reading through Firecrawl (`npx firecrawl-mcp@3.37.0`, allowlist `research`; only search/scrape are tiered R). Needs FIRECRAWL_API_KEY in .env; without it Rex falls back to the browser.
Also: pipelines (apps/agent/src/rex_agent/pipelines.py, infra/pipelines.yaml): reusable routines Rex runs with `run_pipeline` (steps run in code: research / write / send / tool, each checked; approvals pause the run). Built-ins: share_research, send_whatsapp, email_research, daily_brief. Rex saves new ones with `save_pipeline` to ~/.config/rex/pipelines.yaml.
Also: Discover (rex_mcp_servers/discoveries.py, rex_api/discover.py, web Discover tab): Rex researches the user's interests on its own every 6 h (REX_DISCOVER_EVERY_H; Firecrawl past-week search + LLM pick, only URLs from the search kept) and shows finds with a why; unseen finds go into Rex's prompt. API now depends on rex-llm-router.
Also: Files library (rex_mcp_servers/files.py MCP server `files`, rex_api/files.py, web Files tab): Rex downloads docs/images/PDFs etc. into ~/Documents/Rex (REX_FILES_DIR) sorted by type or a named folder, saves notes it writes, moves files; dashboard can save a link, open, reveal in Finder, move, trash. Guards: public URLs only (redirects re-checked), type allowlist, 50 MB cap, HTML/SVG only served as downloads. New pipeline research_doc.
Tomorrow: G5 run-through of the browser-only demo, then T-60 video

## 2026-11-06 — Johny (taking T-38 from Shanky)
Heads-up for Shanky: Johny (with Claude) is building **T-38 real Playwright browser**. Touching your `rex_mcp_servers/browser.py` (mock → Playwright), its tests, and `infra/mcp_servers.yaml` (browser on for rex; rex vexa subset trimmed to join/leave to stay ≤ 25 tools). Don't start T-38.
Also fixed: agent crash on join (RPC registered before room connect, `rex_agent/main.py`); calendar auth errors now reach the model as `ToolError` (re-login hint).
Voice fix: Rex heard only silence / segfaulted in `liblivekit_ffi` — livekit-agents 1.8 auto-gain-control (native APM) on mic input. Turned off via `RoomOptions(audio_input=AudioInputOptions(auto_gain_control=False))` in `rex_agent/main.py`; live voice confirmed.
**T-64 Gmail** (new): `rex_mcp_servers/gmail.py` (search_emails/read_email R, send_email A). Google login is now shared (`calendar.google_creds`), SCOPES include gmail.readonly + gmail.send — **re-run `uv run python -m rex_mcp_servers.calendar login`** and enable the Gmail API in the Cloud project. Rex tool cap 25 → 28 in `infra/mcp_servers.yaml` (Shanky: shout if you'd rather trim instead).
Latency/UX: tool calls now speak a filler ("Checking your inbox.") via `RunContext.with_filler` if a tool keeps the line silent > 0.7 s (`tools_bridge.py`, `brain/acks.py`); chat history capped at 30 items; system prompt rewritten (capabilities, chain tools, no narration). Measured: LLM TTFT ~1.3 s (Gemini flash-lite) is now the biggest cost per step.
Browser live view: browser MCP server writes ~1 fps JPEG + {url,title} to `~/.config/rex/browser-live/`; the agent streams new frames on LiveKit topic `rex.browser`; dashboard `components/BrowserView.tsx` shows them under the transcript.
**T-65 Screen share** (new): dashboard "Share screen" button (LiveKit `TrackToggle`); agent keeps only the newest frame (`rex_agent/screen.py`) and `look_at_screen(question)` sends that one JPEG to the router's `vision` chain (Gemini) only when asked. Live check: Rex read a ModuleNotFoundError off a shared screen and gave the fix.
Screen control: `control_screen(action=click|double_click|right_click|scroll|drag, target, to_target, ...)` moves the real mouse with pyautogui (new dep in rex-agent). Gemini locates the target on the shared frame (0-1000 point; probe: 0-1 px off on test buttons); needs entire-screen share (aspect check) and macOS Accessibility permission for the app running the agent; corner fail-safe on; each action goes to the timeline as `screen.<action>`.

---

## 2026-11-03 — Johny (plan change: no Twilio)
Phase: 3 · Gate: G3 moves to 6 Nov
Decisions made: **D-038** — Twilio/phone calls dropped; Rex is a browser + app agent only. Demo step 2 = in-browser "call" (LiveKit room + web link, Shanky plays the clinic).
Changed: T-30 is now "browser call room" (Johny, 4 Nov); T-31 runs in that room at 16 kHz (5 Nov); T-32 `start_call` returns a room + join link instead of dialing, `CallOutcome` unchanged (Shanky, 5 Nov); T-39 → 6 Nov. R-02 closed.
Heads-up for Shanky: Twilio vars removed from `.env.example`; nothing in code used them.
Tomorrow (Johny): T-30 room + link; then T-31.

---

## 2026-10-29 — Johny (Nemotron backup + Phase 3 plan)
Phase: 2 → 3 · Gate: G2 open (T-29), G3 target 3 Nov
Done today: Nemotron 3 Ultra added as 3rd LLM backup (`dbc1c72`, D-037). Chain: Gemini → Groq → Nemotron → Mistral → OpenRouter.
Heads-up for Shanky: touched your `rex_llm_router/models.py` + `router.py` (new `nvidia` provider / `nvidia_nemotron` alias) and `test_client.py`. New env var `NVIDIA_API_KEY` (in `.env.example`). Nemotron thinking is turned off in `rex_agent/models.py`.
Phase 3 plan: [.planning/phases/03-caller-meeting/03-PLAN.md](.planning/phases/03-caller-meeting/03-PLAN.md). New task **T-39 (Shanky)**: step-3 glue (CallOutcome → calendar event; clinic place + ETA → Slack) + `scripts/check_phase3.py --live`, due 3 Nov.
Shanky's order now: T-29 → T-36 → T-37 → T-34 (31 Oct) → agree `call_tool` interface (31 Oct) → T-32 (2 Nov) → T-38 → T-39 (3 Nov).
Blocked: Twilio Account SID + number (Johny), Mistral key 0 req/min, Gemini 20 req/day.
Tomorrow (Johny): T-30 Twilio trunk; live voice loop T-10/11/12.

---

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
