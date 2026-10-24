"""Factories for the speech and language models used by the voice session."""

from __future__ import annotations

import os
from collections.abc import Mapping

from livekit.agents import llm as lk_llm
from livekit.plugins import gnani, openai

from rex_agent.config import AgentConfig, llm_providers


def build_stt(cfg: AgentConfig, env: Mapping[str, str] | None = None) -> gnani.STT:
    env = os.environ if env is None else env
    return gnani.STT(
        language=cfg.stt_language,
        api_key=env.get("GNANI_API_KEY"),
        sample_rate=cfg.sample_rate,
        format="transcribe",  # numbers, dates and currency come back normalised
    )


def build_tts(cfg: AgentConfig, env: Mapping[str, str] | None = None) -> gnani.TTS:
    env = os.environ if env is None else env
    return gnani.TTS(
        voice=cfg.tts_voice,
        model=cfg.tts_model,
        language=cfg.tts_language,
        api_key=env.get("GNANI_API_KEY"),
        sample_rate=cfg.sample_rate,
        synthesize_method=cfg.tts_method,
    )


def build_llm(env: Mapping[str, str] | None = None) -> lk_llm.FallbackAdapter:
    env = os.environ if env is None else env
    specs = llm_providers(env)
    if not specs:
        raise RuntimeError("No LLM API key set (GEMINI_API_KEY, GROQ_API_KEY, MISTRAL_API_KEY or OPENROUTER_API_KEY)")
    llms = [openai.LLM(model=s.name, base_url=s.base_url, api_key=env[s.key_env]) for s in specs]
    return lk_llm.FallbackAdapter(llms, attempt_timeout=8.0)
