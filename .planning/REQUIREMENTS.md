# Requirements

IDs match `../PRD.md` (F-xx). v1 = must ship for the demo. v2 = stretch. Out of scope listed last.

## v1

| ID | Requirement | Phase | Owner |
|---|---|---|---|
| VOICE-01 (F1) | Streaming voice loop with Gnani Prisma STT + Timbre TTS, VAD, barge-in | 1 | Johny |
| VOICE-02 (F2) | Per-turn language detection; reply in same language; fallback STT/TTS for others | 1, 5 | Johny |
| BRAIN-01 (F3) | Supervisor routes to specialists; fast spoken ack for slow tasks | 1 | Shanky |
| BRAIN-02 | LLM router: Gemini / Mistral / Codestral with automatic fallback on rate limits | 1 | Shanky |
| TOOL-01 (F4) | Calendar: free/busy, create, move, cancel, invite | 2 | Shanky |
| TOOL-02 (F5) | Slack: read, summarise, post | 2 | Shanky |
| TOOL-03 (F6) | Notion: create, append, search | 2 | Shanky |
| TOOL-04 (F7) | Maps: place search, ETA, share pin | 2 | Shanky |
| SAFE-01 (F13) | Permission tiers R/W/A in gateway; approval for A by voice or dashboard | 2 | Shanky + Johny |
| UI-01 (F14) | Dashboard: transcript, timeline, approvals, connections | 1, 2, 5 | Johny |
| CALL-01 (F8) | Outbound Twilio call books a slot and reports a structured outcome | 3 | Johny |
| MEET-01 (F9) | Meeting bot → Gnani batch STT → minutes to Notion + Slack | 3 | Shanky + Johny |
| CODE-01 (F10) | Coder: sandbox fix, tests, draft PR | 4 | Shanky |
| SCREEN-01 (F11) | Desktop companion: push-to-talk + screen explain | 4 | Johny |
| WEB-01 (F12) | Browser control via Playwright with approval | 4 | Shanky |
| SAFE-02 | Undo for Tier W; prompt-injection guard | 5 | Shanky |

## v2 (stretch)
MEM-01 long-term memory (F15) · BRIEF-01 morning briefing (F16) · MAIL-01 Gmail (F17) · CALL-02 inbound receptionist (F18) · SKILL-01 skill store (F19).

## Out of scope
Mobile app, payments, WhatsApp, voice cloning, full desktop computer-use, multi-tenant billing.
