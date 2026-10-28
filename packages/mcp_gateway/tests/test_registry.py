from rex_mcp_gateway.registry import load_registry


def test_load_registry_from_yaml_expands_env(tmp_path):
    p = tmp_path / "servers.yaml"
    p.write_text(
        """
servers:
  location:
    command: ["python", "-m", "rex_mcp_servers.location"]
    env: {UA: "${REX_UA}"}
    default_tier: R
  slack:
    command: ["npx", "-y", "slack"]
    tools:
      post_message: {tier: A}
allowlists:
  rex: [location, slack]
"""
    )
    reg = load_registry(p, env={"REX_UA": "rex-test"})
    assert reg.servers["location"].env == {"UA": "rex-test"}
    assert reg.tier_for("location", "find_place") == "R"
    assert reg.tier_for("slack", "post_message") == "A"
    assert reg.tier_for("slack", "unknown_tool") == "A"  # unknown -> strictest
    assert reg.allowlists["rex"] == {"location", "slack"}


def test_enabled_flag_skips_server(tmp_path):
    p = tmp_path / "s.yaml"
    p.write_text("servers:\n  disabled_srv: {command: [x], enabled: false}\n  live_srv: {command: [y]}\n")
    reg = load_registry(p, env={})
    assert list(reg.servers) == ["live_srv"]


def test_tool_subsets_limit_a_specialist_per_server(tmp_path):
    p = tmp_path / "s.yaml"
    p.write_text(
        "servers:\n  notion: {command: [x]}\n  slack: {command: [y]}\n"
        "allowlists:\n  rex: [notion, slack]\n  meeting: [notion]\n"
        "tool_subsets:\n  rex:\n    notion: [search, create_page]\n"
    )
    reg = load_registry(p, env={})
    assert reg.exposes("rex", "notion", "search")
    assert not reg.exposes("rex", "notion", "delete_block")
    assert reg.exposes("rex", "slack", "anything")  # no subset -> all tools
    assert reg.exposes("meeting", "notion", "delete_block")
