"""Thin async chat client with per-task model fallback.

Fallback policy: rate limit (429), server error (5xx), timeout or connection
error -> try the next model. Any other 4xx is our bug -> raise immediately.
Providers without an API key are skipped.
"""

from __future__ import annotations

import os
import time
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

import httpx

from rex_llm_router.models import ModelSpec
from rex_llm_router.router import route


@dataclass
class Attempt:
    model: ModelSpec
    outcome: str  # ok | rate_limited | server_error | timeout | network_error | skipped
    ms: int = 0
    detail: str = ""


@dataclass
class Completion:
    text: str
    model: ModelSpec
    attempts: list[Attempt] = field(default_factory=list)
    usage: dict[str, Any] = field(default_factory=dict)


class LLMRequestError(Exception):
    """Non-retryable error (bad request, auth)."""

    def __init__(self, attempt: Attempt):
        super().__init__(f"{attempt.model.alias}: {attempt.detail}")
        self.attempt = attempt


class AllModelsFailed(Exception):
    def __init__(self, attempts: list[Attempt]):
        super().__init__("all models failed: " + ", ".join(f"{a.model.alias}={a.outcome}" for a in attempts))
        self.attempts = attempts


class LLMClient:
    def __init__(
        self,
        env: Mapping[str, str] | None = None,
        transport: httpx.AsyncBaseTransport | None = None,
        timeout_s: float = 20.0,
    ):
        self._env = os.environ if env is None else env
        self._transport = transport
        self._timeout = timeout_s

    async def complete(self, task_kind: str, messages: list[dict[str, Any]], **params: Any) -> Completion:
        attempts: list[Attempt] = []
        async with httpx.AsyncClient(transport=self._transport, timeout=self._timeout) as http:
            for model in route(task_kind):
                key = self._env.get(model.key_env)
                if not key:
                    attempts.append(Attempt(model, "skipped", detail=f"{model.key_env} not set"))
                    continue
                started = time.perf_counter()
                try:
                    resp = await http.post(
                        f"{model.base_url}/chat/completions",
                        headers={"Authorization": f"Bearer {key}"},
                        json={"model": model.name, "messages": messages, **params},
                    )
                except httpx.TimeoutException as exc:
                    attempts.append(Attempt(model, "timeout", _ms(started), str(exc)))
                    continue
                except httpx.TransportError as exc:
                    attempts.append(Attempt(model, "network_error", _ms(started), str(exc)))
                    continue

                if resp.status_code == 429:
                    attempts.append(Attempt(model, "rate_limited", _ms(started)))
                    continue
                if resp.status_code >= 500:
                    attempts.append(Attempt(model, "server_error", _ms(started), str(resp.status_code)))
                    continue
                if resp.status_code >= 400:
                    attempt = Attempt(model, "client_error", _ms(started), f"{resp.status_code} {resp.text[:200]}")
                    attempts.append(attempt)
                    raise LLMRequestError(attempt)

                data = resp.json()
                attempts.append(Attempt(model, "ok", _ms(started)))
                text = data["choices"][0]["message"].get("content") or ""
                return Completion(text=text, model=model, attempts=attempts, usage=data.get("usage", {}))
        raise AllModelsFailed(attempts)


def _ms(started: float) -> int:
    return int((time.perf_counter() - started) * 1000)
