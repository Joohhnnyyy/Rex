# JARVIS (adewaskar/jarvis) — what it is and what Rex should take

Source: https://github.com/adewaskar/jarvis · cloned at `inspirations/jarvis/` (commit `1c4016a`, 5 Aug 2026; git-ignored, re-clone to refresh) · MIT · ~15k lines (TS + Node).

## 1. What it is

A browser voice assistant ("Hey Jarvis") with an Iron Man holographic UI (React 19 + Vite + Three.js/R3F + GLSL). It has two processes:

```
browser (face + voice)                     bridge (brain + hands)  bridge/server.mjs
  wake word, energy VAD, STT     ── ws ──►   Claude Agent SDK = headless Claude Code
  TTS sentence queue, HUD        ◄── 8787 ─   spawns every MCP server in ~/.claude.json
  camera, hand tracking                       decideTool() permission gate
```

- **Brain:** `@anthropic-ai/claude-agent-sdk` `query()` with a streaming-input async generator (one long session per socket, so history lives in the session). It uses the Claude Code login, so no API key is needed. Model `claude-opus-5`, effort medium/high, `maxTurns: 24`, `settingSources: []`.
- **Voice:** the browser `SpeechRecognition`/`speechSynthesis` by default. If the bridge has an ElevenLabs key it auto-upgrades to Scribe STT (`/stt`) and Flash v2.5 TTS (`/tts`). The browser picks the engine once at boot from `GET /health` → `{ok, tts, stt}`.
- **In-process MCP servers** (`createSdkMcpServer`), which push straight down the socket:
  - `jarvis`: `display` (model writes HUD HTML against a fixed `.hud-*` class allowlist) and `blade` (opens an image, article, video or page on a draggable card)
  - `jarvis_ui`: `ui_theme`, `ui_reactor`, `ui_orbit`, `ui_chrome`, `ui_effect`, `ui_screen`, `ui_reset` (the model restyles its own face)
  - `jarvis_chrome`: drives the user's real signed-in Chrome through the Claude-for-Chrome extension's native-host Unix socket, not Playwright
  - `jarvis_eyes`: `look` (one camera frame) and `watch` (a grid of time-stamped frames, forward or "what just happened")

## 2. Design ideas worth knowing (by file)

| Idea | Where | Gist |
|---|---|---|
| **Default-deny tool gate decided ahead of time** | `bridge/server.mjs` `decideTool()` | "Voice is a bad interface for a confirmation dialog." Built-in tools sit on read/write lists. MCP tools pass if the server is on an allowlist **or** the tool name starts with a read verb (`get\|list\|search\|…`). A veto regex (`send\|call\|post\|create\|delete\|…\|download`, unanchored) always needs `JARVIS_ALLOW_WRITES=1`. Exemptions are full `server__tool` keys. Both old and new SDK tool names are listed (Task/Agent, etc.). |
| **Badge only for tools that actually ran** | `server.mjs` `announceTool/settleTool` | Allowed tools are announced at `content_block_start`. Doubtful ones are held until `tool_result` (`is_error` → never announced). This stops the "working on it" line for work that never happens. |
| **Turn ids on every streamed message** | `server.mjs` `sendTurn({...msg, ask})` | The client drops tokens from an abandoned answer after barge-in. Interrupt waits for the turn to really finish (capped at 400 ms) before the next question goes in. |
| **Filler lines picked by tool** | `src/lib/fillers.ts` | One spoken ack as soon as the first tool fires, then silence. The phrase depends on `server`/`tool` regexes (calendar → "Checking your calendar."). A no-repeat picker keeps it from sounding canned. |
| **Segment ≠ turn** | `src/lib/voice.ts` `makeAssembler/holdFor` | Transcripts build up. The turn fires immediately on `.?!`, waits 1.6 s if the text ends on a function word (`and\|to\|the\|…`) or a comma, waits 250 ms otherwise, and never holds longer than 6 s. Short commands (`stop\|wait\|cancel\|no`) always go through. |
| **Echo filter on words, not strings** | `voice.ts` `isEcho` | A bag of *content* words (stop-words removed). It counts as echo when ≥ 60 % of them match what Jarvis just said. Override words are never treated as echo. There is a 350 ms self-guard after each sentence starts. |
| **Energy VAD with a guard** | `src/lib/vad.ts` | An adaptive noise floor (rises slowly, falls fast), trigger at 2.6× the floor, ×2.4 more while speaking, hysteresis 0.6. The recorder starts at onset so the first phoneme isn't lost, and blips under 110 ms are thrown away. |
| **Sentence-streamed TTS, one item primed ahead** | `src/lib/tts.ts` | Text is split at sentence boundaries as it streams. An explicit array queue with one pump means it can be cut cleanly. If a cloud voice fails once, everything after uses the fallback, so the answer doesn't stutter. |
| **Capability probe → graceful fallback** | `src/lib/capabilities.ts` | It works with zero keys and upgrades itself when a key appears. There's no flag to set. |
| **SSRF-guarded media/page proxy** | `bridge/net.mjs`, `page.mjs` | `/img`, `/media` (Range passthrough) and `/page?mode=reader\|live` fetch server-side. This fixes hotlink 403s and X-Frame-Options, and the user's IP never reaches model-chosen hosts. Hostnames are blocked before DNS, resolved IPs are checked per connection (to stop rebinding), every redirect hop is checked, content-type and byte caps apply, and `.svg` is never served. |
| **Origin-checked localhost socket** | `server.mjs` `originAllowed` | A WebSocket handshake isn't covered by the same-origin policy, so any tab could drive the agent. Only local dev ports are allowed, and a missing Origin is refused by default. |
| **Spoken-output persona prompt** | `server.mjs` `SYSTEM_PROMPT` | At most two sentences, median under 12 words. No markdown, URLs or sources read aloud. Numbers are written as spoken. No "let me check" narration. "Never read a blade aloud; say what it means." |
| **Loose zod schemas** | `bridge/ui.mjs` | Accepts `'0.5'`/`1`/`null`. `.catch(undefined)` plus clamping means a quoted number can't break a turn. |
| **Diagnostics built in** | `src/ui/Diagnostics.tsx`, `window.__voice` | **D** shows whether it's hearing you and producing sound. **T** runs an audio self-test. Dropped transcripts carry a reason (`drop('echo…')`). |

