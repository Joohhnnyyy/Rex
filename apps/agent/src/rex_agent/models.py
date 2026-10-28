"""Factories for the speech and language models used by the voice session."""

from __future__ import annotations

import os
from collections.abc import Mapping
from typing import Any

from livekit.agents import llm as lk_llm
from livekit.plugins import gnani, openai

from rex_agent.config import AgentConfig, llm_providers

# Google's documented placeholder for a tool call Gemini did not make (e.g. one from the fallback model).
_GEMINI_SKIP_SIGNATURE = {"google": {"thought_signature": "skip_thought_signature_validator"}}


class PortableLLM(openai.LLM):
    """Keeps one chat history usable when the fallback chain switches provider mid-conversation.

    Gemini attaches thought signatures to its tool calls and rejects tool calls without one (400);
    Mistral/Groq reject that extra field (422). Without this, one slow Gemini reply breaks every later turn.
    """

    def __init__(self, *, gemini: bool, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._gemini = gemini

    def chat(self, *, chat_ctx: lk_llm.ChatContext, **kwargs: Any) -> Any:
        return super().chat(chat_ctx=portable_ctx(chat_ctx, gemini=self._gemini), **kwargs)


def portable_ctx(chat_ctx: lk_llm.ChatContext, *, gemini: bool) -> lk_llm.ChatContext:
    items = []
    for item in chat_ctx.items:
        if item.type == "function_call" and gemini and not item.extra.get("google"):
            item = item.model_copy(update={"extra": {**item.extra, **_GEMINI_SKIP_SIGNATURE}})
        elif item.type in ("function_call", "message") and not gemini and item.extra:
            item = item.model_copy(update={"extra": {}})
        items.append(item)
    return lk_llm.ChatContext(items)


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
    llms = [
        PortableLLM(
            gemini=s.provider == "gemini",
            model=s.name,
            base_url=s.base_url,
            api_key=env[s.key_env],
            # Thinking off: Rex's turns are routing + tool calls; measured 2.6 s -> 2.1 s per tool step on 2.5-flash.
            **({"reasoning_effort": "none"} if s.provider == "gemini" else {}),
        )
        for s in specs
    ]
    # 4 s per attempt (was 8): a hung provider used to leave the caller in silence for 8 s before fallback.
    return lk_llm.FallbackAdapter(llms, attempt_timeout=4.0)
