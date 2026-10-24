# Rex

## What this is
Rex is a multilingual, voice-first AI operator. You speak (English, Hinglish or one of 10 Indian languages; other languages via fallback) and Rex acts across Google Calendar, Slack, Notion, Google Maps, GitHub, a code sandbox, Twilio phone calls, a meeting bot, the browser and your screen. Built on Gnani Prisma STT + Timbre TTS for the Gnani AI Great Indian AI Internship Challenge.

## Core value
One voice that *does* things across your apps, in your language, and always asks before anything risky.

## Who it's for
Students, freelancers and small-business owners in India who juggle many apps and speak code-mixed languages.

## Constraints
- Deadline: 2026-11-10 23:59 IST; public social post must be live before submission.
- Team of 2: Johny (voice, telephony, desktop, frontend) and Shanky (orchestrator, MCP tools, backend, coder).
- ≥ 1 Gnani model on every voice path. Synthetic data only. Free tiers (Gemini, Mistral, Twilio trial, LiveKit Cloud free).

## Key decisions
See `../DECISIONS.md` (D-001 … D-019). Highlights: LiveKit Agents + Gnani plugins; Gemini/Mistral/Codestral router; MCP gateway with R/W/A tiers; Twilio via LiveKit SIP; Tauri desktop + Playwright; calls open in English: "Hello, this is Rex, {user}'s AI assistant."

## Source documents
`../PRD.md`, `../ARCHITECTURE.md`, `../IMPLEMENTATION_ROADMAP.md`, `../PROGRESS.md`.
