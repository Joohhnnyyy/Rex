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
