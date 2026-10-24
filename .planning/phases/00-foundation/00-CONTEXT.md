# Phase 00 — Foundation: context

## Goal
A Python workspace that both teammates can run, with the first two real building blocks tested: the shared data contracts and the LLM router.

## Decisions locked for this phase
- Python 3.12, `uv` workspace, `hatchling` builds, `ruff` + `pytest`. Packages use a `src/` layout and a `rex_` prefix.
- Shared contracts live in `packages/shared` (`rex_shared`) as Pydantic v2 models — the single source of truth (TS types generated later in Phase 01).
- LLM router talks to every provider through the **OpenAI-compatible chat completions** API (Gemini's OpenAI-compatible endpoint, Mistral, OpenRouter) with one small `httpx` client — no vendor SDKs.
- Fallback rule: on HTTP 429 / 5xx / timeout, try the next model in the task's chain; 4xx other than 429 is a real error and is raised.
- Docker Compose holds Postgres (pgvector) + Redis only for now; Langfuse/Vexa added when needed.
- Web (Next.js) and desktop (Tauri) scaffolds are created in Phase 01 by Johny (T-15) and Phase 04 (T-42).

## Out of this phase
Voice, MCP gateway, DB models, auth.

## Workflow
Superpowers: design in `docs/plans/2026-10-24-rex-foundation-design.md`, bite-sized TDD plan in `00-01-PLAN.md`, test-first, verify before claiming done.
