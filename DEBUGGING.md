# Debugging Guide

## First 60 seconds

1. `make status` — are postgres, redis, api, agent, web, vexa up?
2. Dashboard → Timeline: did the action start? what status?
3. Langfuse: open the trace for the `turn_id` (link on each timeline card) — which span failed or was slow?
4. Logs: `docker compose logs -f agent | jq 'select(.session_id=="…")'`.
5. Search claude-mem (`search "<error text>"`) — has this happened before? Then check DECISION_LOG.md.

## Tracing IDs

Every log line carries `session_id`, `turn_id`, optional `job_id`, `tool`, `trace_id`. The timeline card shows them under "details".

## Voice problems

| Symptom | Likely cause | Fix |
|---|---|---|
| No transcript | Wrong audio format to Prisma WS | Must be PCM16 LE mono, 512-sample frames, real-time pace; check `sample_rate` matches the source (8 k phone / 16 k web) |
| Transcript arrives late | Gnani sends finals only; VAD end-of-speech too long | Lower `min_silence_duration` (try 350–450 ms); check `stt_ms` metric |
| Agent talks over user | Barge-in disabled or echo | Use interruptible WS TTS; enable echo cancellation in browser (`echoCancellation: true`) |
| Wrong language reply | Lang lock not set / TTS voice map missing | Check `turn.lang`, `voices.py` map |
| Numbers garbled ("chaar" vs 4) | `format=verbatim` | Use `format=transcribe` |
| Robotic pauses | TTS REST instead of WS | Use WebSocket/SSE streaming TTS |

## Telephony problems

| Symptom | Fix |
|---|---|
| `SipCallError` 403/21219 | Trial account calling an unverified number → verify it in Twilio |
| Call connects, silence | Codec/sample rate: phone leg is 8 kHz; set STT 8000; check LiveKit trunk media settings |
| Trial message plays first | Expected on Twilio trial; mention in demo or upgrade |
| Agent never joins room | Dispatch failed — check agent worker registration name matches dispatch |

## Tool / MCP problems

| Symptom | Fix |
|---|---|
| Tool not listed | Server crashed at start; run its command manually; stdout must be JSON-RPC only |
| `ToolTimeout` | Raise per-tool timeout in yaml or move to job queue |
| 401/403 from provider | Reconnect in Connections; check scopes |
| Approval never resolves | SSE disconnected; check `approval:{id}` key in Redis |
| LLM picks wrong specialist | Add eval case; tighten specialist descriptions; check router model fallback didn't kick in |

## LLM problems

- 429s → router should fall back; check `llm_router` logs for `fallback_to`.
- JSON parse errors in minutes → use structured output / schema mode; retry once with error message.
- Hallucinated tool args → validate with Pydantic before gateway call; return the validation error to the model.

## Coder sandbox

`docker logs rex-sbx-<job_id>`; containers are kept 15 min after failure for inspection (`make sbx-shell JOB=<id>`).

## Desktop companion

Tauri dev tools: `pnpm --filter desktop tauri dev`, right-click → Inspect. macOS screen capture needs *System Settings → Privacy → Screen Recording* permission for the app (and the terminal in dev).

## Reproducing a bug

Save the turn audio (`DEBUG_SAVE_AUDIO=1`, synthetic sessions only) → replay with `python scripts/replay_turn.py <file.wav>` → add it to `evals/regressions/`.

## Logging a fix

Add a line to DECISION_LOG.md if the fix changed a design choice; add an observation `note: fixed …` to the task in the project graph.
