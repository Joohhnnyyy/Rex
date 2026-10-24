# Phase 01 — Voice loop + supervisor: context

Goal: talk to Rex in the browser or terminal in Hinglish / English / Indian languages and get a spoken answer in < 2 s.

Locked decisions
- LiveKit Agents 1.8 with the official `livekit-plugins-gnani` (it provides **both** Prisma STT and Timbre TTS).
- LLM = LiveKit `FallbackAdapter` over OpenAI-compatible endpoints in router order (Gemini → Groq → Mistral → OpenRouter); providers without keys are skipped.
- STT language `en-IN,hi-IN` (Prisma auto-detect pair); `format=transcribe`.
- TTS `timbre-v2.5`, voice `Nalini`, SSE; TTS language switched per user turn from script detection.
- Turn detection: multilingual model, VAD fallback if model files are missing.
- Greeting and call disclosure in English.
