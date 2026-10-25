"""Unit tests for Vexa Meeting MCP Server (T-33)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from rex_mcp_servers.vexa import VexaClient, build_server

REPO_ROOT = Path(__file__).resolve().parents[3]


def test_vexa_yaml_config_and_tiers():
    p = REPO_ROOT / "infra" / "mcp_servers.yaml"
    cfg = yaml.safe_load(p.read_text())
    servers = cfg.get("servers", {})
    if "vexa" in servers:
        tools = servers["vexa"].get("tools", {})
        assert tools.get("join_meeting", {}).get("tier") == "W"
        assert tools.get("fetch_transcript", {}).get("tier") == "R"


@pytest.mark.asyncio
async def test_vexa_meeting_lifecycle():
    client = VexaClient()
    server = build_server(client)

    tools = await server.list_tools()
    tool_names = {t.name for t in tools}
    assert {"join_meeting", "get_meeting_status", "fetch_transcript", "leave_meeting"} <= tool_names

    # 1. Join meeting
    res_join = await server.call_tool("join_meeting", {"meeting_url": "https://meet.google.com/abc-defg-hij"})
    assert not res_join.is_error
    data_join = json.loads(res_join.content[0].text)
    assert data_join["ok"] is True
    assert data_join["status"] == "in_call"
    meeting_id = data_join["meeting_id"]

    # 2. Status
    res_st = await server.call_tool("get_meeting_status", {"meeting_id": meeting_id})
    data_st = json.loads(res_st.content[0].text)
    assert data_st["ok"] is True
    assert data_st["status"] == "in_call"

    # 3. Transcript
    res_tr = await server.call_tool("fetch_transcript", {"meeting_id": meeting_id})
    data_tr = json.loads(res_tr.content[0].text)
    assert data_tr["ok"] is True
    assert "Johny:" in data_tr["transcript"]

    # 4. Leave
    res_lv = await server.call_tool("leave_meeting", {"meeting_id": meeting_id})
    data_lv = json.loads(res_lv.content[0].text)
    assert data_lv["ok"] is True
    assert data_lv["status"] == "completed"

    # 5. Non-existent meeting
    res_err = await server.call_tool("get_meeting_status", {"meeting_id": "bad_id"})
    data_err = json.loads(res_err.content[0].text)
    assert data_err["ok"] is False
