# AGENTS.md — instructions for AI coding agents

This file is read by any AI coding agent (Claude Code, Codex, Cursor, Gemini CLI, Aider…) working in this repo.

## Read first

1. [PROJECT_CONTEXT.md](docs/team/PROJECT_CONTEXT.md) — what and why.
2. [ARCHITECTURE.md](docs/team/ARCHITECTURE.md) — system design and component flow.
3. [DECISION_LOG.md](docs/team/DECISION_LOG.md) — chronological log of technical decisions (D-001 through D-049).

## Repo map

| Path | Language | What lives there |
|---|---|---|
| `apps/agent/` | Python | LiveKit worker, Gnani STT/TTS adapters, VAD, supervisor, desktop accessibility, screen vision, research |
| `apps/api/` | Python | FastAPI app: LiveKit token minting, connections, memory, discoveries, files |
| `apps/web/` | TypeScript | Next.js 15 dashboard, living SVG mascot engine, timeline, approval drawer |
| `packages/mcp_gateway/` | Python | MCP client hub, tiers (R/W/A), audit log, undo engine |
| `packages/mcp_servers/` | Python | MCP servers (calendar, gmail, browser, files, memory, discoveries, minutes, sandbox, location, vexa) |
| `packages/llm_router/` | Python | Model router (Gemini, Groq, Mistral, Codestral) + PortableLLM normalizer |
| `packages/shared/` | Python | Pydantic schemas and shared data definitions |
| `infra/` | YAML/Docker | MCP server registry (`mcp_servers.yaml`) and Docker sandbox |

## Commands

```bash
make dev          # run agent + api with reload
make check        # lint and run complete test suite
make test         # run pytest suite
make lint         # ruff lint and format check
make fmt          # auto-format with ruff
```

## Rules

1. **Schemas first.** Any new cross-boundary data shape goes into `packages/shared`.
2. **Every new tool is MCP** and goes through the gateway with a declared tier (R/W/A). Never call a third-party API directly from an agent prompt or specialist.
3. **Never commit secrets.** Use `.env` (git-ignored) and `settings.py`. Tests use fakes, not real keys.
4. **Synthetic data only** in fixtures, seeds, prompts and screenshots. No real phone numbers or personal data.
5. **Gnani stays in the voice path.** Primary STT and TTS must use Gnani Prisma and Timbre WebSocket streams.
6. **Latency budget**: anything in the voice loop must not add > 50 ms; heavy work goes to background tasks.
7. **Log, don't print.** Use `structlog` with `session_id`, `turn_id`, `tool`.
8. **Tests**: new tools need a unit test with an injectable client or fake MCP server.
9. **Record decisions**: Record any non-trivial design choice or pivot in [DECISION_LOG.md](docs/team/DECISION_LOG.md).

## Definition of done

Code committed · tests + `make check` green · documentation aligned with reality.
