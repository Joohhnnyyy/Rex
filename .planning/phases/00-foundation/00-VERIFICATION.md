# Verification — Phase 00

Run on Johny's laptop (remote session), 2026-10-24.

| Check | Command | Result |
|---|---|---|
| Install | `uv sync` (Python 3.12) | ✅ |
| Unit tests | `uv run pytest` | ✅ 17 passed |
| Lint | `uv run ruff check .` | ✅ All checks passed |
| Format | `uv run ruff format --check .` | ✅ 16 files formatted |
| Compose file | `docker compose -f infra/docker-compose.yml config -q` | ✅ valid (run in cloud sandbox) |
| Compose up | `make infra-up` | ⏳ needs Docker on a laptop |
| Live LLM call | `uv run --env-file .env python scripts/llm_smoke.py` | ⏳ needs GEMINI/MISTRAL keys |

Gate G0 ("both run make dev"): **partially met** — remaining: copy `setup/` templates, Docker up, keys in `.env`, Shanky runs the same checks.
