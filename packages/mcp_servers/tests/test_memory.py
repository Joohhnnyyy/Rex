"""Long-term memory: survives a new server (restart), feeds the prompt, search and forget work."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from rex_mcp_servers import memory

REPO_ROOT = Path(__file__).resolve().parents[3]


def _json(res) -> dict:
    return json.loads(res.content[0].text)


@pytest.mark.asyncio
async def test_facts_persist_across_restarts_and_reach_the_prompt(tmp_path):
    path = tmp_path / "memory.json"
    assert memory.prompt_block(path) == ""

    s1 = memory.build_server(path)
    await s1.call_tool("remember_fact", {"key": "Coffee Order", "value": "cold brew, no sugar"})
    await s1.call_tool("remember_fact", {"key": "manager", "value": "Shanky"})
    await s1.call_tool("remember_fact", {"key": "coffee order", "value": "filter coffee"})  # correction
    memory.add_episode("Sent Asmi 'are you awake' on WhatsApp.", path)

    s2 = memory.build_server(path)  # a fresh process reads the same file
    found = _json(await s2.call_tool("search_memory", {"query": "coffee"}))
    assert found["facts"] == {"coffee_order": "filter coffee"}
    assert _json(await s2.call_tool("search_memory", {"query": "whatsapp asmi"}))["episodes"][0]["summary"].startswith(
        "Sent Asmi"
    )

    block = memory.prompt_block(path)
    assert "- coffee order: filter coffee" in block and "- manager: Shanky" in block
    assert "Sent Asmi 'are you awake' on WhatsApp." in block

    assert _json(await s2.call_tool("forget_fact", {"key": "Manager"}))["ok"] is True
    assert "manager" not in memory.load(path)["facts"]
    assert _json(await s2.call_tool("forget_fact", {"key": "manager"}))["ok"] is False


def test_prompt_shows_only_recent_episodes(tmp_path):
    path = tmp_path / "m.json"
    for i in range(memory.PROMPT_EPISODES + 3):
        memory.add_episode(f"session {i}", path)
    block = memory.prompt_block(path)
    assert "session 2:" not in block and "session 2\n" not in block
    assert block.rstrip().endswith(f"session {memory.PROMPT_EPISODES + 2}")
    assert len(memory.load(path)["episodes"]) == memory.PROMPT_EPISODES + 3  # all kept on disk


def test_yaml_tiers_and_rex_allowlist():
    cfg = yaml.safe_load((REPO_ROOT / "infra" / "mcp_servers.yaml").read_text())
    tools = cfg["servers"]["memory"]["tools"]
    assert tools["remember_fact"]["tier"] == "W"
    assert tools["forget_fact"]["tier"] == "W"
    assert tools["search_memory"]["tier"] == "R"
    assert "memory" in cfg["allowlists"]["rex"]
