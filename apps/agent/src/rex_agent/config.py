from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass

from rex_llm_router import ModelSpec, route


@dataclass(frozen=True)
class AgentConfig:
    user_name: str = "Johny"
    english_only: bool = True  # REX_ENGLISH_ONLY=0 turns multilingual mode back on
    stt_language: str = "en-IN"
    tts_language: str | None = "en-IN"  # None = switch per user turn (multilingual mode)
    tts_model: str = "timbre-v2.5"
    tts_voice: str = "Nalini"
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
