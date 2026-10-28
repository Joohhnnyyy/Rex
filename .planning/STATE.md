# State

_Last updated: 2026-10-28 (evening) by Claude (session with Johny)._

## Position
Phase **02 Core tools** — Calendar, Slack and Notion verified live against real services (T-22, T-23 done). `check_phase2.py`: offline 27/28, `--live` 26/30; every live test has passed at least once — remaining failures are free-tier LLM limits, not tools. Latency pass landed: rex tools 59 → 24 (prompt 7,143 → 3,003 tokens), mixed-provider history fix, Gemini thinking off. Overall progress 60 % (`../PROGRESS.md`).

### Earlier
Phase 00 Foundation and Phase 01 voice loop built; Phase 01 gate (spoken answer < 2 s) still not measured live.

## Next actions
1. Johny: unblock Mistral key (0 req/min) or add Gemini billing; close voice loop (T-10/11/12, p50 ≤ 1.8 s); start **T-30 Twilio SIP trunk** (critical path, due 29 Oct).
2. Shanky: re-run `check_phase2.py --live` after the Gemini quota resets (≈ 29 Oct 13:00 IST) → T-28/T-29; T-36; rest of T-37. Full list in `../HANDOFF.md` (28 Oct).

## Open decisions
Gemini billing vs free tier (blocks reliable live tests + demo) · D-010 Vexa hosted vs self-host · D-012 fallback TTS.

## Blockers
LLM quota: Gemini free tier 20 requests/day/model; Mistral key allows 0 requests/min.
