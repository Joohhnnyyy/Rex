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
    assert set(by_id) == {"voice", "calendar", "gmail", "slack", "notion", "browser"}
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
