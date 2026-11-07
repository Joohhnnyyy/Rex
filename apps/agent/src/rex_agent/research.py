"""Read-only web research through Firecrawl (search the web, read one page as clean markdown).

Rex gets one small tool instead of Firecrawl's 30: the search/scrape schemas alone are ~2k tokens and are
sent on every turn. Calls go through the gateway's `firecrawl` server (allowlist "research"), so they show
on the timeline. Doing things on websites (forms, logins) stays with the Playwright browser.
"""

from __future__ import annotations

import json
import re
from typing import Any

from rex_mcp_gateway.gateway import Gateway, NeedsApproval, wrap_untrusted

SPECIALIST = "research"
MAX_CHARS = 6000
SEARCH_LIMIT = 5


def _text(raw: Any) -> str:
    return "\n".join(getattr(c, "text", "") for c in getattr(raw, "content", []) if getattr(c, "text", None))


def _results(payload: Any) -> list[dict]:
    """Search results wherever the response keeps them: a list, {"web": [...]}, {"data": {"web": [...]}}."""
    if isinstance(payload, list):
        return [r for r in payload if isinstance(r, dict)]
    if isinstance(payload, dict):
        for key in ("web", "results", "data", "news"):
            if key in payload:
                found = _results(payload[key])
                if found:
                    return found
    return []


def compact_search(text: str) -> str:
    try:
        results = _results(json.loads(text))
    except ValueError:
        return text[:MAX_CHARS]
    if not results:
        return text[:MAX_CHARS]
    lines = []
    for i, r in enumerate(results[:SEARCH_LIMIT], 1):
        title = " ".join(str(r.get("title") or "").split())
        url = r.get("url") or r.get("link") or ""
        about = " ".join(str(r.get("description") or r.get("snippet") or r.get("markdown") or "").split())[:400]
        lines.append(f"{i}. {title}\n   {url}\n   {about}")
    return "\n".join(lines)


def compact_page(text: str) -> str:
    try:
        payload = json.loads(text)
        if isinstance(payload, dict):
            text = str(payload.get("markdown") or (payload.get("data") or {}).get("markdown") or text)
    except ValueError:
        pass
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", text)  # images
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)  # [link text](url) -> link text
    text = "\n".join(line.rstrip() for line in text.splitlines() if len(line.strip()) > 2)
    return text[:MAX_CHARS] + (" …(cut)" if len(text) > MAX_CHARS else "")


class Research:
    def __init__(self, gw: Gateway) -> None:
        self.gw = gw

    async def run(self, query: str = "", url: str = "") -> str:
        if url:
            tool, args, what = "firecrawl_scrape", {"url": url, "formats": ["markdown"], "onlyMainContent": True}, url
        elif query:
            tool, args, what = "firecrawl_search", {"query": query, "limit": SEARCH_LIMIT}, query
        else:
            return "Give a search query, or the url of a page to read."
        try:
            out = await self.gw.call(SPECIALIST, f"firecrawl.{tool}", args, summary=f"web · {what[:80]}")
        except Exception as e:  # server not connected (no key) or denied
            return f"Web research isn't available ({type(e).__name__}). Use the browser instead."
        if isinstance(out, NeedsApproval):
            return "That needs approval first."
        if not out.ok:
            msg = out.text.lower()
            if "unknown tool" in msg or "api key" in msg or "unauthorized" in msg or "401" in msg:
                return "Web research isn't set up (FIRECRAWL_API_KEY missing or invalid). Use the browser instead."
            return f"The web lookup failed: {out.text[:200]}"
        body = compact_page(_text(out.raw)) if url else compact_search(_text(out.raw))
        return wrap_untrusted(f"web {what[:60]}", body)