## 3. Mapping to Rex (browser + app only, D-038)

Rex already has: LiveKit + Silero VAD + the multilingual turn detector (`apps/agent/src/rex_agent/main.py`), per-specialist fast acks (`brain/acks.py`), an MCP gateway with R/W/A tiers and a two-step approval, and the web dashboard (`apps/web`). So JARVIS's VAD and wake-word code is **not** worth copying. LiveKit does that better. What *is* worth taking:

| Take | Into Rex | Cost | Why now |
|---|---|---|---|
| **Tool-aware filler** (fillers.ts) | `brain/acks.py`: choose the ack from the tool/server name too, not only the specialist; add a no-repeat picker | S | Latency feel in the demo; the logic is tiny |
| **Utterance assembler `holdFor`** | Only if the LiveKit turn detector cuts Hinglish mid-thought: a `CONTINUES` list for Hindi/English function words (`aur, ki, ko, ke, toh, matlab, and, to, the…`) | S–M | Measure first (T-12) |
| **Spoken-output rules** in the system prompt | `rex_agent/prompts.py`: ≤ 2 sentences, numbers as spoken, never speak URLs/IDs/JSON, no "let me check" narration, "show on dashboard, don't read it out" | S | Free quality win |
| **Model-authored panel with a class allowlist** (`display` tool) | The dashboard Timeline could render a `show_panel` tool's sanitised HTML (DOMPurify + fixed `.rex-*` classes) for results like calendar slots and ETA maps | M | Better demo visuals; optional |
| **Read-verb / effectful-verb veto as a safety net** | Gateway: if a tool isn't listed in a tier, default it by name (read verb → R, effectful verb → A) instead of failing open | S | Protects against new MCP tools |
| **Turn ids on events** | Timeline events after barge-in: tag with the turn/job id so the UI drops stale ones | S | Only if we see stale events |
| **SSRF guard** | Only if Rex's browser tool (T-38) proxies pages/images to the dashboard | M | Security, if applicable |
| **Diagnostics hotkey** | Dashboard: a mic level + "agent speaking" + last-dropped-reason panel | S | Saves debugging time in dry runs |
| **Three.js voice visual** (reactor, `src/` R3F + GLSL) | `apps/web`: an original Rex orb that reacts to listening / thinking / speaking and audio level | M | Kept for now (Johny, 6 Nov): demo wow-factor; own look, not the Iron Man reactor |

**Don't copy:** the Agent SDK brain (Rex's LLM is Gemini/Groq through our router, D-005/D-037), browser `SpeechRecognition` (we're on Gnani), ElevenLabs (the Gnani rule), driving Chrome through the private native-host socket (fragile).
