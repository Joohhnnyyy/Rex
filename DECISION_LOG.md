# Decision Log (append-only, newest first)

Chronological record of every decision and change of mind. Never edit old entries — add a new one that supersedes. Format: `YYYY-MM-DD · ID · who · decision · reason`.

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
