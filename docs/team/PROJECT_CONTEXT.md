# Project Context — Rex

One page that any human or AI agent should read before touching the repo.

## The one-liner

Rex is a multilingual, voice-first operator: you speak in Hinglish (or Tamil, Kannada, Bengali, English…), and it acts across your calendar, messages, notes, maps, code, desktop apps, and screen — asking before anything risky.

## Why it exists

- Indian users code-mix (Hinglish, Tanglish) and most assistants handle that badly. Gnani's Prisma STT is built for Indian languages and natural conversation.
- Students, freelancers, and knowledge workers juggle 5–8 apps. A single voice that can *act* (not just answer) saves real time.
- The contest rewards regional / code-mixed speech, real-world impact, robust engineering, and a sharp 60-second demo. Rex touches all four.

## Hard constraints

| Constraint | Value |
|---|---|
| Deadline | 10 Nov 2026, 11:59 PM IST (public post must be live first) |
| Team | 2 people: **Johny** and **Shanky** |
| Required tech | ≥ 1 Gnani model (we use Prisma STT v2.5 + Timbre TTS v3.0) |
| Data | Synthetic only. No real phone numbers / IDs / unauthorized personal data |
| Budget | Free tiers: Gemini, Mistral, Groq, LiveKit Cloud free, 5,000 Gnani programme credits |
| Demo | ≤ 60 s video, one continuous story |

## Personas

- **Riya, final-year student** — Hinglish; wants meeting minutes, travel driving times, and reminders.
- **Arjun, freelance developer** — wants bugs diagnosed, test suites verified in sandbox, and clients updated by voice.
- **Meena, salon owner (Tier-2 town)** — Kannada/Hinglish; wants Rex to check schedules, save notes, and update team members.

## System in 30 seconds

```
Mic / Screen Share ─► LiveKit Room ─► Gnani Prisma STT ─► Supervisor (Gemini Flash Lite)
                                                         │
             ┌──────────── routes to tool/specialist ────┤
             ▼                                           ▼
 Comms · Calendar · Desktop · Meeting · Coder · Browser · Files · Memory
             │
             ▼
     MCP Gateway (permission tiers R/W/A + audit + undo)
             │
             ├── Google Workspace (Calendar & Gmail)
             ├── Slack & Notion
             ├── macOS Accessibility Engine (WhatsApp, Notes, Chrome)
             ├── OpenStreetMap (Location & Travel)
             ├── Docker Sandbox (Test execution)
             ├── Local File Library (~/Documents/Rex)
             └── Vexa (Meeting Bot)
             │
             ▼
   Result ─► Gnani Timbre TTS ─► speaker / headphones   +   timeline card on dashboard
```

Full detail: [ARCHITECTURE.md](ARCHITECTURE.md).

## Glossary

| Term | Meaning |
|---|---|
| Supervisor | The top-level LLM agent that understands intent and routes work |
| Specialist | A focused agent context with scoped tools (Comms, Calendar, Desktop, Meeting, Coder, Files) |
| MCP Gateway | Our core engine that connects to every MCP server, enforces permission tiers and logs actions |
| Tier R / W / A | Read / Write-reversible / Act-external permission tiers (see AUTHENTICATION_AND_SECURITY.md) |
| Fast ack | The instant spoken acknowledgement ("On it" / "Ek minute") before executing tools |
| Timeline | The user-visible log of actions with approval cards and undo |
| Living Mascot | Interactive SVG mascot that reacts to voice volume, pointer gaze, and emotional state |
