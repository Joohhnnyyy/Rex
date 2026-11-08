# Debugging Guide

## First 60 Seconds

1. **API Backend**: Verify FastAPI is healthy on port 8000:
   ```bash
   curl http://localhost:8000/healthz
   # Expected: {"status": "ok", "service": "rex-api"}
   ```
2. **LiveKit Agent Worker**: Ensure `uv run python -m rex_agent dev` is running without worker pool timeouts.
3. **Web Dashboard**: Confirm Next.js dashboard is reachable at `http://localhost:3000`.
4. **Google OAuth Token**: Verify token exists and is valid:
   ```bash
   uv run python -m rex_mcp_servers.calendar login
   ```
5. **Decisions & Context**: Check [DECISION_LOG.md](DECISION_LOG.md) to see if an architectural change affects the behavior.

---

## Tracing & Logs

Every log line in the agent worker uses `structlog` with context variables: `session_id`, `turn_id`, and `tool`.

```bash
# Monitor live agent worker logs
uv run --env-file .env python -m rex_agent dev
```

---

## Voice Loop Troubleshooting

| Symptom | Likely Cause | Solution |
|---|---|---|
| **No transcript** | Mismatched audio format to Gnani Prisma WS | Must be PCM16 LE mono, 16 kHz for WebRTC, 512-sample frames. |
| **Transcript arrives late** | VAD silence duration too long | Adjust `min_silence_duration` in agent config (350–450 ms). |
| **Agent speaks over user** | Barge-in cancellation not firing | Ensure Silero VAD turn detector is active and client audio echo cancellation is enabled. |
| **Wrong language reply** | Language lock not set / TTS voice map missing | Check detected `turn.lang` in worker logs; ensure matching Timbre voice is mapped. |
| **Numbers garbled ("chaar" vs 4)** | STT format mode set to verbatim | Configure Prisma with `format="transcribe"` for inverse text normalization. |
| **Robotic voice pauses** | REST TTS used instead of WebSocket streaming | Ensure Gnani Timbre WebSocket streaming client is active. |

---

## Tool & MCP Gateway Issues

| Symptom | Likely Cause | Solution |
|---|---|---|
| **Tool not discovered** | MCP server failed to start or crashed on init | Run the server directly (e.g. `uv run python -m rex_mcp_servers.calendar`) to verify JSON-RPC stdio. |
| **ToolTimeout** | Network or external API latency exceeded timeout | Raise `timeout_s` in `infra/mcp_servers.yaml`. |
| **401/403 from Google / Slack / Notion** | Expired or missing OAuth token | Re-authenticate via `uv run python -m rex_mcp_servers.calendar login` or refresh tokens in `.env`. |
| **Approval never resolves** | LiveKit RPC client disconnected | Confirm the web client is connected and listening to the `rex.decide` RPC method. |
| **Model picks wrong tool** | Overcrowded tool prompt | Check tool subset allow-list in `infra/mcp_servers.yaml`; rex supervisor limits active tools to ≤ 25. |

---

## LLM Router & Provider Failover

- **Rate Limits (429s)**: The router automatically cascades from Gemini 3.1 Flash Lite &rarr; Groq Llama 3.3 &rarr; Mistral Small. Check `llm_router` logs for `fallback_to` events.
- **Provider History Incompatibility**: If failover between Gemini and Groq/Mistral occurs, `PortableLLM` automatically strips Gemini-specific `thought_signature` fields to prevent HTTP 422 errors.
- **Malformed Tool Call Arguments**: Gateway Pydantic schemas validate all arguments before dispatch and return structured error messages back to the LLM for self-correction.

---

## Desktop Accessibility & Screen Vision

- **Accessibility Permissions**: macOS requires explicit permission under *System Settings &rarr; Privacy & Security &rarr; Accessibility* for the terminal or agent runner process.
- **Screen Recording Permissions**: WebRTC screen share vision requires *System Settings &rarr; Privacy & Security &rarr; Screen Recording* permission granted to the browser (Chrome / Safari).
