import re
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[3]


def load_mcp_config():
    p = REPO_ROOT / "infra" / "mcp_servers.yaml"
    return yaml.safe_load(p.read_text()) or {}


def test_slack_server_config():
    cfg = load_mcp_config()
    servers = cfg.get("servers", {})
    assert "slack" in servers, "Slack server must be defined in mcp_servers.yaml"

    slack = servers["slack"]
    assert slack.get("default_tier") == "A", "Slack default_tier must be A (strictest)"

    # Verify allowlist
    allowlists = cfg.get("allowlists", {})
    assert "slack" in allowlists.get("rex", []), "Slack must be allow-listed for rex"

    # Verify all post/send/reply tools are Tier A
    tools = slack.get("tools", {})
    assert tools, "Slack tools must be explicitly declared"

    post_tools = [t for t, p in tools.items() if re.search("post|send|reply", t)]
    assert post_tools, "Must declare at least one post/send/reply tool"
    for t in post_tools:
        assert tools[t].get("tier") == "A", f"Tool {t} reaches others and must be Tier A"


def test_slack_read_tools_tier_r():
    cfg = load_mcp_config()
    tools = cfg.get("servers", {}).get("slack", {}).get("tools", {})
    read_tools = [t for t, p in tools.items() if re.search(r"^(list|get|read)_|_history$", t)]
    assert read_tools, "Must have read tools defined"
    for t in read_tools:
        assert tools[t].get("tier") == "R", f"Tool {t} should be read-only (Tier R)"
