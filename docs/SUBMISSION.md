# Rex — Submission Document

**Gnani AI — Great Indian AI Internship Challenge (October–November 2026)**  
**Team:** Johny & Shanky  
**Award Focus:** Mixed Vibes (multilingual, natural Hinglish speech AI) · Backup: Demo Day Drop  

---

## 1. Executive Summary

**Rex** is a voice-first multimodal AI assistant built specifically for Indian professional workflows and everyday tasks. Unlike text-based chat assistants or rigid IVR bots, Rex:

1. **Listens and Speaks in Natural Hinglish & Indian Languages**: Powered by **Gnani Prisma STT** and **Gnani Timbre TTS** over sub-50ms WebRTC streams via LiveKit, supporting instant barge-in interruption.
2. **Multi-Model Intelligence & State Normalization**: Intelligently routes tasks through a fault-tolerant multi-model LLM router (**Gemini 3.1 Flash Lite**, **Groq Llama 3.3 70B**, **Mistral Small**, and **Codestral**), picking the optimal model per task kind with zero-downtime automatic fallback and cross-provider history normalization (`PortableLLM`).
3. **Acts Safely Through MCP**: Routes all actions through a standardized **Model Context Protocol (MCP) Gateway** with strict three-tier permissions (**Tier R** Read, **Tier W** Reversible Write with single-phrase Undo, and **Tier A** Act/Destructive requiring explicit human confirmation).
4. **End-to-End Autonomous Workflows**:
   - **Calendar & Gmail**: Google Calendar meeting booking, free slot search, and calendar management in Asia/Kolkata timezone with reversible event creation; Gmail search and draft queuing.
   - **Comms & Collaboration**: Team messaging, channel search, and knowledge retrieval across Slack and Notion.
   - **Location & Travel**: Real driving times, ETAs, and place lookups across Indian cities via OpenStreetMap.
   - **Meeting Capture & Minutes**: Vexa bot meeting integration, audio transcription, and structured JSON minutes generation filed directly to Notion and Slack.
   - **Code Sandbox**: Automated bug diagnosis, code patching, and test suite execution within an isolated Docker sandbox.
   - **Native Desktop & Vision**: Direct macOS accessibility tree inspection and control (WhatsApp, Notes, Chrome) paired with real-time WebRTC screen share vision.
   - **File Library & Memory**: Autonomous document organization in `~/Documents/Rex`, persistent cross-session memory, and proactive background interest discoveries.

---

## 2. System Architecture

```text
[ User Microphone ]
       │  (WebRTC Opus audio)
       ▼
[ LiveKit Cloud Worker ] ──> [ Gnani Prisma STT (WebSocket, hi-IN streaming) ]
       │                                     │
       ▼                                     ▼
[ Language Router & Supervisor ] <── [ Live Transcript ]
       │
       ├──> Multi-Model LLM Router (Gemini Flash / Groq / Mistral / Codestral)
       │    └── PortableLLM History Normalizer
       │
       ├──> [ MCP Gateway (Tiers R / W / A) ]
       │         │
       │         ├── Calendar Server (Google Calendar, IST)
       │         ├── Gmail Server (Query & Draft Dispatch)
       │         ├── Comms (Slack & Notion)
       │         ├── Location Server (OSM Nominatim & OSRM)
       │         ├── Meeting Server (Vexa bot + Minutes generator)
       │         ├── Sandbox Server (Docker runner, pytest)
       │         ├── Browser Server (Playwright automation)
       │         ├── Desktop Server (macOS Accessibility Engine)
       │         ├── Files Server (~/Documents/Rex Library)
       │         └── Memory & Discoveries Server (Cross-session facts)
       │
       ▼
[ Gnani Timbre TTS (WebSocket, interruptible) ] ──> [ User Speaker / Headphones ]
```

---

## 3. Models and APIs Used

