# AGENTS.md — instructions for AI coding agents

This file is read by any AI coding agent (Claude Code, Codex, Cursor, Gemini CLI, Aider…) working in this repo. Claude-specific additions live in [CLAUDE.md](CLAUDE.md).

## Read first

1. [PROJECT_CONTEXT.md](PROJECT_CONTEXT.md) — what and why.
2. [ARCHITECTURE.md](ARCHITECTURE.md) — where code belongs.
3. [IMPLEMENTATION_ROADMAP.md](IMPLEMENTATION_ROADMAP.md) — find the `T-xx` you are working on.
4. [HANDOFF.md](HANDOFF.md) — the latest state.

## Repo map

| Path | Language | What lives there |
|---|---|---|
| `apps/agent/voice/` | Python | LiveKit worker, Gnani STT/TTS adapters, VAD, language router |
| `apps/agent/brain/` | Python | LangGraph supervisor + specialist subgraphs, prompts |
| `apps/api/` | Python | FastAPI app, routers, services, Alembic migrations |
| `apps/web/` | TypeScript | Next.js dashboard |
| `apps/desktop/` | TS + Rust | Tauri companion |
| `packages/mcp_gateway/` | Python | MCP client hub, tiers, audit |
| `packages/mcp_servers/<name>/` | Python | Our MCP servers (`call_tool`, `screen_tool`, `approval_tool`, `skills_registry`, `minutes`) |
| `packages/llm_router/` | Python | Model selection and fallback |
| `packages/shared/` | Python → TS | Pydantic schemas (source of truth) and generated types |
| `infra/` | YAML/Docker | Compose, sandbox image, LiveKit and Caddy config |

## Commands

```bash
make dev          # run agent + api + web with reload
make check        # ruff + mypy + pytest + eslint + tsc
make test         # pytest -q && pnpm -r test
make types        # regenerate TS types from packages/shared
make migrate      # alembic upgrade head
make eval         # run routing + tool eval set (evals/)
python scripts/progress.py   # refresh PROGRESS.md from the project graph
```

## Rules

1. **Stay in your track.** Check the task owner in the roadmap; don't refactor the other person's track without a note in HANDOFF.md.
2. **Schemas first.** Any new cross-boundary data shape goes into `packages/shared` and `make types` is run in the same PR.
3. **Every new tool is MCP** and goes through the gateway with a declared tier (R/W/A). Never call a third-party API directly from an agent prompt or specialist.
4. **Never commit secrets.** Use `.env` (git-ignored) and `settings.py`. Tests use fakes, not real keys.
5. **Synthetic data only** in fixtures, seeds, prompts and screenshots. No real phone numbers — use `+91 90000 0000x` style placeholders or the team's verified test numbers from `.env`.
6. **Gnani stays in the voice path.** Fallback STT/TTS only when the language router says so.
7. **Latency budget**: anything in the voice loop must not add > 50 ms; heavy work goes to the job queue.
8. **Log, don't print.** Use `structlog` with `session_id`, `turn_id`, `job_id`.
9. **Tests**: new tools need a unit test with a fake MCP server; new prompts need ≥ 3 eval cases in `evals/`.
10. **Small PRs** (< 400 lines), title `T-xx: <what>`, link the task.

## Updating progress (required)

When you finish or block a task, update the project graph (see CLAUDE.md "Progress protocol"): set the task's `status` observation, add a dated note, then run `python scripts/progress.py`. Record any non-trivial choice in [DECISION_LOG.md](DECISION_LOG.md).

## Definition of done

Code merged · tests + `make check` green · docs touched if behaviour changed · graph status `done` · HANDOFF.md mentions it.
