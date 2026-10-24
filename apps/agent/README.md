# rex_agent — the voice loop (T-10 / T-11 / T-12)

Gnani **Prisma STT** (streaming, `hi-IN` — handles Hinglish, `format=transcribe`) → LLM via fallback
(**Gemini → Groq → Mistral → OpenRouter**, whichever keys are set) → Gnani **Timbre TTS** (`timbre-v2.5`, SSE).
Silero VAD + LiveKit multilingual turn detector, barge-in on by default, preemptive generation on.
Each user turn's language is detected from the transcript (script ranges + Hinglish words) and the TTS
language is switched to match.

## Run it on your laptop

```bash
uv sync
uv run --env-file .env python -m livekit.agents download-files   # once: VAD + turn-detector model
uv run --env-file .env python -m rex_agent console                # talk through your mic in the terminal
uv run --env-file .env python -m rex_agent dev                    # register with LiveKit Cloud
```

With `dev` running, open the LiveKit **Agents Playground** (agents-playground.livekit.io), connect to your
project, and the `rex` agent joins the room. (Explicit dispatch: the agent name is `rex`.)

## Settings (.env)

| Variable | Default | Meaning |
|---|---|---|
| `REX_USER_NAME` | Johny | Who Rex works for |
| `REX_ENGLISH_ONLY` | `1` | English-only (STT/TTS `en-IN`). Set `0` for multilingual mode |
| `REX_STT_LANGUAGE` | `hi-IN` | Prisma streaming language (one only — the `en-IN,hi-IN` pair is batch-only and is rejected with 1008); `hi-IN` handles Hinglish; e.g. `ta-IN` for a Tamil demo |
| `REX_TTS_MODEL` | `timbre-v2.5` | Timbre model (v2.5 honours `language`) |
| `REX_TTS_VOICE` | `Nalini` | Voice from Gnani's catalogue for that model |
| `REX_TTS_METHOD` | `sse` | `rest` / `sse` / `websocket` |
| `REX_TURN_DETECTION` | `multilingual` | `vad` to skip the turn-detector model |

## What to check in the first live run
1. Greeting is spoken in English within ~2 s of joining.
2. Say "Kal 4 baje meeting rakhni hai" → reply in Hinglish.
3. Interrupt Rex mid-sentence → it stops.
4. Look at the logged metrics: `stt`, `llm ttft`, `tts ttfb`, end-of-utterance delay. Target total ≤ 1.8 s.
5. If the TTS voice errors, try `REX_TTS_VOICE=Pranav` with `REX_TTS_MODEL=timbre-v2.0`.
