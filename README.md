# Rex — a multilingual voice operator

> Speak once, in your own language. Rex books it, calls them, writes the code and posts the minutes.

Rex is a voice-first AI agent built for the **Gnani AI — Great Indian AI Internship Challenge** (submissions close **10 Nov 2026, 11:59 PM IST**). It listens with **Gnani Prisma STT**, speaks with **Gnani Timbre TTS**, plans with a multi-model LLM router (Gemini, Mistral, Codestral), and acts through **MCP** tools: Google Calendar, Gmail, Slack, Notion, Google Maps, GitHub, a code sandbox, Twilio phone calls, a meeting bot, the browser and your screen.

| | |
|---|---|
| Team | **Johny** (voice, telephony, desktop, frontend) · **Shanky** (orchestrator, MCP tools, backend, coder) |
| Award focus | Mixed Vibes (code-mixed speech) · backup: Demo Day Drop |
| Status | See [PROGRESS.md](PROGRESS.md) (generated from the project graph) |

## What it does (MVP)

1. Full-duplex voice in Hinglish, English and 10 Indian languages, with barge-in.
2. Calendar: find free slots, create and move events, send invites.
3. Caller: phones a clinic or shop over Twilio, books a slot, reports back.
4. Meeting: a bot joins Meet/Zoom, records, and files minutes + action items to Notion and Slack.
5. Comms: read, summarise and post Slack messages.
6. Notes: create and search Notion pages.
7. Location: place search, ETA, share a pin.
8. Coder: reads a repo, fixes a bug in a Docker sandbox, runs tests, opens a PR.
9. Screen + browser: "What's this error?" reads the screen; browser control fills forms with approval.
10. Safety: approval gate for risky actions, live action timeline, undo.

## Repository layout

```
rex/
├── apps/
│   ├── agent/          # Python: LiveKit agent worker (voice loop, supervisor, sub-agents)
│   ├── api/            # Python: FastAPI backend (auth, tasks, timeline, approvals, webhooks)
│   ├── web/            # TypeScript: Next.js dashboard (live transcript, timeline, approvals)
│   └── desktop/        # TypeScript/Rust: Tauri companion (push-to-talk, screen capture, tray)
├── packages/
│   ├── mcp_gateway/    # Python: MCP client hub, permission tiers, audit log
│   ├── mcp_servers/    # Python: our own MCP servers (call, screen, approval, skills, minutes)
│   ├── llm_router/     # Python: model routing (Gemini / Mistral / Codestral / OpenRouter)
│   └── shared/         # Pydantic schemas + generated TS types
├── infra/              # docker-compose, LiveKit config, Vexa, Caddy
├── scripts/            # progress.py and dev helpers
├── memory/     # project knowledge graph (progress tracking)
└── *.md                # the documentation set (start with PROJECT_CONTEXT.md)
```

## Quick start (target state)

```bash
git clone <repo> rex && cd rex
cp .env.example .env            # fill in keys — see INTEGRATIONS.md
cp mcp.json.example .mcp.json   # project-graph MCP for Claude Code (see CLAUDE.md)
docker compose -f infra/docker-compose.yml up -d   # postgres, redis, livekit, vexa
uv sync                         # python workspace
pnpm install                    # web + desktop
make dev                        # agent worker + api + web
```

Open `http://localhost:3000`, press and hold the mic, and say: *"Kal 4 baje Shanky ke saath meeting rakho."*

## Documentation map

| Read this | When |
|---|---|
| [PROJECT_CONTEXT.md](PROJECT_CONTEXT.md) | First. One-page context for humans and agents |
| [PRD.md](PRD.md) | What we are building and why |
| [ARCHITECTURE.md](ARCHITECTURE.md) | How the system fits together |
| [IMPLEMENTATION_ROADMAP.md](IMPLEMENTATION_ROADMAP.md) | Phase-wise plan and who owns what |
| [FEATURE_DEVELOPMENT.md](FEATURE_DEVELOPMENT.md) | How to build and ship a feature |
| [BACKEND_CONTEXT.md](BACKEND_CONTEXT.md) · [API.md](API.md) · [DATABASE.md](DATABASE.md) | Backend work |
| [MCP_CONNECTION.md](MCP_CONNECTION.md) · [INTEGRATIONS.md](INTEGRATIONS.md) | Adding tools and third-party services |
| [AUTHENTICATION_AND_SECURITY.md](AUTHENTICATION_AND_SECURITY.md) | Auth, secrets, permission tiers |
| [DESIGN.md](DESIGN.md) | UI and voice design |
| [DEBUGGING.md](DEBUGGING.md) | When something breaks |
| [DECISIONS.md](DECISIONS.md) · [DECISION_LOG.md](DECISION_LOG.md) | Why things are the way they are |
| [HANDOFF.md](HANDOFF.md) | End-of-day handoff between Johny and Shanky |
| [AGENTS.md](AGENTS.md) · [CLAUDE.md](CLAUDE.md) | Instructions for AI coding agents |

## Contest rules we must respect

- At least one Gnani model in every demo path (we use Prisma STT and Timbre TTS everywhere).
- **Synthetic data only**: no real phone numbers, Aadhaar, PAN or recorded calls. Calls go to the team's own verified numbers.
- Demo video posted publicly on LinkedIn or X with `#GnaniAI` and `#GreatIndianAIInternshipChallenge`, tagging Gnani AI, **before** submission.
- No misleading demos: anything mocked is labelled as mocked.

## License

MIT (code). Third-party components keep their own licenses — see [INTEGRATIONS.md](INTEGRATIONS.md).
