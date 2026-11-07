from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass

from rex_llm_router import ModelSpec, route

# Gnani timbre-v3.0 voices (all speak the 10 Indian languages). v2.5 voices are rejected by v3.0 and vice versa.
VOICES: dict[str, str] = {
    "Lakshmi": "female, expressive and warm (default)",
    "Shivani": "female, warm and patient",
    "Chetana": "female, warm and empathetic",
    "Kalpana": "female, calm and composed",
    "Riyaa": "female, confident and lively",
    "Tarika": "female, warm and reassuring",
    "Vasudha": "female, expressive narrator",
    "Devansh": "male, young and energetic",
    "Shubham": "male, energetic and confident",
    "Yashraj": "male, warm storyteller",
    "Avinash": "male, professional and firm",
    "Prakash": "male, steady and deliberate",
    "Harshad": "male, professional and firm",
}


@dataclass(frozen=True)
class AgentConfig:
    user_name: str = "Johny"
    english_only: bool = True  # REX_ENGLISH_ONLY=0 turns multilingual mode back on
    stt_language: str = "en-IN"
    tts_language: str | None = "en-IN"  # None = switch per user turn (multilingual mode)
    tts_model: str = "timbre-v3.0"  # v3.0 voices speak all 10 languages and act on <laugh>-style tags
    tts_voice: str = "Lakshmi"
    tts_method: str = "sse"  # rest | sse | websocket
    sample_rate: int = 16000

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> AgentConfig:
        env = os.environ if env is None else env
        d = cls()
        english_only = env.get("REX_ENGLISH_ONLY", "1").lower() not in {"0", "false", "no"}
        # Streaming STT accepts one language; hi-IN handles Hinglish (the en-IN,hi-IN pair is batch-only).
        default_stt = "en-IN" if english_only else "hi-IN"
        return cls(
            user_name=env.get("REX_USER_NAME", d.user_name),
            english_only=english_only,
            stt_language=env.get("REX_STT_LANGUAGE", default_stt),
            tts_language="en-IN" if english_only else None,
            tts_model=env.get("REX_TTS_MODEL", d.tts_model),
            tts_voice=env.get("REX_TTS_VOICE", d.tts_voice),
            tts_method=env.get("REX_TTS_METHOD", d.tts_method),
        )


def llm_providers(env: Mapping[str, str] | None = None) -> list[ModelSpec]:
    """Supervisor models (router order) whose API key is present."""
    env = os.environ if env is None else env
    return [m for m in route("supervise") if env.get(m.key_env)]
