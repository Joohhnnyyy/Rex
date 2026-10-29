"""Pick an ordered fallback chain of models for a kind of task."""

from __future__ import annotations

import os

from rex_llm_router.models import ModelSpec, spec

CHAINS: dict[str, list[str]] = {
    "supervise": ["gemini_flash", "groq_llama", "nvidia_nemotron", "mistral_small", "openrouter_free"],
    "summarise": ["mistral_small", "groq_llama", "gemini_flash"],
    "code": ["codestral", "gemini_flash"],
    "vision": ["gemini_flash"],
}


def route(task_kind: str) -> list[ModelSpec]:
    """Return the models to try, in order, for ``task_kind``.

    Override the order with REX_CHAIN_<KIND>, e.g. REX_CHAIN_SUPERVISE=mistral_small,groq_llama
    (used to test without spending the 20/day Gemini free-tier quota).
    """
    try:
        aliases = CHAINS[task_kind]
    except KeyError:
        raise ValueError(f"unknown task kind {task_kind!r}; expected one of {sorted(CHAINS)}") from None
    if override := os.environ.get(f"REX_CHAIN_{task_kind.upper()}"):
        aliases = [a.strip() for a in override.split(",") if a.strip()]
    return [spec(a) for a in aliases]
