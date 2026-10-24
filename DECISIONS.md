# Decisions (current state)

The **current** answer to each architectural question. When a decision changes, update it here and append the change to [DECISION_LOG.md](DECISION_LOG.md) (which keeps history). Each decision is also an entity `D-xxx` in the project graph.

| ID | Question | Decision | Status | Owner | Why (short) |
|---|---|---|---|---|---|
| D-001 | Product scope | Voice operator with 10 MVP features; demo story is the acceptance test | Accepted | Both | 17 days, 2 people |
| D-002 | Team split | Johny: audio/devices/pixels; Shanky: tools/data/models | Accepted | Both | Clear ownership, few merge conflicts |
| D-003 | Voice framework | LiveKit Agents 1.x (+ `livekit-plugins-gnani`) | Accepted | Johny | SIP/telephony built in; web + desktop + phone in one room model. Pipecat (`pipecat-gnani`) is the fallback |
| D-004 | STT / TTS | Gnani Prisma v2.5 (WS) / Timbre v3.0 (WS) | Accepted | Johny | Contest requirement; Indian languages; barge-in |
| D-005 | LLMs | Multi-model router: Gemini (supervisor, vision), Groq Llama 3.3 (fast fallback), Mistral Small (summaries), Codestral (code), OpenRouter free (fallback) | Accepted | Shanky | Free tiers; best model per job |
| D-006 | Orchestration | ~~LangGraph~~ → LiveKit function tools + Supervisor class (see D-021) | Superseded | Shanky | Explicit state, interrupts for approvals |
| D-007 | Tool protocol | MCP everywhere, behind our gateway | Accepted | Shanky | Uniform tools, config-driven skills |
| D-008 | Telephony | Twilio trial number via LiveKit SIP | Accepted | Johny | Team choice; verified-number limit fits synthetic-data rule |
| D-009 | Screen access | Tauri desktop companion + Playwright browser control | Accepted | Johny / Shanky | More capable than browser screen-share |
| D-010 | Meeting capture | Vexa (hosted token first), audio re-transcribed with Gnani batch STT | Proposed — decide by 30 Oct | Shanky | Indian-language minutes |
| D-011 | Language coverage | Gnani for en + 10 Indian langs; faster-whisper fallback STT for others | Accepted | Johny | "Most languages" requirement |
| D-012 | Fallback TTS | Piper (local) vs. an API voice | Open — decide by 1 Nov | Johny | Quality vs. cost |
| D-013 | Backend | FastAPI + Postgres/pgvector + Redis (arq) | Accepted | Shanky | Simple, async, free |
| D-014 | Frontend | Next.js + LiveKit React components | Accepted | Johny | Fast to build |
| D-015 | Hosting | One VM in Mumbai region + LiveKit Cloud | Accepted | Shanky | Latency to Indian users |
| D-016 | Safety | Permission tiers R/W/A in gateway; approvals for A; undo for W | Accepted | Shanky | Trust + judges |
| D-017 | Progress tracking | MCP memory knowledge graph in git + claude-mem per machine + generated PROGRESS.md | Accepted | Both | Shared, queryable progress for humans and agents |
| D-019 | Product name | **Rex** | Accepted | Both | Short, punchy, easy wake word |
| D-018 | Award focus | Mixed Vibes first, Demo Day Drop backup | Accepted | Both | Code-mixed speech is the core |

## Decision template

```
### D-0xx — <question>
Context: <what forced the decision>
Options: A) … B) … C) …
Decision: <chosen option>
Consequences: <what gets easier/harder>
Revisit if: <trigger>
```
