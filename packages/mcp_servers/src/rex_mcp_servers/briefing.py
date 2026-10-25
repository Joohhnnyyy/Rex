"""Briefing & Memory MCP Server (T-55 stretch pick).

Provides:
- get_morning_briefing: synthesizes calendar schedule, open action items, and travel times into a spoken briefing.
- store_memory: saves long-term user facts and preferences (e.g. favorite coffee spot, preferred meeting time).
- get_memory: retrieves stored user preferences and facts.
"""

from __future__ import annotations

import argparse
import json
import logging
from datetime import UTC, datetime
from typing import Any

from mcp.server.mcpserver import MCPServer

logger = logging.getLogger("rex.mcp.briefing")


class BriefingMemoryStore:
    """In-memory key-value memory store for user facts and preferences."""

    def __init__(self) -> None:
        self.memories: dict[str, str] = {
            "timezone": "Asia/Kolkata",
            "preferred_lang": "hi-IN",
            "home_location": "HSR Layout, Bengaluru",
            "work_location": "Indiranagar, Bengaluru",
        }

    def store(self, key: str, value: str) -> dict[str, Any]:
        self.memories[key.lower().strip()] = value
        return {"ok": True, "stored": {key: value}}

    def get_all(self) -> dict[str, Any]:
        return {"ok": True, "memories": dict(self.memories)}

    def generate_briefing(
        self,
        user_name: str = "Shankar",
        events: list[dict[str, str]] | None = None,
        tasks: list[str] | None = None,
    ) -> dict[str, Any]:
        today_events = events or [
            {"time": "10:00 AM", "title": "Team Standup with Johny"},
            {"time": "04:00 PM", "title": "Product Demo Review"},
        ]
        pending_tasks = tasks or ["Verify MCP Gateway permission tiers", "Review LiveKit audio latency"]

        events_summary = ", ".join(f"{e['title']} at {e['time']}" for e in today_events)
        tasks_summary = ", ".join(pending_tasks)

        spoken_text = (
            f"Namaste {user_name}! Aaj aapke schedule mein {len(today_events)} meetings hain: {events_summary}. "
            f"Aapke pending tasks hain: {tasks_summary}. "
            f"Travel time to Indiranagar lagbhag 25 minutes hoga. Have a productive day!"
        )

        return {
            "ok": True,
            "spoken_briefing": spoken_text,
            "meeting_count": len(today_events),
            "events": today_events,
            "tasks": pending_tasks,
            "date": datetime.now(UTC).strftime("%Y-%m-%d"),
        }


def build_server(store: BriefingMemoryStore | None = None) -> MCPServer:
    mem = store or BriefingMemoryStore()
    server = MCPServer("briefing")

    @server.tool()
    async def get_morning_briefing(user_name: str = "Shankar") -> str:
        """Generate a morning briefing summarizing meetings, action items, and travel info in Hinglish/English [Tier R].

        Args:
            user_name: Name of the user.
        """
        out = mem.generate_briefing(user_name=user_name)
        return json.dumps(out, ensure_ascii=False)

    @server.tool()
    async def store_memory(key: str, value: str) -> str:
        """Save a user fact or preference to long-term memory [Tier W].

        Args:
            key: Fact category or label (e.g. 'dietary_preference', 'primary_clinic').
            value: The detail to remember.
        """
        out = mem.store(key, value)
        return json.dumps(out, ensure_ascii=False)

    @server.tool()
    async def get_memories() -> str:
        """Retrieve stored user memories and preferences [Tier R]."""
        out = mem.get_all()
        return json.dumps(out, ensure_ascii=False)

    return server


def main() -> None:
    parser = argparse.ArgumentParser(description="Rex Briefing & Memory MCP Server")
    parser.parse_args()
    srv = build_server()
    srv.run(transport="stdio")


if __name__ == "__main__":
    main()
