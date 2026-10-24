# Integrations

Every external service, how we use it, how to set it up, and its limits. "Verify" = confirm during setup and record in DECISION_LOG.md.

## Summary

| Service | Purpose | Owner | Auth | Free tier / limit to watch |
|---|---|---|---|---|
| Gnani Prisma STT v2.5 | Speech → text (stream, REST ≤ 60 s, batch) | Johny | `GNANI_API_KEY` | 5,000 programme credits |
| Gnani Timbre TTS v3.0 | Text → speech (WS, SSE, REST) | Johny | same | same — cache fixed phrases |
| LiveKit Cloud + Agents 1.x | Rooms, agent dispatch, SIP | Johny | API key/secret | free tier minutes |
| Twilio | PSTN number, SIP trunk | Johny | Account SID (AC…) + API key SID (SK…) / secret | **trial: verified numbers only**, trial message prefix |
| Gemini API | Supervisor, vision | Shanky | `GEMINI_API_KEY` | RPM/RPD caps → router fallback |
| Mistral API (Small, Codestral) | Summaries, minutes, code | Shanky | `MISTRAL_API_KEY` | free plan rate limits |
| Groq | Fast fallback LLM (Llama 3.3 70B) | Shanky | `GROQ_API_KEY` | free tier RPM/TPD caps |
| OpenRouter | Emergency free models | Shanky | key | low RPM |
| Google Workspace (Calendar, Gmail) | Scheduling, mail | Shanky | OAuth (test users) | app unverified → add both of us as test users |
| Google Maps Platform | Places, directions, ETA | Shanky | API key | monthly free credit; restrict key |
| Slack | Comms | Shanky | bot token | hackathon workspace |
| Notion | Notes, minutes | Shanky | integration token | share pages with integration |
| GitHub | Repo, PRs | Shanky | fine-grained PAT | demo repo only |
| Vexa | Meeting bot | Shanky | API key or self-host | transcripts polled; GPU needed if self-host transcription (we use Gnani batch instead) |
| Playwright MCP | Browser control | Shanky | local | — |
| faster-whisper | Fallback STT | Johny | local | CPU OK for short turns |
| Fallback TTS (D-012) | Non-Gnani languages | Johny | TBD | — |
| Langfuse | Tracing | Shanky | keys | cloud free tier or self-host |
| claude-mem | Dev memory (per machine) | both | local | Apache-2.0, Node ≥ 20 |
| MCP memory server | Project progress graph | both | local | — |

## Gnani

- Pipecat: `pip install pipecat-gnani` → `GnaniSTTService` (WS), `GnaniTTSService` (WS, interruptible), HTTP/SSE variants.
- LiveKit: `uv add "livekit-agents[gnani]~=1.8"` → `gnani.STT(...)`; options `sample_rate` (8000/16000/44100/48000), `use_streaming`, `format="transcribe"` (inverse text normalisation), `preferred_language`.
- Streaming languages: bn, en, gu, hi, kn, ml, mr, pa, ta, te (`-IN`). Batch adds `en-IN,hi-IN` bilingual.
- Audio for WS STT: raw PCM16 LE mono, 512-sample frames, real-time cadence. Finals only (no interim).
- TTS voice determines language (default voice "Pranav"); keep a `lang → voice` map in `apps/agent/voice/voices.py` from the voices catalogue.
- Docs: https://docs.gnani.ai/llms.txt

## LiveKit + Twilio (telephony)

1. Twilio: buy/assign trial number; **verify Johny's and Shanky's phones** (trial can only call verified numbers).
2. Twilio Elastic SIP trunk → termination URI + credentials.
3. LiveKit: create outbound trunk with Twilio address, number, credentials → `LIVEKIT_SIP_TRUNK_ID`.
4. Caller agent: dispatch to new room with metadata `{to, goal, constraints, lang}` → `CreateSIPParticipant(sip_trunk_id, sip_call_to, wait_until_answered=True)`.
5. End with EndCallTool / `delete_room`. Status webhooks → `/v1/webhooks/twilio/status`.
- Phone audio is 8 kHz → set STT `sample_rate=8000` on the caller session.
- Ref: https://docs.livekit.io/telephony/making-calls/outbound-calls

## Google

- One GCP project "rex-dev"; OAuth consent screen *External – Testing*, test users = our two accounts.
- Enable Calendar API, Gmail API (stretch), Places API (New), Routes API.
- Restrict the Maps key to those APIs + server IP.
- Workspace MCP: Google's open-source Workspace MCP server (verify exact package at setup).

## Slack

Create app "Rex (hackathon)" in a dedicated workspace; bot scopes in AUTHENTICATION_AND_SECURITY.md; install; invite bot to `#standup`, `#general`. MCP: `zencoderai/slack-mcp-server`.

## Notion

Internal integration "Rex"; share a "Rex" parent page with it; minutes template page id in `NOTION_MINUTES_TEMPLATE_ID`. MCP: Notion's official server (verify).

## Vexa

Hosted token for the hackathon (faster) unless D-010 says self-host. Bot joins via `POST /bots`; MCP at `/mcp`; fetch audio after end → Gnani batch STT.

## Data rules for all integrations

Synthetic contacts only (`Dr. Mehta Dental Clinic → Shanky's verified phone`). Demo Slack/Notion/Calendar hold fake data. No real customer data ever.
