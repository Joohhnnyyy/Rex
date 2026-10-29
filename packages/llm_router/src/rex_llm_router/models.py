"""Model catalogue. Every provider is reached through its OpenAI-compatible chat API."""

from __future__ import annotations

import os
from dataclasses import dataclass

PROVIDERS: dict[str, dict[str, str]] = {
    # Gemini's OpenAI-compatible endpoint
    "gemini": {"base_url": "https://generativelanguage.googleapis.com/v1beta/openai", "key_env": "GEMINI_API_KEY"},
    "groq": {"base_url": "https://api.groq.com/openai/v1", "key_env": "GROQ_API_KEY"},
    "mistral": {"base_url": "https://api.mistral.ai/v1", "key_env": "MISTRAL_API_KEY"},
    "openrouter": {"base_url": "https://openrouter.ai/api/v1", "key_env": "OPENROUTER_API_KEY"},
    "nvidia": {"base_url": "https://integrate.api.nvidia.com/v1", "key_env": "NVIDIA_API_KEY"},
}

# alias -> (provider, default model id, supports vision). Override ids with REX_MODEL_<ALIAS>,
# because free-tier model names change often.
CATALOGUE: dict[str, tuple[str, str, bool]] = {
    "gemini_flash": ("gemini", "gemini-2.5-flash", True),
    "groq_llama": ("groq", "llama-3.3-70b-versatile", False),
    # ~3.9 s per tool turn (Groq 1.4 s): backup for when the free tiers above are exhausted
    "nvidia_nemotron": ("nvidia", "nvidia/nemotron-3-ultra-550b-a55b", False),
    "mistral_small": ("mistral", "mistral-small-latest", False),
    "codestral": ("mistral", "codestral-latest", False),
    "openrouter_free": ("openrouter", "meta-llama/llama-3.3-70b-instruct:free", False),
}


@dataclass(frozen=True)
class ModelSpec:
    alias: str
    provider: str
    name: str
    vision: bool

    @property
    def base_url(self) -> str:
        return PROVIDERS[self.provider]["base_url"]

    @property
    def key_env(self) -> str:
        return PROVIDERS[self.provider]["key_env"]


def spec(alias: str) -> ModelSpec:
    provider, default_name, vision = CATALOGUE[alias]
    name = os.environ.get(f"REX_MODEL_{alias.upper()}", default_name)
    return ModelSpec(alias=alias, provider=provider, name=name, vision=vision)
