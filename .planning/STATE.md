# State

_Last updated: 2026-10-24 (evening) by Claude (session with Johny)._

## Position
Phase **01 Voice loop**: plans 01-01 (agent worker) and 01-02 (supervisor + dashboard v0) built; live verification pending on a Mac. Next: Phase 02 (MCP gateway + calendar/Slack/Notion/Maps).

### Earlier
Milestone v1 · **Phase 00 Foundation** — plan 00-01 executed, verification partial (see `phases/00-foundation/00-VERIFICATION.md`). Overall progress 11 % (`../PROGRESS.md`).

## Next actions
1. Johny: copy `setup/` templates + `cp mcp.json.example .mcp.json`; install Superpowers + GSD + claude-mem in Claude Code; finish accounts (T-02); add keys to `.env`; run `scripts/llm_smoke.py`.
2. Shanky: `uv sync && uv run pytest`; `make infra-up` (T-03); start **T-14 Supervisor LangGraph v1** (ready — all deps done).
3. Johny: start **T-10 Prisma STT in LiveKit** once Gnani + LiveKit keys are in `.env`.

## Open decisions
D-010 Vexa hosted vs self-host (by 30 Oct) · D-012 fallback TTS (by 1 Nov).

## Blockers
None.
