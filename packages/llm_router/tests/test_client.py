import json

import httpx
import pytest

from rex_llm_router.client import AllModelsFailed, LLMClient, LLMRequestError

KEYS = {"GEMINI_API_KEY": "g", "GROQ_API_KEY": "q", "MISTRAL_API_KEY": "m", "OPENROUTER_API_KEY": "o"}
MSGS = [{"role": "user", "content": "Namaste"}]


def _ok(text):
    return httpx.Response(200, json={"choices": [{"message": {"content": text}}], "usage": {"total_tokens": 7}})


def make_client(handler, keys=KEYS):
    return LLMClient(env=keys, transport=httpx.MockTransport(handler))


async def test_first_model_success():
    seen = []

    def handler(req):
        seen.append(req)
        return _ok("Namaste! Kaise madad karoon?")

    res = await make_client(handler).complete("supervise", MSGS)
    assert res.text.startswith("Namaste")
    assert res.model.provider == "gemini"
    assert len(seen) == 1
    body = json.loads(seen[0].content)
    assert body["messages"] == MSGS
    assert seen[0].headers["authorization"] == "Bearer g"


async def test_falls_back_on_429():
    def handler(req):
        if "generativelanguage" in str(req.url):
            return httpx.Response(429, json={"error": "rate limited"})
        assert "api.groq.com" in str(req.url)
        return _ok("from groq")

    res = await make_client(handler).complete("supervise", MSGS)
    assert res.text == "from groq"
    assert res.model.provider == "groq"
    assert [a.outcome for a in res.attempts] == ["rate_limited", "ok"]


async def test_falls_back_on_server_error_and_timeout():
    calls = {"n": 0}

    def handler(req):
        calls["n"] += 1
        if calls["n"] == 1:
            return httpx.Response(503)
        if calls["n"] == 2:
            raise httpx.ReadTimeout("slow", request=req)
        return _ok("third time lucky")

    res = await make_client(handler).complete("supervise", MSGS)
    assert res.text == "third time lucky"
    assert [a.outcome for a in res.attempts] == ["server_error", "timeout", "ok"]


async def test_client_error_is_raised_without_fallback():
    calls = {"n": 0}

    def handler(req):
        calls["n"] += 1
        return httpx.Response(400, json={"error": "bad request"})

    with pytest.raises(LLMRequestError):
        await make_client(handler).complete("supervise", MSGS)
    assert calls["n"] == 1


async def test_all_models_failed_lists_attempts():
    res_handler = lambda req: httpx.Response(429)  # noqa: E731
    with pytest.raises(AllModelsFailed) as exc:
        await make_client(res_handler).complete("supervise", MSGS)
    assert len(exc.value.attempts) == 4
    assert {a.outcome for a in exc.value.attempts} == {"rate_limited"}


async def test_provider_without_key_is_skipped():
    def handler(req):
        assert "generativelanguage" not in str(req.url)
        return _ok("mistral answered")

    res = await make_client(handler, keys={"MISTRAL_API_KEY": "m"}).complete("supervise", MSGS)
    assert res.text == "mistral answered"
    assert res.attempts[0].outcome == "skipped"
