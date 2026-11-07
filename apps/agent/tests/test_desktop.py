"""use_desktop: snapshots become short ref lines, short refs expand, errors explain the fix."""

from __future__ import annotations

import json

import pytest

from rex_agent.desktop import Desktop, flatten
from rex_mcp_gateway.gateway import ToolOutcome

TREE = {
    "role": "window",
    "name": "WhatsApp",
    "children": [
        {"role": "button", "name": "Asmi", "ref_id": "@s1:e4", "available_actions": ["Click"]},
        {"role": "statictext", "name": "are you   awake?"},
        {"role": "textfield", "name": "Type a message", "ref_id": "@s1:e9", "value": ""},
        {"role": "group"},
    ],
}


def test_flatten_keeps_refs_and_readable_text_and_filters():
    assert flatten(TREE) == [
        '- window "WhatsApp"',
        'e4 button "Asmi"',
        '- statictext "are you awake?"',
        'e9 textfield "Type a message"',
    ]
    assert flatten(TREE, find="message") == ['e9 textfield "Type a message"']


class _Content:
    def __init__(self, text):
        self.text = text


class _Raw:
    def __init__(self, env):
        self.content = [_Content(json.dumps(env))]


class FakeGateway:
    def __init__(self, replies):
        self.replies, self.calls = replies, []

    async def call(self, specialist, tool, args, summary=None):
        self.calls.append((specialist, tool, args))
        env = self.replies.get(tool, {"ok": True, "data": {}})
        return ToolOutcome(ok=True, text="(wrapped)", raw=_Raw(env))


@pytest.mark.asyncio
async def test_look_then_click_and_type_with_short_refs():
    gw = FakeGateway({"desktop.desktop_snapshot": {"ok": True, "data": {"snapshot_id": "s1", "tree": TREE}}})
    d = Desktop(gw)

    seen = await d.run("look", app="WhatsApp")
    assert 'e4 button "Asmi"' in seen and "<untrusted_data" in seen
    assert gw.calls[0] == ("screen", "desktop.desktop_snapshot", {"app": "WhatsApp", "compact": True})

    assert "Clicked" in await d.run("click", ref="e4")
    assert gw.calls[-1][2] == {"ref_id": "@s1:e4"}

    out = await d.run("type", app="WhatsApp", ref="e9", text="are you awake", submit=True)
    assert "pressed Return" in out
    assert gw.calls[-2][1:] == ("desktop.desktop_type", {"ref_id": "@s1:e9", "text": "are you awake"})
    assert gw.calls[-1][1:] == ("desktop.desktop_press", {"combo": "return", "app": "WhatsApp"})


@pytest.mark.asyncio
async def test_guards_and_stale_ref_message():
    gw = FakeGateway({"desktop.desktop_click": {"ok": False, "error": {"code": "STALE_REF", "message": "gone"}}})
    d = Desktop(gw)
    assert "needs a ref" in await d.run("click")
    assert "needs the app name" in await d.run("look")
    assert "Unknown action" in await d.run("teleport")
    assert "Look again" in await d.run("click", ref="@s9:e1")


@pytest.mark.asyncio
async def test_multiline_text_is_pasted_not_typed():
    gw = FakeGateway({})
    d = Desktop(gw)
    d.snapshot_id = "s1"
    out = await d.run("type", app="WhatsApp", ref="e9", text="Sites:\n- TeePublic\n- Redbubble", submit=True)
    assert "pressed Return" in out
    assert [c[1] for c in gw.calls] == [
        "desktop.desktop_click",
        "desktop.desktop_clipboard_set",
        "desktop.desktop_press",
        "desktop.desktop_press",
    ]
    assert gw.calls[1][2] == {"text": "Sites:\n- TeePublic\n- Redbubble"}
    assert gw.calls[2][2] == {"combo": "cmd+v", "app": "WhatsApp"}
