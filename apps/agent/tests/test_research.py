"""research_web: Firecrawl search/scrape through the gateway, trimmed to a few hundred tokens."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from rex_agent.research import MAX_CHARS, Research, compact_page, compact_search
from rex_mcp_gateway.gateway import ToolDenied, ToolOutcome

REPO_ROOT = Path(__file__).resolve().parents[3]

SEARCH = {
    "web": [
        {"title": "Naruto  T-Shirts | Redwolf", "url": "https://redwolf.in/naruto", "description": "Official merch"},
        {"title": "Souled Store", "url": "https://thesouledstore.com/naruto", "description": "Anime tees"},
    ]
}


def test_compact_search_and_page():
    out = compact_search(json.dumps({"success": True, "data": SEARCH}))
    assert out.splitlines()[:3] == ["1. Naruto T-Shirts | Redwolf", "   https://redwolf.in/naruto", "   Official merch"]
    assert "2. Souled Store" in out
    assert compact_search("plain text answer") == "plain text answer"

    page = compact_page(json.dumps({"markdown": "# Title\n\n\nBody " + "x" * (MAX_CHARS + 50)}))
    assert page.startswith("# Title\nBody") and page.endswith("…(cut)")


class _C:
    def __init__(self, t):
        self.text = t


class FakeGateway:
    def __init__(self, reply=None, raise_exc=None):
        self.reply, self.raise_exc, self.calls = reply, raise_exc, []

    async def call(self, specialist, tool, args, summary=None):
        self.calls.append((specialist, tool, args))
        if self.raise_exc:
            raise self.raise_exc
        return self.reply


@pytest.mark.asyncio
async def test_search_and_read_go_through_the_research_allowlist():
    raw = type("R", (), {"content": [_C(json.dumps(SEARCH))]})()
    gw = FakeGateway(ToolOutcome(ok=True, text="(wrapped)", raw=raw))
    r = Research(gw)
    out = await r.run(query="naruto t-shirt india")
    assert "redwolf.in/naruto" in out and "<untrusted_data" in out
    assert gw.calls[0] == ("research", "firecrawl.firecrawl_search", {"query": "naruto t-shirt india", "limit": 5})

    await r.run(url="https://redwolf.in/naruto")
    assert gw.calls[1][1:] == (
        "firecrawl.firecrawl_scrape",
        {"url": "https://redwolf.in/naruto", "formats": ["markdown"], "onlyMainContent": True},
    )


@pytest.mark.asyncio
async def test_missing_server_or_key_points_to_the_browser():
    r = Research(FakeGateway(raise_exc=ToolDenied("server 'firecrawl' is not connected")))
    assert "Use the browser" in await r.run(query="x")
    r = Research(FakeGateway(ToolOutcome(ok=False, text="The tool failed: Unauthorized: invalid API key")))
    assert "FIRECRAWL_API_KEY" in await r.run(query="x")
    assert "Give a search query" in await Research(FakeGateway()).run()


def test_yaml_only_search_and_scrape_are_read_tier():
    cfg = yaml.safe_load((REPO_ROOT / "infra" / "mcp_servers.yaml").read_text())
    fc = cfg["servers"]["firecrawl"]
    assert fc["default_tier"] == "A"
    assert {k: v["tier"] for k, v in fc["tools"].items()} == {"firecrawl_search": "R", "firecrawl_scrape": "R"}
    assert cfg["allowlists"]["research"] == ["firecrawl"]
    assert "firecrawl" not in cfg["allowlists"]["rex"]


def test_page_drops_images_and_link_urls():
    md = "[Jump to content](https://x/#a)\n![](https://img/x.png)[Bhopal](https://w/Bhopal) is a city.\n\n*\n"
    assert compact_page(md) == "Jump to content\nBhopal is a city."
