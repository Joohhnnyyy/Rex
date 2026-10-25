from rex_agent.config import AgentConfig
from rex_agent.main import Rex, event_to_json, load_runtime_registry


def _names(agent):
    return {getattr(t, "info", None).name if hasattr(t, "info") else str(t) for t in agent.tools}


def test_rex_exposes_core_tools():
    names = _names(Rex(AgentConfig()))
    assert {"delegate_task", "approve_action", "deny_action", "undo_action"} <= names


async def test_approve_without_gateway_is_graceful():
    agent = Rex(AgentConfig())
    assert await agent.approve_action(None, "x") == "No tools are connected."


async def test_undo_without_gateway_is_graceful():
    agent = Rex(AgentConfig())
    assert await agent.undo_action(None) == "No tools are connected."


def test_runtime_registry_has_location_for_rex():
    reg = load_runtime_registry()
    assert "location" in reg.servers
    assert reg.allowed("rex", "location")
    assert reg.servers["location"].command[1:] == ["-m", "rex_mcp_servers.location"]


def test_event_json_has_type():
    import json
    import uuid
    from datetime import UTC, datetime

    from rex_shared.schemas import ActionEvent

    ev = ActionEvent(
        id=uuid.uuid4(), ts=datetime.now(UTC), tool="location.find_place", tier="R", status="started", summary="find"
    )
    d = json.loads(event_to_json(ev))
    assert d["type"] == "action_event" and d["tool"] == "location.find_place"
