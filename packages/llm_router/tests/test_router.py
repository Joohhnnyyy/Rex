import pytest

from rex_llm_router.router import route


def test_supervise_starts_with_gemini_and_falls_back_to_mistral():
    chain = route("supervise")
    assert chain[0].provider == "gemini"
    assert any(m.provider == "mistral" for m in chain[1:])


def test_code_starts_with_codestral():
    assert route("code")[0].name.startswith("codestral")


def test_vision_chain_only_has_vision_models():
    chain = route("vision")
    assert chain and all(m.vision for m in chain)


def test_unknown_task_kind_raises():
    with pytest.raises(ValueError):
        route("dance")


def test_model_ids_can_be_overridden_by_env(monkeypatch):
    monkeypatch.setenv("REX_MODEL_GEMINI_FLASH", "gemini-test-001")
    assert route("supervise")[0].name == "gemini-test-001"


def test_supervise_uses_groq_as_fast_second_choice():
    assert [m.provider for m in route("supervise")][:2] == ["gemini", "groq"]
