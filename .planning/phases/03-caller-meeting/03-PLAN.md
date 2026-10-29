# Phase 03 — Caller + Meeting (plan, 2026-10-29)

**Gate G3:** demo steps 1–3 run end to end, live (`scripts/check_phase3.py --live`). Target **3 Nov** (feature freeze, D-035); 4 Nov is buffer.

| Demo step | Needs |
|---|---|
| 1. "Standup ke minutes Notion mein daalo aur team ko Slack karo" | Vexa bot in a real Meet (T-33) → Gnani batch STT (T-34) → minutes (T-35) → Notion + Slack (verified in Phase 2) |
| 2. "Dentist ko call karke Saturday shaam ka slot book karo" | Twilio SIP (T-30) → Caller agent (T-31) → `call_tool` returns `CallOutcome` (T-32) |
| 3. Slot on Calendar; clinic location + ETA on Slack | T-39 glue: `CallOutcome` → `calendar.create_event`; `location.find_place` + `travel_time` → `slack_post_message` |

## Critical path
T-02 Twilio Account SID + number + verified phone → **T-30** → **T-31** → **T-32** → **T-39**. Everything else runs beside it.

## Schedule

| Date | Johny | Shanky |
|---|---|---|
| 29–30 Oct | T-02 Twilio SID/number; **T-30** trunk, test call rings a verified phone; T-10/11/12 live voice (p50 ≤ 1.8 s) | **T-29** Phase 2 gate (`check_phase2.py --live`); T-36; rest of T-37 |
| 31 Oct | T-30 done; T-31 skeleton (8 kHz STT/TTS, disclosure line) | **T-34** batch STT; agree `call_tool` interface with Johny |
| 1–2 Nov | **T-31** books a slot with Shanky playing the clinic | **T-32** `call_tool` (start/status/hangup → `CallOutcome`); T-38 real browser |
| 2–3 Nov | Live run of step 1 from a real Meet (T-33/T-35 only have offline tests so far, D-036) | **T-39** step-3 glue + `check_phase3.py --live` |
| 3 Nov | **G3** — both run steps 1–3 live; feature freeze | |
| 4 Nov | Buffer / fixes only | |

## Risks
- **R-02 Twilio trial:** calls only to verified numbers, trial message plays first → verify Shanky's phone on 30 Oct; trial message is fine for the demo.
- **R-04 LLM limits:** chain is Gemini → Groq → Nemotron (D-037) → Mistral → OpenRouter. Nemotron (~3.9 s/turn) keeps tests running but is too slow for a live call. Decision still open: Gemini billing or Groq Developer tier before 3 Nov.
- **R-05 meeting bot admission:** admit the bot by hand; synthetic recording as fallback for step 1.
- Phase 1 gate (spoken answer < 2 s) never measured live — the Caller depends on the same loop, so T-10/11/12 come first.

## Cut if late (in this order)
Diarisation in T-34 (plain transcript is enough) → live Meet for step 1 (use a recording) → ETA in step 3 (location pin only).
