# Decisions (current state)

The **current** answer to each architectural question. When a decision changes, update it here and append the change to [DECISION_LOG.md](DECISION_LOG.md) (which keeps full chronological history).

| ID | Question | Decision | Status | Owner | Why (short) |
|---|---|---|---|---|---|
| D-001 | Product scope | Voice operator with 10 core features; demo story is the acceptance test | Accepted | Both | Scope focused on high-impact Indian workflows |
| D-002 | Team split | Johny: audio/devices/pixels; Shanky: tools/data/models | Accepted | Both | Clear ownership, clean modular tracks |
| D-003 | Voice framework | LiveKit Agents 1.x (+ `livekit-plugins-gnani`) | Accepted | Johny | Streaming WebRTC, barge-in cancellation, pre-warmed worker pool |
| D-004 | STT / TTS | Gnani Prisma v2.5 (WS) / Timbre v3.0 (WS) | Accepted | Johny | Contest requirement; streaming code-mixed Indian speech |
| D-005 | LLMs | Multi-model router: Gemini 3.1 Flash Lite (supervisor, vision), Groq Llama 3.3 (fast fallback), Mistral Small (summaries), Codestral (code) | Accepted | Shanky | Free tiers, PortableLLM state normalization |
| D-006 | Orchestration | ~~LangGraph~~ → LiveKit function tools + Supervisor class (see D-021) | Superseded | Shanky | Native streaming/barge-in with tool calls |
| D-007 | Tool protocol | MCP everywhere, behind our gateway | Accepted | Shanky | Uniform tools, config-driven skills, audit events |
| D-008 | Telephony | ~~Twilio trial via LiveKit SIP~~ → Dropped (see D-038/D-039) | Superseded | Johny | Focus on web voice + desktop accessibility + browser automation |
| D-009 | Screen & Desktop | Browser WebRTC screen share + native macOS accessibility tree automation | Accepted | Johny / Shanky | Direct element inspection and control without OCR lag |
| D-010 | Meeting capture | Vexa bot integration + structured minutes generation | Accepted | Shanky | Automated meeting capture and action item filing |
| D-011 | Language coverage | Gnani for en-IN + 10 Indian languages, faster-whisper fallback for others | Accepted | Johny | Regional Indian language coverage |
| D-013 | Backend | ~~Postgres + Redis~~ → Streamlined async FastAPI service with file/JSON persistence (see D-040) | Superseded | Shanky | Zero ops overhead; sub-millisecond local file I/O |
| D-014 | Frontend | Next.js 15 + LiveKit React components + SVG living mascot engine | Accepted | Johny | Fast, responsive, voice-coupled UI |
| D-016 | Safety | Permission tiers R/W/A in gateway; approvals for A; undo for W | Accepted | Shanky | Guarded actions, prompt injection isolation |
| D-019 | Product name | **Rex** | Accepted | Both | Short, punchy, easy wake word |
| D-026 | Slack MCP | @zencoderai/slack-mcp-server with posting as Tier A | Accepted | Shanky | Reaches others; reading history is Tier R |
| D-027 | Notion MCP | @notionhq/notion-mcp-server with default_tier W and deletes Tier A | Accepted | Shanky | Reversible notes are W, destructive actions are A |
| D-028 | Undo for Tier W | Gateway undo stack and compensating call execution + agent undo_action tool | Accepted | Shanky | User can say "undo karo" to revert actions |
| D-029 | Minutes MCP | rex_mcp_servers.minutes using structured JSON extraction and Notion/Slack formatting | Accepted | Shanky | Clean structured extraction for meetings |
| D-030 | Sandbox runner | rex_mcp_servers.sandbox with workspace boundary and test execution | Accepted | Shanky | Isolated code execution for Coder specialist |
| D-031 | Browser MCP | rex_mcp_servers.browser with submit_form as Tier A | Accepted | Shanky | Browser form submits require explicit approval |
| D-032 | Vexa MCP | rex_mcp_servers.vexa for meeting bot recording and transcript retrieval | Accepted | Shanky | Automated meeting capture |
| D-033 | Coder Specialist | rex_agent.brain.coder loop with Codestral and sandbox test verification | Accepted | Shanky | Autonomous self-healing code agent |
| D-038 | Telephony cut | Drop Twilio / external PSTN phone calls | Accepted | Johny | Web app and desktop application workflows are the core focus |
| D-039 | Scope freeze | Rex is browser and native app agent only | Accepted | Both | Prioritize Google Workspace, Slack, screen vision and desktop automation |
| D-040 | Backend cut | Ponytail cut: remove unused Postgres/Redis and redundant API routes | Accepted | Johny / Shanky | Clean, fast, focused API for token minting, connections, memory and files |
| D-046 | Mascot engine | All 15 Bloub animation states and 16 expressions adapted to React and Rex red | Accepted | Johny | Living character that couples to voice volume and pointer gaze |
| D-048 | Focus mode | Immersive focus mode with CSS atmosphere/orbital light and glass dock | Accepted | Johny | Dynamic glow coupled to mic and TTS levels |
| D-049 | Mascot identity | Mascot eye-only capsule identity with expressive emotional states | Accepted | Johny | Distinctive character design |
