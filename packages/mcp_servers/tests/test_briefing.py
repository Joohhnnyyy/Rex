"""Unit tests for Briefing & Memory MCP Server (T-55)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from rex_mcp_servers.briefing import BriefingMemoryStore, build_server

REPO_ROOT = Path(__file__).resolve().parents[3]


def test_briefing_yaml_config_and_tiers():
    p = REPO_ROOT / "infra" / "mcp_servers.yaml"
    cfg = yaml.safe_load(p.read_text())
    servers = cfg.get("servers", {})
    if "briefing" in servers:
        tools = servers["briefing"].get("tools", {})
        assert tools.get("get_morning_briefing", {}).get("tier") == "R"
        assert tools.get("store_memory", {}).get("tier") == "W"


@pytest.mark.asyncio
async def test_briefing_and_memory_tools():
    store = BriefingMemoryStore()
    server = build_server(store)

    tools = await server.list_tools()
    tool_names = {t.name for t in tools}
    assert {"get_morning_briefing", "store_memory", "get_memories"} <= tool_names

    # 1. Store preference
    res_st = await server.call_tool("store_memory", {"key": "favorite_cafe", "value": "Third Wave Coffee, HSR"})
    assert not res_st.is_error
    data_st = json.loads(res_st.content[0].text)
    assert data_st["ok"] is True

    # 2. Get memories
    res_get = await server.call_tool("get_memories", {})
    data_get = json.loads(res_get.content[0].text)
    assert data_get["ok"] is True
    assert data_get["memories"]["favorite_cafe"] == "Third Wave Coffee, HSR"

    # 3. Morning briefing
    res_br = await server.call_tool("get_morning_briefing", {"user_name": "Shankar"})
    data_br = json.loads(res_br.content[0].text)
    assert data_br["ok"] is True
    assert "Namaste Shankar" in data_br["spoken_briefing"]
    assert data_br["meeting_count"] == 2
