# Decision Log (append-only, newest first)

Chronological record of every decision and change of mind. Never edit old entries — add a new one that supersedes. Format: `YYYY-MM-DD · ID · who · decision · reason`.

## 2026-11-08

- **D-049** · Johny · Per user direction after rejecting two logo rounds, use the existing red eye-only mascot as the logo with expression variants. Export actual dashboard-engine poses to keep character and identity consistent; primary expression is not selected yet.

- **D-048** · Johny · Enrich immersive Focus mode with CSS atmosphere/orbital light and a glass input dock; actual microphone/voice levels drive the glow, particles and activity signal. Preserve existing mascot/call behaviour and reduced-motion support; keep offline activity flat.

- **D-047** · Johny · Render immersive mode as a body-level modal portal instead of a fixed descendant of the animated dashboard; use separate responsive content rows, scroll/focus containment and restoration. Compact the overview and place Rex first through tablet widths. Fixes the overlay inheriting the dashboard’s transformed containing block.

- **D-046** · Johny · Per user expansion, include all 15 Bloub animation states and 16 expressions via its MIT framework-free core, adapted to React and Rex red. Keep capsule at rest, allow the requested body morphs, and expose manual/sequence previews in Lab; preserve reduced motion and live state mappings. Supersedes D-045’s restriction to a fixed body.

- **D-045** · Johny · User clarified: red buttons and a stationary red capsule with only two animated white eyes. Remove mouth, eyebrows, HUD and platform; retain ten live emotions and reduced-motion support. Supersedes D-043’s mascot styling and D-044’s blue navigation accent.

- **D-044** · Johny · Adapt the supplied dashboard video into a charcoal framed workspace, blue illuminated navigation rail, stacked left cards and a dominant Rex assistant panel. Preserve the original mascot, existing live controls and demo labels; use CSS transitions and existing reduced-motion support without new dependencies.

- **D-043** · Johny · Restore the original committed mascot and HUD after the user explicitly requested undoing the capsule change entirely. Supersedes D-041 and D-042.

- **D-042** · Johny · Replace the capsule with expressions sketched in black on a solid red square, per the updated user references. Remove the body shading, HUD and platform; keep ten live states, blinking and gaze. Supersedes D-041's visual treatment.

- **D-041** · Johny · Red capsule mascot with expressive white eyes, gaze and playful body reactions, per user reference. Keep the existing SVG and ten live emotion states so every dashboard view shares the character without new rendering dependencies.

## 2026-11-07

- **D-040** · Johny · **Ponytail cut (~930 lines).** Removed API auth/sessions/timeline/tools routes (dashboard uses LiveKit RPC + text streams), Postgres/Redis compose, call/approval/session schemas, sip_setup.py, seed_graph.py, and the 5 specialists with no executor (Rex keeps coder + meeting) · Nothing called them; the API is localhost-only, so the token endpoint stays unauthenticated. Add auth back before any public deploy.
- **D-039** · Johny · **Drop the call feature entirely.** No Caller agent, call room or call_tool (T-30, T-31, T-32, T-39 dropped); Rex is browser-based only · Not enough time before the 10 Nov deadline; browser, Gmail, Calendar and screen control are the demo. (supersedes D-038)

## 2026-11-03

- **D-038** · Johny · **Drop Twilio / phone calls.** Rex runs only as a browser (web app) and app agent. The Caller (demo step 2) talks to the "clinic" in a LiveKit room joined from a web link, labelled as a simulated call · Twilio trial cannot bridge calls into LiveKit (no Elastic SIP, no TwiML Bins, external TwiML won't ring); no time or budget to upgrade before the 10 Nov deadline. (supersedes D-008)

## 2026-10-29

- **D-037** · Johny/Claude · NVIDIA Nemotron 3 Ultra (`nvidia/nemotron-3-ultra-550b-a55b`) is the 3rd supervise backup after Gemini and Groq, thinking off · Measured on Rex's 24-tool turn: 3/3 correct tool calls, ~3.9 s vs Groq gpt-oss-120b 1.44 s — good enough to keep tests running when free tiers run out, too slow for the main voice model.

## 2026-10-26

- **D-035** · Both · Re-plan after Shanky's push: verify-and-harden first (26–28 Oct), phone call is the critical path, T-32/T-34/T-54 move to Shanky, T-50 cut, desktop app → browser screen-share, feature freeze 3 Nov, submit 9 Nov · Johny's track at 29 % vs Shanky's 85 %; most of Shanky's work not yet verified live.
- **D-036** · Both · Tasks are only `done` after a live run against the real service; code + offline tests = `in_progress` · Keeps PROGRESS.md honest.

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
