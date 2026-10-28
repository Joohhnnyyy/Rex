"""Offline check that our factories match the installed LiveKit / Gnani plugin APIs."""

from livekit.agents import llm as lk_llm

from rex_agent.config import AgentConfig
from rex_agent.models import build_llm, build_stt, build_tts, portable_ctx

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


def _history(extra):
    return lk_llm.ChatContext(
        [
            lk_llm.ChatMessage(role="user", content=["what's on tomorrow?"]),
            lk_llm.FunctionCall(call_id="c1", name="calendar__list_events", arguments="{}", extra=extra),
            lk_llm.FunctionCallOutput(call_id="c1", name="calendar__list_events", output="[]", is_error=False),
        ]
    )


def test_portable_ctx_strips_gemini_signatures_for_other_providers():
    ctx = portable_ctx(_history({"google": {"thought_signature": "abc"}}), gemini=False)
    assert ctx.items[1].extra == {}


def test_portable_ctx_gives_gemini_a_placeholder_for_foreign_tool_calls():
    ctx = portable_ctx(_history({}), gemini=True)
    assert ctx.items[1].extra["google"]["thought_signature"] == "skip_thought_signature_validator"


def test_portable_ctx_keeps_geminis_own_signature():
    original = _history({"google": {"thought_signature": "real"}})
    assert portable_ctx(original, gemini=True).items[1].extra["google"]["thought_signature"] == "real"
    assert original.items[1].extra["google"]["thought_signature"] == "real"  # input not mutated
