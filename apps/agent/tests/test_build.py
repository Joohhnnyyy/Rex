"""Offline check that our factories match the installed LiveKit / Gnani plugin APIs."""

from livekit.agents import llm as lk_llm

from rex_agent.config import AgentConfig
from rex_agent.models import build_llm, build_stt, build_tts

ENV = {"GNANI_API_KEY": "x", "GEMINI_API_KEY": "g", "GROQ_API_KEY": "q"}


def test_build_stt_and_tts_with_key():
    cfg = AgentConfig.from_env(ENV)
    stt = build_stt(cfg, ENV)
    tts = build_tts(cfg, ENV)
    assert stt is not None and tts is not None
    assert tts.sample_rate == 16000


def test_build_llm_is_fallback_adapter_over_available_providers():
    llm = build_llm(ENV)
    assert isinstance(llm, lk_llm.FallbackAdapter)
    assert len(llm._llm_instances) == 2
