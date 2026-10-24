"""The specialists the supervisor can delegate to.

Each specialist gets a one-line description (the LLM routes on it), a `slow` flag
(slow work runs in the background after a spoken acknowledgement), and the
MCP tool namespaces it may use once the gateway (T-20) is connected.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Specialist:
    name: str
    description: str
    slow: bool = False
    tool_namespaces: tuple[str, ...] = ()


@dataclass
class ExecResult:
    ok: bool
    summary: str  # one short sentence, spoken to the user
    data: dict = field(default_factory=dict)


Executor = Callable[[str, str], Awaitable[ExecResult]]  # (request, lang) -> result

REGISTRY: dict[str, Specialist] = {
    s.name: s
    for s in [
        Specialist(
            "calendar", "Find free time, create, move or cancel calendar events and invites.", False, ("calendar",)
        ),
        Specialist(
            "comms",
            "Read, summarise or send Slack messages and emails; save notes to Notion.",
            False,
            ("slack", "gmail", "notion"),
        ),
        Specialist("location", "Look up places, travel time / ETA, and share a location pin.", False, ("maps",)),
        Specialist(
            "caller",
            "Phone a business or person to book or confirm an appointment, then report back.",
            True,
            ("call_tool", "calendar"),
        ),
        Specialist(
            "meeting",
            "Join a meeting, record it, and produce minutes and action items.",
            True,
            ("vexa", "minutes", "notion", "slack"),
        ),
        Specialist(
            "coder",
            "Read a code repository, fix a bug or make a change, run tests, open a pull request.",
            True,
            ("github", "sandbox"),
        ),
        Specialist(
            "screen",
            "Look at the user's screen or browser and explain or act on what is there.",
            False,
            ("screen_tool", "playwright"),
        ),
    ]
}


def specialist_names() -> list[str]:
    return list(REGISTRY)


class NotConnected:
    """Placeholder executor until the specialist's tools are wired through the MCP gateway."""

    def __init__(self, name: str) -> None:
        self.name = name

    async def __call__(self, request: str, lang: str) -> ExecResult:
        return ExecResult(ok=False, summary=f"The {self.name} skill is not connected yet.")
