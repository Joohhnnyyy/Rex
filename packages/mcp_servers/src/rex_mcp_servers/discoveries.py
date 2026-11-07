"""Rex's own research: it searches the web for things the user is into and keeps what's worth showing.

Interests come from the user's list (set on the dashboard) plus facts Rex remembers whose key starts with
"interest" (e.g. remember_fact("interest_anime", "Naruto")). Each run searches the past week per interest
with Firecrawl, then an LLM keeps only items that are new and genuinely interesting, each with one line on
why the user would care. Found items live in ~/.config/rex/discoveries.json (REX_DISCOVERIES_PATH).
"""

from __future__ import annotations

import json
import os
import re
import uuid
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from pathlib import Path

import httpx

from rex_mcp_servers import memory

SEARCH_URL = "https://api.firecrawl.dev/v2/search"
MAX_INTERESTS = 4  # searches per run: each costs Firecrawl credits
MAX_ITEMS = 200
PICK_SYSTEM = (
    "You pick discoveries for a user from web search results. Keep only items that are new (this week), "
    "specific and genuinely interesting for the stated interest: releases, launches, deals, events, notable "
    "news. Skip generic pages, listicles of old content, shops' home pages and anything already known. "
    'Reply with JSON only: {"items": [{"url": "...", "title": "short title", "why": "one sentence on why '
    'this user would care"}]}. At most 2 items per interest; an empty list is fine.'
)

Write = Callable[[str, str], Awaitable[str]]  # (system, user) -> text


def store_path() -> Path:
    override = os.environ.get("REX_DISCOVERIES_PATH")
    return Path(override).expanduser() if override else Path.home() / ".config" / "rex" / "discoveries.json"


def load(path: Path | None = None) -> dict:
    try:
        data = json.loads((path or store_path()).read_text())
    except (FileNotFoundError, ValueError):
        data = {}
    return {"interests": data.get("interests", []), "items": data.get("items", []), "last_run": data.get("last_run")}


def save(data: dict, path: Path | None = None) -> None:
    p = path or store_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=1))
    os.replace(tmp, p)


def interests(data: dict | None = None) -> list[str]:
    """The user's list first, then remembered interests; de-duplicated, capped per run."""
    data = data or load()
    found = [str(i).strip() for i in data["interests"] if str(i).strip()]
    for key, fact in memory.load()["facts"].items():
        if key.startswith("interest"):
            found.append(str(fact.get("value", "")).strip())
    seen: set[str] = set()
    out = []
    for topic in found:
        if topic and topic.lower() not in seen:
            seen.add(topic.lower())
            out.append(topic)
    return out[:MAX_INTERESTS]


def set_interests(topics: list[str], path: Path | None = None) -> list[str]:
    data = load(path)
    data["interests"] = [t.strip() for t in topics if t and t.strip()][:12]
    save(data, path)
    return data["interests"]


def mark_seen(path: Path | None = None) -> None:
    data = load(path)
    for item in data["items"]:
        item["seen"] = True
    save(data, path)


def unseen(limit: int = 3, path: Path | None = None) -> list[dict]:
    return [i for i in reversed(load(path)["items"]) if not i.get("seen")][:limit]


async def search(topic: str, http: httpx.AsyncClient, key: str) -> list[dict]:
    resp = await http.post(
        SEARCH_URL,
        headers={"Authorization": f"Bearer {key}"},
        json={"query": topic, "limit": 6, "tbs": "qdr:w", "sources": [{"type": "web"}]},
    )
    resp.raise_for_status()
    web = (resp.json().get("data") or {}).get("web") or []
    return [
        {"title": r.get("title", ""), "url": r.get("url", ""), "description": (r.get("description") or "")[:300]}
        for r in web
        if r.get("url")
    ]


def _json(text: str) -> dict:
    match = re.search(r"\{.*\}", text, re.S)
    try:
        return json.loads(match.group(0)) if match else {}
    except ValueError:
        return {}


async def run(write: Write, key: str, http: httpx.AsyncClient | None = None, path: Path | None = None) -> dict:
    """One discovery pass. Returns {"added": n, "searched": [...], "errors": [...]}."""
    data = load(path)
    topics = interests(data)
    known = {i["url"] for i in data["items"]}
    added, errors = 0, []
    own = http is None
    http = http or httpx.AsyncClient(timeout=30)
    try:
        for topic in topics:
            try:
                results = [r for r in await search(topic, http, key) if r["url"] not in known]
            except Exception as e:
                errors.append(f"{topic}: search failed ({type(e).__name__})")
                continue
            if not results:
                continue
            listing = "\n".join(f"- {r['title']} | {r['url']} | {r['description']}" for r in results)
            picked = _json(await write(PICK_SYSTEM, f"Interest: {topic}\nResults:\n{listing}"))
            allowed = {r["url"]: r for r in results}
            for item in (picked.get("items") or [])[:2]:
                url = str(item.get("url", ""))
                if url not in allowed or url in known:  # only URLs that came back from the search
                    continue
                known.add(url)
                data["items"].append(
                    {
                        "id": uuid.uuid4().hex[:10],
                        "topic": topic,
                        "title": str(item.get("title") or allowed[url]["title"])[:140],
                        "url": url,
                        "why": str(item.get("why", ""))[:240],
                        "found_at": datetime.now(UTC).isoformat(timespec="seconds"),
                        "seen": False,
                    }
                )
                added += 1
    finally:
        if own:
            await http.aclose()
    data["items"] = data["items"][-MAX_ITEMS:]
    data["last_run"] = datetime.now(UTC).isoformat(timespec="seconds")
    save(data, path)
    return {"added": added, "searched": topics, "errors": errors}


def prompt_block(limit: int = 3) -> str:
    """New finds for Rex's prompt, so it can bring one up naturally."""
    items = unseen(limit)
    return "\n".join(f"- {i['title']} ({i['topic']}): {i['why']}" for i in items)
