# Summary 00-01 — Workspace, shared schemas, LLM router

Completed 2026-10-24 (built by Claude with TDD; review: Shanky).

## Delivered
- **uv workspace** (Python 3.12): `packages/shared` (rex_shared), `packages/llm_router` (rex_llm_router), `apps/api` (rex_api). Ruff + pytest configured in root `pyproject.toml`.
- **Shared contracts** `rex_shared.schemas`: `Tier`, `ActionEvent`, `ApprovalRequest` (+ `is_expired`), `CallOutcome` (booked ⇒ slot required), `ActionItem`, `Minutes`, `Turn`.
- **LLM router**: chains per task (`supervise`, `summarise`, `code`, `vision`); one OpenAI-compatible async client for Gemini / Mistral / OpenRouter; falls back on 429, 5xx, timeout, network error; raises on other 4xx; skips providers without keys; records every attempt with latency. Model ids overridable via `REX_MODEL_<ALIAS>`.
- **API skeleton**: `GET /healthz`.
- **Infra**: `infra/docker-compose.yml` (pgvector pg16, redis 7, health checks).
- **Templates** in `setup/` (Makefile, CI workflow, pre-commit) — remote tools can't write those paths; copy once.
- `scripts/llm_smoke.py` for a live check once keys are in `.env`.

## Tests
17 tests, all offline (httpx MockTransport). Ruff lint + format clean.

## Deviations from plan
- Makefile / CI / pre-commit shipped as templates (protected paths).
- Graph moved from `.claude/memory/` to `memory/` (protected path).
