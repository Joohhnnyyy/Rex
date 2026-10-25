# Rex — Submission Document

**Gnani AI — Great Indian AI Internship Challenge (October–November 2026)**  
**Team:** Johny & Shanky  
**Award Focus:** Mixed Vibes (multilingual, natural Hinglish speech AI) · Backup: Demo Day Drop  

---

## 1. Executive Summary

**Rex** is a voice-first multimodal AI assistant built specifically for Indian professional workflows and everyday tasks. Unlike text-based chat assistants or rigid IVR bots, Rex:
1. **Listens and Speaks in Natural Hinglish & Indian Languages**: Powered by **Gnani Prisma STT** and **Gnani Timbre TTS** over sub-50ms WebRTC streams via LiveKit, supporting instant barge-in interruption.
2. **Multi-Model Intelligence**: Intelligently routes tasks through a fault-tolerant multi-model LLM router (**Gemini Flash**, **Mistral Small**, **Codestral**, and **Groq Llama**), picking the optimal model per task kind with zero-downtime automatic fallback.
3. **Acts Safely Through MCP**: Routes all actions through a standardized **Model Context Protocol (MCP) Gateway** with strict three-tier permissions (**Tier R** Read, **Tier W** Reversible Write with single-phrase Undo, and **Tier A** Act/Destructive requiring explicit human confirmation).
4. **End-to-End Autonomous Specialists**:
   - **Calendar**: Google Calendar meeting booking, free slot search, and calendar management in Asia/Kolkata timezone.
   - **Comms**: Team messaging and channel search across Slack and Notion workspace documentation.
   - **Location**: Real driving times, ETAs, and place lookups across Indian cities via OpenStreetMap.
   - **Meeting**: Vexa bot meeting capture, audio transcription, and structured JSON minutes generation filed directly to Notion and Slack.
   - **Coder**: Automated bug diagnosis, code patching, and test suite execution within an isolated Docker sandbox.
   - **Browser**: Playwright web automation with human approval gates on form submissions.
   - **Briefing & Memory**: Daily morning briefs synthesized from calendars, unread messages, and long-term user preferences.

---

## 2. System Architecture

```
[ User Microphone ]
       │  (WebRTC Opus audio)
       ▼
[ LiveKit Cloud Worker ] ──> [ Gnani Prisma STT (WebSocket, hi-IN streaming) ]
       │                                     │
       ▼                                     ▼
[ Language Router & Supervisor ] <── [ Live Transcript ]
       │
       ├──> Multi-Model LLM Router (Gemini Flash / Groq / Mistral / Codestral)
       │
       ├──> [ MCP Gateway (Tiers R / W / A) ]
       │         │
       │         ├── Calendar Server (Google Calendar, IST)
       │         ├── Comms (Slack & Notion)
       │         ├── Location Server (OSM Nominatim & OSRM)
       │         ├── Meeting Server (Vexa bot + Minutes generator)
       │         ├── Sandbox Server (Docker runner, pytest)
       │         ├── Browser Server (Playwright with Tier A approval)
       │         └── Briefing Server (Daily digest & memories)
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
| **Supervisor & Small Talk** | Gemini 2.5 / 3.1 Flash & Groq Llama 3.3 | Fast acknowledgement (< 500 ms) and general conversation |
| **Minutes & Summaries** | Mistral Small | Strict JSON schema extraction for meeting decisions and action items |
| **Code Specialist** | Codestral | Autonomous code diagnosis, patching, and iterative test verification |
| **Maps & Routing** | OpenStreetMap (Nominatim + OSRM) | Geocoding and driving duration estimates across India |
| **Productivity Tools** | Google Calendar, Slack, Notion, Vexa | MCP runtime tools for calendar, communications, and meeting bots |

---

## 4. Safety & Trust Architecture

Rex implements safety by architecture rather than just prompt engineering:
- **Permission Tiers**:
  - **Tier R (Read)**: Runs immediately; read-only operations (e.g. calendar search, channel history).
  - **Tier W (Write, Reversible)**: Runs and announces outcome; registers a compensating action in the Gateway undo stack. Saying *"Rex, undo karo"* or *"Cancel that"* immediately executes the compensating call.
  - **Tier A (Act, Irreversible / Reaches Others)**: Suspends execution, generates a unique `action_id`, and asks the user for explicit confirmation. Only executes after the user says *"Haan"* / *"Yes"* or approves on the dashboard.
- **Prompt Injection Isolation**:
  - All external tool outputs, emails, and web pages are wrapped in `<untrusted_data>` boundaries.
  - System instructions treat untrusted data strictly as inert information, never as executable commands.

---

## 5. Team Contributions Breakdown

### Johny
- Realtime voice loop implementation with LiveKit agent worker.
- Gnani Prisma STT and Gnani Timbre TTS WebSocket adapters.
- VAD tuning, latency logging per spoken turn, and barge-in speech interruption.
- Next.js web dashboard (`apps/web`) with room connection, push-to-talk, live transcript, and approval cards.
- Telephony & outbound SIP call integration.

### Shanky
- MCP Gateway core architecture, dynamic namespacing, and audit event streams (`packages/mcp_gateway`).
- Three-tier permission engine (R/W/A) and approval protocol.
- Google Calendar MCP server with IST handling and reversible event creation (`rex_mcp_servers.calendar`).
- Slack & Notion MCP server integration and tier verification.
- Location tools (`rex_mcp_servers.location`) using OpenStreetMap.
- Meeting Minutes generator with structured Pydantic schema validation (`rex_mcp_servers.minutes`).
- Docker sandbox test runner (`rex_mcp_servers.sandbox`) and Coder specialist (`rex_agent.brain.coder`).
- Browser MCP server with Tier A submit gating (`rex_mcp_servers.browser`).
- Briefing & Memory MCP server (`rex_mcp_servers.briefing`).
- Tier W undo architecture and prompt injection guards.
- FastAPI backend (`apps/api`) with magic link auth, JWT tokens, sessions, tools registry, and timeline endpoints.
- Comprehensive 70-case evaluation suite and test harness (`evals/routing.yaml`, `scripts/run_evals.py`).
