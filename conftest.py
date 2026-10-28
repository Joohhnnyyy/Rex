import pytest


@pytest.fixture(autouse=True)
def _default_llm_chain(request, monkeypatch):
    """Offline tests assume the default model chain; only live tests honour REX_CHAIN_* overrides."""
    if "live" not in request.node.path.parts:
        for name in ("REX_CHAIN_SUPERVISE", "REX_CHAIN_SUMMARISE", "REX_CHAIN_CODE", "REX_CHAIN_VISION"):
            monkeypatch.delenv(name, raising=False)
