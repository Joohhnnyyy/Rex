"""Pick an ordered fallback chain of models for a kind of task."""

from __future__ import annotations

from rex_llm_router.models import ModelSpec, spec

CHAINS: dict[str, list[str]] = {
    "supervise": ["gemini_flash", "groq_llama", "mistral_small", "openrouter_free"],
    "summarise": ["mistral_small", "groq_llama", "gemini_flash"],
    "code": ["codestral", "gemini_flash"],
    "vision": ["gemini_flash"],
}


def route(task_kind: str) -> list[ModelSpec]:
    """Return the models to try, in order, for ``task_kind``."""
    try:
        aliases = CHAINS[task_kind]
    except KeyError:
        raise ValueError(f"unknown task kind {task_kind!r}; expected one of {sorted(CHAINS)}") from None
    return [spec(a) for a in aliases]