| Component | Provider / Technology | Purpose |
|---|---|---|
| **STT** | Gnani Prisma (WebSocket) | Low-latency streaming speech-to-text with code-mixed Hinglish support |
| **TTS** | Gnani Timbre (WebSocket) | Expressive natural voice synthesis with fast barge-in cancellation |
| **Voice Transport** | LiveKit Cloud / Agents 1.x | WebRTC audio channels, turn detection, and agent room dispatch |
| **Supervisor & Multimodal** | Gemini 3.1 Flash Lite & Groq Llama 3.3 | Sub-second voice conversation and screen vision frame evaluation |
| **Minutes & Summaries** | Mistral Small | Strict JSON schema extraction for meeting decisions and action items |
| **Code Specialist** | Codestral | Autonomous code diagnosis, patching, and iterative test verification |
| **Maps & Routing** | OpenStreetMap (Nominatim + OSRM) | Geocoding and driving duration estimates across India |
| **Productivity Tools** | Google Workspace, Slack, Notion, Vexa | MCP runtime tools for calendar, email, communications, and meeting bots |

---

## 4. Safety & Trust Architecture

Rex implements safety by architecture rather than just prompt engineering:
- **Permission Tiers**:
  - **Tier R (Read)**: Runs immediately; read-only operations (e.g. calendar search, email search, channel history).
  - **Tier W (Write, Reversible)**: Runs and announces outcome; registers a compensating action in the Gateway undo stack. Saying *"Rex, undo karo"* or *"Cancel that"* immediately executes the compensating call.
  - **Tier A (Act, Irreversible / Reaches Others)**: Suspends execution, generates a unique `action_id`, and asks the user for explicit confirmation. Only executes after the user says *"Haan"* / *"Yes"* or approves on the dashboard via LiveKit RPC (`rex.decide`).
- **Prompt Injection Isolation**:
  - All external tool outputs, emails, and web pages are wrapped in `<untrusted_data>` boundaries.
  - System instructions treat untrusted data strictly as inert information, never as executable commands.

---

## 5. Team Contributions Breakdown

### Johny
- Realtime voice loop implementation with LiveKit agent worker.
- Gnani Prisma STT and Gnani Timbre TTS WebSocket streaming adapters.
- VAD tuning, latency optimization, and sub-50ms barge-in speech interruption.
- Next.js 15 web dashboard (`apps/web`) with room connection, push-to-talk, live transcript, and approval cards.
- Reactive SVG Mascot state machine (`lib/bloub`, `lib/mascot.ts`) with pointer gaze tracking, blink intervals, and audio energy coupling.
- Native macOS desktop accessibility engine (`apps/agent/src/rex_agent/desktop.py`) with UI element inspection, click/type/focus automation, and verification.
- Live WebRTC screen share vision analysis (`apps/agent/src/rex_agent/screen.py`).

### Shanky
- MCP Gateway core architecture, dynamic namespacing, and audit event streams (`packages/mcp_gateway`).
- Three-tier permission engine (Tier R / Tier W / Tier A) and runtime approval protocol.
- Tier W compensating action undo stack (*"Rex, undo that"* / *"Cancel karo"*).
- Multi-Model LLM Router (`packages/llm_router`) with `PortableLLM` cross-provider state normalizer (handling Gemini `thought_signature` vs Groq/Mistral).
- Google Calendar MCP server with IST handling and reversible event creation (`rex_mcp_servers.calendar`).
- Gmail MCP server with search and Tier A send gating (`rex_mcp_servers.gmail`).
- Local file library and structured note management (`rex_mcp_servers.files`).
- Cross-session memory and background discovery engine (`rex_mcp_servers.memory`, `rex_mcp_servers.discoveries`).
- Meeting Minutes generator with structured Pydantic schema validation (`rex_mcp_servers.minutes`).
- Docker sandbox test runner (`rex_mcp_servers.sandbox`) and Coder specialist (`rex_agent.brain.coder`).
- Browser automation MCP server with Tier A submit gating (`rex_mcp_servers.browser`).
- FastAPI backend service (`apps/api`) with LiveKit token minting, connection management, memory, and files endpoints.
- Comprehensive evaluation suite and test harness (`evals/routing.yaml`, `scripts/run_evals.py`).
