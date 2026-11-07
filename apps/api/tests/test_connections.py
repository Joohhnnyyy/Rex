import pytest
from httpx import ASGITransport, AsyncClient

from rex_api import connections
from rex_api.main import create_app
from rex_api.settings import Settings


@pytest.mark.asyncio
async def test_connections_report_each_service(monkeypatch, tmp_path):
    monkeypatch.setenv("REX_GOOGLE_TOKEN_PATH", str(tmp_path / "missing.json"))
    monkeypatch.setenv("SLACK_BOT_TOKEN", "xoxb-test")
    monkeypatch.delenv("NOTION_TOKEN", raising=False)
    monkeypatch.setattr(
        connections,
        "_browser",
        lambda: connections.Connection(id="browser", name="Browser", status="ok", detail="Chromium ready"),
    )

    app = create_app(Settings())
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        res = await c.get("/v1/connections")
    assert res.status_code == 200
    by_id = {x["id"]: x for x in res.json()}
    assert set(by_id) == {"voice", "calendar", "gmail", "slack", "notion", "firecrawl", "browser"}
    assert by_id["calendar"]["status"] == "off" and "calendar login" in by_id["calendar"]["detail"]
    assert by_id["gmail"]["status"] == "off"
    assert by_id["slack"]["status"] == "ok"
    assert by_id["notion"] == {"id": "notion", "name": "Notion", "status": "off", "detail": "Set NOTION_TOKEN in .env"}


@pytest.mark.asyncio
async def test_memory_endpoint_lists_facts_and_newest_calls_first(monkeypatch, tmp_path):
    from rex_mcp_servers import memory

    path = tmp_path / "m.json"
    monkeypatch.setenv("REX_MEMORY_PATH", str(path))
    memory.remember("manager", "Shanky")
    memory.add_episode("first call")
    memory.add_episode("second call")
    async with AsyncClient(transport=ASGITransport(app=create_app(Settings())), base_url="http://test") as c:
        body = (await c.get("/v1/memory")).json()
    assert body["facts"]["manager"]["value"] == "Shanky"
    assert [e["summary"] for e in body["episodes"]] == ["second call", "first call"]


@pytest.mark.asyncio
async def test_discoveries_endpoints(monkeypatch, tmp_path):
    monkeypatch.setenv("REX_DISCOVERIES_PATH", str(tmp_path / "d.json"))
    monkeypatch.setenv("REX_MEMORY_PATH", str(tmp_path / "m.json"))
    monkeypatch.delenv("FIRECRAWL_API_KEY", raising=False)
    async with AsyncClient(transport=ASGITransport(app=create_app(Settings())), base_url="http://test") as c:
        assert (await c.put("/v1/discoveries/interests", json={"interests": ["Naruto", " "]})).json() == {
            "interests": ["Naruto"]
        }
        body = (await c.get("/v1/discoveries")).json()
        assert body["active_interests"] == ["Naruto"] and body["items"] == [] and body["ready"] is False
        res = await c.post("/v1/discoveries/run")
        assert res.status_code == 503 and "FIRECRAWL_API_KEY" in res.json()["detail"]
        assert (await c.post("/v1/discoveries/seen")).json() == {"ok": True}


@pytest.mark.asyncio
async def test_files_are_served_safely(monkeypatch, tmp_path):
    from rex_mcp_servers import files

    monkeypatch.setenv("REX_FILES_DIR", str(tmp_path / "Rex"))
    img = files.write_note("x", "y")
    files._save([{**img, "mime": "image/png"}])  # pretend it's an image
    page = files.write_note("page", "<script>alert(1)</script>")
    entries = files.load()
    files._save([*entries, {**page, "mime": "text/html", "name": "page.html"}])
    async with AsyncClient(transport=ASGITransport(app=create_app(Settings())), base_url="http://test") as c:
        listed = (await c.get("/v1/files")).json()
        assert {f["name"] for f in listed["files"]} >= {"x.md", "page.html"}
        r = await c.get(f"/v1/files/{img['id']}/content")
        assert (
            r.headers["content-disposition"].startswith("inline") and r.headers["x-content-type-options"] == "nosniff"
        )
        r = await c.get(f"/v1/files/{page['id']}/content")
        assert r.headers["content-disposition"].startswith("attachment")  # never rendered on our origin
        assert r.headers["content-type"] == "application/octet-stream"
        assert (await c.get("/v1/files/nope/content")).status_code == 404
