"""Long-term memory MCP server: facts about the user and a log of past sessions, kept on disk.

One JSON file (default ~/.config/rex/memory.json, override with REX_MEMORY_PATH) survives restarts:
  facts:    {"key": {"value": ..., "updated": "YYYY-MM-DD"}}   e.g. home_city, manager, coffee_order
  episodes: [{"date": ..., "summary": ...}]                     one or two lines per finished session

The agent reads `prompt_block()` into Rex's system prompt at the start of every call and appends an
episode when a call ends; the tools below let Rex add, correct, forget and search during a call.
"""

from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from mcp.server.mcpserver import MCPServer

IST = ZoneInfo("Asia/Kolkata")
MAX_EPISODES = 500  # oldest dropped beyond this; search_memory still covers everything kept
PROMPT_EPISODES = 8  # recent sessions Rex sees without searching


def memory_path() -> Path:
    override = os.environ.get("REX_MEMORY_PATH")
    return Path(override).expanduser() if override else Path.home() / ".config" / "rex" / "memory.json"


def load(path: Path | None = None) -> dict:
    p = path or memory_path()
    try:
        data = json.loads(p.read_text())
    except FileNotFoundError:
        data = {}
    return {"facts": data.get("facts", {}), "episodes": data.get("episodes", [])}


def save(data: dict, path: Path | None = None) -> None:
    """Write atomically so a crash mid-write never leaves a half-written memory file."""
    p = path or memory_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=1))
    os.replace(tmp, p)


def _today() -> str:
    return datetime.now(IST).strftime("%Y-%m-%d")


def _key(key: str) -> str:
    return "_".join(key.lower().split())


# ponytail: read-modify-write without a lock; the agent and this server write rarely and never together.
def remember(key: str, value: str, path: Path | None = None) -> None:
    data = load(path)
    data["facts"][_key(key)] = {"value": value.strip(), "updated": _today()}
    save(data, path)


def forget(key: str, path: Path | None = None) -> bool:
    data = load(path)
    found = data["facts"].pop(_key(key), None) is not None
    if found:
        save(data, path)
    return found


def add_episode(summary: str, path: Path | None = None) -> None:
    data = load(path)
    data["episodes"] = [*data["episodes"], {"date": _today(), "summary": summary.strip()}][-MAX_EPISODES:]
    save(data, path)


def search(query: str, path: Path | None = None) -> dict:
    """Facts and past sessions containing any word of the query (case-insensitive)."""
    words = [w for w in query.lower().split() if len(w) > 2] or [query.lower()]
    data = load(path)
    hit = lambda text: any(w in text.lower() for w in words)  # noqa: E731
    return {
        "facts": {k: f["value"] for k, f in data["facts"].items() if hit(f"{k} {f['value']}")},
        "episodes": [e for e in data["episodes"] if hit(e["summary"])][-10:],
    }


def prompt_block(path: Path | None = None) -> str:
    """What Rex should know at the start of a call; empty when nothing is stored yet."""
    data = load(path)
    lines = []
    if data["facts"]:
        lines.append("Facts about the user:")
        lines += [f"- {k.replace('_', ' ')}: {f['value']}" for k, f in sorted(data["facts"].items())]
    if data["episodes"]:
        lines.append("Recent sessions (oldest first):")
        lines += [f"- {e['date']}: {e['summary']}" for e in data["episodes"][-PROMPT_EPISODES:]]
    return "\n".join(lines)


def build_server(path: Path | None = None) -> MCPServer:
    server = MCPServer("memory")

    @server.tool()
    async def remember_fact(key: str, value: str) -> str:
        """Save or update a lasting fact about the user so you know it in future calls [Tier W].

        Use for preferences, people, places, projects and routines, not one-off requests.

        Args:
            key: short label, e.g. "manager", "home city", "coffee order", "current project"
            value: the fact, e.g. "Shanky", "Bengaluru", "cold brew, no sugar"
        """
        remember(key, value, path)
        return json.dumps({"ok": True, "saved": {_key(key): value}}, ensure_ascii=False)

    @server.tool()
    async def forget_fact(key: str) -> str:
        """Delete a stored fact the user says is wrong or wants forgotten [Tier W].

        Args:
            key: the label of the fact to delete
        """
        return json.dumps({"ok": forget(key, path), "key": _key(key)})

    @server.tool()
    async def search_memory(query: str) -> str:
        """Search stored facts and past sessions older than the ones already in your instructions [Tier R].

        Args:
            query: words to look for, e.g. "dentist", "WhatsApp Asmi", "Rex demo"
        """
        return json.dumps(search(query, path), ensure_ascii=False)

    return server


if __name__ == "__main__":
    build_server().run()
