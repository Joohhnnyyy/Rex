# Summary 01-01 — Voice agent worker

Built 2026-10-24 (Claude, TDD). Package `apps/agent` (`rex_agent`).

- Pipeline: Prisma STT → FallbackAdapter LLM (Gemini/Groq/Mistral/OpenRouter) → Timbre TTS; Silero VAD; multilingual turn detector with VAD fallback; preemptive generation; barge-in default.
- Per-turn language detection (`lang.py`) for 8 Indic scripts + English + Hinglish; switches TTS language.
- Metrics logged per turn + usage summary on shutdown.
- 21 new tests (42 total), ruff clean.

Not yet verified live: this session's network blocks Gnani, LiveKit, LLM providers and Hugging Face. Live check steps in `apps/agent/README.md`.
