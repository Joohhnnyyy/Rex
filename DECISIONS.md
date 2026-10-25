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
| D-026 | Slack MCP | @zencoderai/slack-mcp-server with posting as Tier A | Accepted | Shanky | Reaches others; reading history is Tier R |
| D-027 | Notion MCP | @notionhq/notion-mcp-server with default_tier W and deletes Tier A | Accepted | Shanky | Reversible notes are W, destructive actions are A |
| D-028 | Undo for Tier W | Gateway undo stack and compensating call execution + agent undo_action tool | Accepted | Shanky | User can say "undo karo" to revert actions |
| D-029 | Minutes MCP | rex_mcp_servers.minutes using LLMClient with Notion blocks and Slack mrkdwn | Accepted | Shanky | Clean structured extraction for meetings |
| D-030 | Sandbox runner | rex_mcp_servers.sandbox with workspace boundary and test execution | Accepted | Shanky | Isolated code execution for Coder specialist |
| D-031 | Browser MCP | rex_mcp_servers.browser with submit_form as Tier A | Accepted | Shanky | Browser form submits require explicit approval |
| D-032 | Vexa MCP | rex_mcp_servers.vexa for meeting bot recording and transcript retrieval | Accepted | Shanky | Automated meeting capture |
| D-033 | Coder Specialist | rex_agent.brain.coder loop with Codestral and sandbox test verification | Accepted | Shanky | Autonomous self-healing code agent |
| D-034 | Briefing MCP | rex_mcp_servers.briefing for personalized morning brief in Hinglish | Accepted | Shanky | High-value daily synthesized routine |

## Decision template

```
### D-0xx — <question>
Context: <what forced the decision>
Options: A) … B) … C) …
Decision: <chosen option>
Consequences: <what gets easier/harder>
Revisit if: <trigger>
```
