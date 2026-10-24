# Project Context — Rex

One page that any human or AI agent should read before touching the repo.

## The one-liner

Rex is a multilingual, voice-first operator: you speak in Hinglish (or Tamil, Kannada, Bengali, English…), and it acts across your calendar, messages, notes, maps, code, phone and screen — asking before anything risky.

## Why it exists

- Indian users code-mix (Hinglish, Tanglish) and most assistants handle that badly. Gnani's Prisma STT is built for Indian languages and telephony audio.
- Students, freelancers and small-business owners juggle 5–8 apps. A single voice that can *act* (not just answer) saves real time.
- The contest rewards regional / code-mixed speech, real-world impact, telephony audio and a sharp 60-second demo. Rex touches all four.

## Hard constraints

| Constraint | Value |
|---|---|
| Deadline | 10 Nov 2026, 11:59 PM IST (public post must be live first) |
| Team | 2 people: **Johny** and **Shanky** |
| Required tech | ≥ 1 Gnani model (we use Prisma STT v2.5 + Timbre TTS v3.0) |
| Data | Synthetic only. No real phone numbers / IDs / recorded calls |
| Budget | Free tiers: Gemini, Mistral, Twilio trial, LiveKit Cloud free, 5,000 Gnani programme credits |
| Demo | ≤ 60 s video, one continuous story |

## Personas

- **Riya, final-year student** — Hinglish; wants meeting minutes and reminders.
- **Arjun, freelance developer** — wants bugs fixed and clients updated by voice.
- **Meena, salon owner (Tier-2 town)** — Kannada; wants Rex to call suppliers and book customers.

## System in 30 seconds

```
Mic / Phone / Meeting ─► LiveKit room ─► Gnani Prisma STT ─► Supervisor (Gemini)
                                                        │
             ┌──────────── routes to a specialist ──────┤
             ▼                                          ▼
 Comms · Calendar · Caller · Meeting · Coder · Screen/Browser
             │
             ▼
     MCP Gateway (permission tiers + audit) ─► Google, Slack, Notion, Maps, GitHub,
                                               Docker sandbox, Twilio, Vexa, Playwright
             │
             ▼
   Result ─► Gnani Timbre TTS ─► speaker / phone   +   timeline card on the dashboard
```

Full detail: [ARCHITECTURE.md](ARCHITECTURE.md).

## Glossary

| Term | Meaning |
|---|---|
| Supervisor | The top-level LLM agent that understands intent and routes work |
| Specialist / sub-agent | A focused agent with 3–10 tools (Comms, Calendar, Caller, Meeting, Coder, Screen) |
| MCP Gateway | Our process that connects to every MCP server, enforces permission tiers and logs actions |
| Tier R / W / A | Read / Write-reversible / Act-external permission tiers (see AUTHENTICATION_AND_SECURITY.md) |
| Fast ack | The instant spoken acknowledgement ("Theek hai, check kar raha hoon") before a long task |
| Timeline | The user-visible log of every action, with approve / undo |
| Project graph | The knowledge-graph memory that tracks project progress (`memory/project-graph.jsonl`) |

## Where we are

Run `python scripts/progress.py` → regenerates [PROGRESS.md](PROGRESS.md) from the project graph. Yesterday's state and today's plan live in [HANDOFF.md](HANDOFF.md).
