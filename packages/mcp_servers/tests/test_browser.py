"""Browser MCP server (T-38): tiers, URL guard, and a real headless Chromium run against a local page."""

from __future__ import annotations

import asyncio
import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs

import pytest
import yaml
from mcp.server.mcpserver.exceptions import ToolError

from rex_mcp_servers.browser import Browser, build_server, check_url, read_live_frame

REPO_ROOT = Path(__file__).resolve().parents[3]

FORM = b"""<html><head><title>Clinic booking</title></head><body>
<h1>Book a visit</h1><a href="/about">About the clinic</a>
<form action="/done" method="get">
  <label for="n">Your name</label><input id="n" name="name">
  <input name="email" placeholder="Email address">
  <button type="submit">Book now</button>
</form></body></html>"""


class _Handler(BaseHTTPRequestHandler):
    def do_GET(self):  # noqa: N802
        if self.path.startswith("/done"):
            q = parse_qs(self.path.split("?", 1)[1])
            body = f"<html><title>Booked</title><body>Booked for {q['name'][0]}</body></html>".encode()
        else:
            body = FORM
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *a):
        pass


def test_yaml_tiers_and_rex_tool_budget():
    cfg = yaml.safe_load((REPO_ROOT / "infra" / "mcp_servers.yaml").read_text())
    tools = cfg["servers"]["browser"]["tools"]
    assert tools["navigate"]["tier"] == "R"
    assert tools["read_page"]["tier"] == "R"
    assert tools["fill_form"]["tier"] == "W"
    assert tools["click"]["tier"] == "A"
    assert tools["submit_form"]["tier"] == "A"
    assert "browser" in cfg["allowlists"]["rex"]


def test_check_url_blocks_local_and_non_http():
    with pytest.raises(ToolError):
        check_url("http://127.0.0.1:8000/", allow_local=False)
    with pytest.raises(ToolError):
        check_url("http://192.168.1.1/", allow_local=False)
    with pytest.raises(ToolError):
        check_url("file:///etc/passwd", allow_local=True)
    assert check_url("127.0.0.1:9/x", allow_local=True) == "https://127.0.0.1:9/x"


@pytest.fixture
def site():
    srv = HTTPServer(("127.0.0.1", 0), _Handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{srv.server_port}"
    srv.shutdown()


@pytest.mark.asyncio
async def test_real_browser_fill_and_submit(site, tmp_path, monkeypatch):
    monkeypatch.setenv("REX_BROWSER_ALLOW_LOCAL", "1")
    b = Browser(headless=True, profile_dir=tmp_path / "profile")
    b.live_dir = tmp_path / "live"
    server = build_server(b)
    try:
        res = await server.call_tool("navigate", {"url": site})
        page = json.loads(res.content[0].text)
        assert page["title"] == "Clinic booking"
        assert "Book a visit" in page["text"]
        assert {"field": "Your name", "type": "text"} in page["fields"]
        assert any(link["text"] == "About the clinic" for link in page["links"])
        assert "Book now" in page["buttons"]

        for _ in range(30):  # the live view writes a frame within ~1 s
            frame = read_live_frame(b.live_dir)
            if frame:
                break
            await asyncio.sleep(0.1)
        state, jpeg = frame
        assert state["title"] == "Clinic booking" and state["url"].startswith(site)
        assert jpeg[:2] == b"\xff\xd8"  # JPEG

        await server.call_tool("fill_form", {"field": "Your name", "value": "Shanky"})
        await server.call_tool("fill_form", {"field": "Email address", "value": "s@example.com"})
        res = await server.call_tool("submit_form", {"button": "Book now"})
        done = json.loads(res.content[0].text)
        assert done["title"] == "Booked"
        assert "Booked for Shanky" in done["text"]

        with pytest.raises(ToolError, match="read_page"):  # the model is told how to recover
            await server.call_tool("fill_form", {"field": "No such field", "value": "x"})
    finally:
        await b.close()
