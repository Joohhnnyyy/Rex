"""Rex's own research: interests, Firecrawl search, LLM pick, de-duplication, seen flags."""

from __future__ import annotations

import json

import httpx
import pytest

from rex_mcp_servers import discoveries, memory


@pytest.fixture(autouse=True)
def stores(tmp_path, monkeypatch):
    monkeypatch.setenv("REX_DISCOVERIES_PATH", str(tmp_path / "d.json"))
    monkeypatch.setenv("REX_MEMORY_PATH", str(tmp_path / "m.json"))


def transport(results_by_query, seen_queries):
    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        seen_queries.append((body["query"], body["tbs"], request.headers["authorization"]))
        return httpx.Response(200, json={"success": True, "data": {"web": results_by_query.get(body["query"], [])}})

    return httpx.MockTransport(handler)


def picker(urls):
    async def write(system, user):
        assert "Results:" in user and "JSON" in system
        return "Sure! " + json.dumps({"items": [{"url": u, "title": f"T {u}", "why": "You love this."} for u in urls]})

    return write


def test_interests_merge_list_and_memory_without_duplicates():
    discoveries.set_interests(["Naruto", " IPL ", ""])
    memory.remember("interest_anime", "naruto")  # same as the list, different case
    memory.remember("interest_ai", "AI agents")
    memory.remember("manager", "Shanky")  # not an interest
    assert discoveries.interests() == ["Naruto", "IPL", "AI agents"]


@pytest.mark.asyncio
async def test_run_keeps_only_searched_urls_dedupes_and_marks_new():
    discoveries.set_interests(["Naruto"])
    results = {"Naruto": [{"title": "New Boruto arc", "url": "https://a.com/1", "description": "x"},
                          {"title": "Old shop", "url": "https://shop.com", "description": "y"}]}  # fmt: skip
    queries = []
    async with httpx.AsyncClient(transport=transport(results, queries)) as http:
        # the model also "suggests" a URL that wasn't in the results: it must be dropped
        out = await discoveries.run(picker(["https://a.com/1", "https://made-up.com"]), "fc-key", http)
    assert out == {"added": 1, "searched": ["Naruto"], "errors": []}
    assert queries == [("Naruto", "qdr:w", "Bearer fc-key")]
    items = discoveries.load()["items"]
    assert [(i["url"], i["topic"], i["seen"]) for i in items] == [("https://a.com/1", "Naruto", False)]
    assert "T https://a.com/1 (Naruto): You love this." in discoveries.prompt_block()

    async with httpx.AsyncClient(transport=transport(results, queries)) as http:
        again = await discoveries.run(picker(["https://a.com/1"]), "fc-key", http)
    assert again["added"] == 0 and len(discoveries.load()["items"]) == 1  # no duplicates

    discoveries.mark_seen()
    assert discoveries.unseen() == [] and discoveries.prompt_block() == ""


@pytest.mark.asyncio
async def test_search_failures_are_reported_not_hidden():
    discoveries.set_interests(["F1"])
    failing = httpx.MockTransport(lambda r: httpx.Response(401, json={"error": "bad key"}))
    async with httpx.AsyncClient(transport=failing) as http:
        out = await discoveries.run(picker([]), "bad", http)
    assert out["added"] == 0 and out["errors"] == ["F1: search failed (HTTPStatusError)"]
    assert discoveries.load()["last_run"]
