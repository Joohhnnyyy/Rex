import re
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[3]


def load_mcp_config():
    p = REPO_ROOT / "infra" / "mcp_servers.yaml"
    return yaml.safe_load(p.read_text()) or {}


def test_notion_server_config():
    cfg = load_mcp_config()
    servers = cfg.get("servers", {})
    assert "notion" in servers, "Notion server must be defined in mcp_servers.yaml"

    notion = servers["notion"]
    assert notion.get("default_tier") == "W", "Notion default_tier must be W (reversible writes)"

    # Verify allowlist
    allowlists = cfg.get("allowlists", {})
    assert "notion" in allowlists.get("rex", []), "Notion must be allow-listed for rex"

    # Verify delete / archive tools are Tier A
    tools = notion.get("tools", {})
    assert tools, "Notion tools must be explicitly declared"

    delete_tools = [t for t, p in tools.items() if re.search("delete|archive", t)]
    assert delete_tools, "Must declare at least one delete/archive tool"
    for t in delete_tools:
        assert tools[t].get("tier") == "A", f"Tool {t} deletes/archives data and must be Tier A"


def test_notion_search_and_read_tier_r():
    cfg = load_mcp_config()
    tools = cfg.get("servers", {}).get("notion", {}).get("tools", {})
    read_tools = [t for t, p in tools.items() if re.search("search|retrieve|get|fetch", t)]
    assert read_tools, "Must have read/search tools defined"
    for t in read_tools:
        assert tools[t].get("tier") == "R", f"Tool {t} should be read-only (Tier R)"
