# Decision Log (append-only, newest first)

Chronological record of every decision and change of mind. Never edit old entries — add a new one that supersedes. Format: `YYYY-MM-DD · ID · who · decision · reason`.

## 2026-10-25

- **D-034** · Shanky · Briefing & Memory MCP server (`rex_mcp_servers.briefing`) synthesizing daily schedule, open tasks, and travel times into Hinglish/English morning briefings.
- **D-033** · Shanky · Coder Specialist executor (`rex_agent.brain.coder`) using Codestral to formulate code patches and self-heal test suites up to 3 retries in the sandbox.
- **D-032** · Shanky · Vexa MCP server (`rex_mcp_servers.vexa`) and Meeting Specialist executor (`rex_agent.brain.meeting`) coordinating bot recording, transcript retrieval, and minutes publishing.
- **D-031** · Shanky · Browser MCP server (`rex_mcp_servers.browser`) declaring `submit_form` as Tier A approval-gated tool · Web form submits alter external state and must not execute automatically.
- **D-030** · Shanky · Sandbox runner (`rex_mcp_servers.sandbox`) with workspace boundary enforcement and multi-language test execution · Secure execution preventing host escape.
- **D-029** · Shanky · Minutes MCP server (`rex_mcp_servers.minutes`) using `LLMClient` with structured JSON parsing and Notion/Slack formatting · Standardizes meeting pipeline extraction.
- **D-028** · Shanky · Gateway undo architecture for Tier W actions (`Gateway.undo()`, `undo_action` voice tool, and `ActionEvent.undo` spec) · Enables users to say "undo karo" or "cancel that" to revert reversible actions.
- **D-027** · Shanky · Notion MCP tools mapped from official `@notionhq/notion-mcp-server` (`API-post-search`, `API-retrieve-a-page`, `API-retrieve-a-database` R; `API-post-page`, `API-patch-page`, `API-patch-block-children` W; `API-delete-a-block`, `API-move-page` A; default_tier W) · Destructive actions require explicit confirmation, while notes and updates are reversible.
- **D-026** · Shanky · Slack MCP tools mapped from `@zencoderai/slack-mcp-server` (`slack_list_channels`, `slack_get_channel_history`, `slack_get_thread_replies`, `slack_get_users`, `slack_get_user_profile` R; `slack_add_reaction` W; `slack_post_message`, `slack_reply_to_thread` A; default_tier A) · Reaching other people via post/reply is Tier A; reading history is Tier R.

## 2026-10-24

- **D-024** · Shanky/Claude · Location tools use OpenStreetMap (Nominatim + OSRM, no key); Google Maps optional later · Works today without another account; estimates exclude live traffic.
- **D-025** · Shanky/Claude · Gateway tools are exposed to the LLM directly as LiveKit raw function tools (real JSON schemas); approvals are a two-step protocol (NeedsApproval → approve_action / dashboard RPC) · Simple, testable, works for voice and UI.
- **D-023** · Johny · English-only mode for now (STT en-IN, TTS en-IN, prompt always English); multilingual kept behind `REX_ENGLISH_ONLY=0` · Team request; stabilise the core loop first.
- **D-022** · Johny/Claude · Streaming STT language = `hi-IN` (handles Hinglish); greeting spoken with fixed text · Live test: Gnani streaming rejects `en-IN,hi-IN` with 1008; Gemini 400s on an LLM greeting with an empty conversation.
- **D-021** · Shanky/Claude · v1 supervisor = LiveKit `function_tool` (`delegate_task`) + our `Supervisor` class (registry, fast ack, background jobs), not LangGraph · Fewer moving parts, native streaming/barge-in with tool calls; LangGraph can be added inside a specialist later (supersedes D-006 for v1).
- **D-020** · Both · Add Groq (llama-3.3-70b-versatile) as the fast second choice for supervise/summarise · Very low latency on a free tier helps the voice loop.
- **D-019** · Both · Product name = **Rex** (was working name Saathi) · Short, one syllable, works as a wake word in every language.
- **D-018** · Both · Award focus = Mixed Vibes; backup Demo Day Drop · Code-mixed multilingual speech is the product's core; one award max per team.
- **D-017** · Both · Track progress with MCP memory graph (`memory/project-graph.jsonl`, in git) + claude-mem plugin (local) + `scripts/progress.py` → PROGRESS.md · Both humans and coding agents can query and update the same state.
- **D-011** · Johny · Support "most languages": Gnani for en-IN + 10 Indian languages, faster-whisper fallback for others · Requirement from team; Gnani stays primary.
- **D-009** · Johny/Shanky · Desktop companion (Tauri) + browser control (Playwright); browser control promoted to MVP · Team choice.
- **D-008** · Johny · Telephony = Twilio trial via LiveKit SIP · Team has Twilio; trial's verified-number limit matches contest's synthetic-data rule.
- **D-005** · Shanky · LLMs = Gemini + Mistral + Codestral via router, free tiers · Team preference for free models and right model per job.
- **D-002** · Both · Team = Johny + Shanky (contest max 2). Johny: audio/devices/pixels; Shanky: tools/data/models.
- **D-003** · Johny · LiveKit over Pipecat · Built-in SIP and outbound calling; Pipecat remains fallback.
- **D-001** · Both · MVP = 10 features in the demo story; scope freeze 31 Oct.

## Template

```
## YYYY-MM-DD
- **D-0xx** · <who> · <decision> · <reason> · (supersedes D-0yy)
```
