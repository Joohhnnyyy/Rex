"""Unit tests for Browser MCP Server (T-44)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from rex_mcp_servers.browser import BrowserSession, build_server

REPO_ROOT = Path(__file__).resolve().parents[3]


def test_browser_mcp_yaml_declares_submit_as_tier_a():
    p = REPO_ROOT / "infra" / "mcp_servers.yaml"
    cfg = yaml.safe_load(p.read_text())
    servers = cfg.get("servers", {})
    assert "browser" in servers, "browser server must be defined in mcp_servers.yaml"
    tools = servers["browser"].get("tools", {})
    assert tools.get("submit_form", {}).get("tier") == "A", "submit_form must be Tier A"
    assert tools.get("navigate", {}).get("tier") == "R", "navigate must be Tier R"
    assert tools.get("read_page", {}).get("tier") == "R", "read_page must be Tier R"
    assert tools.get("fill_form", {}).get("tier") == "W", "fill_form must be Tier W"


@pytest.mark.asyncio
async def test_browser_automation_workflow():
    session = BrowserSession()
    server = build_server(session)

    tools = await server.list_tools()
    tool_names = {t.name for t in tools}
    assert {"navigate", "read_page", "fill_form", "submit_form"} <= tool_names

    # 1. Navigate
    res_nav = await server.call_tool("navigate", {"url": "https://example.com/contact"})
    assert not res_nav.is_error
    data_nav = json.loads(res_nav.content[0].text)
    assert data_nav["status"] == 200

    # 2. Read page
    res_read = await server.call_tool("read_page", {})
    assert not res_read.is_error

    # 3. Fill form fields
    await server.call_tool("fill_form", {"field": "name", "value": "Shankar"})
    await server.call_tool("fill_form", {"field": "email", "value": "shankar@example.com"})
    assert session.form_data == {"name": "Shankar", "email": "shankar@example.com"}

    # 4. Submit form
    res_sub = await server.call_tool("submit_form", {"action_name": "submit_contact"})
    assert not res_sub.is_error
    data_sub = json.loads(res_sub.content[0].text)
    assert data_sub["ok"] is True
    assert len(session.submitted_forms) == 1
    assert session.submitted_forms[0]["data"]["name"] == "Shankar"
    assert session.form_data == {}
