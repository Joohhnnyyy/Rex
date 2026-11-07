"""The background specialists Rex can delegate long jobs to (everything else is a direct tool)."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field

REGISTRY: dict[str, str] = {
    "meeting": "Join a meeting, record it, and produce minutes and action items.",
    "coder": "Read a code repository, fix a bug or make a change, run tests, open a pull request.",
}


@dataclass
class ExecResult:
    ok: bool
    summary: str  # one short sentence, spoken to the user
    data: dict = field(default_factory=dict)


Executor = Callable[[str, str], Awaitable[ExecResult]]  # (request, lang) -> result
