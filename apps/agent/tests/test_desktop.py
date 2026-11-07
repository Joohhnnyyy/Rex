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
    assert gw.calls[-2][1:] == ("desktop.desktop_set_value", {"ref_id": "@s1:e9", "value": "are you awake"})
    assert gw.calls[-1][1:] == ("desktop.desktop_press", {"combo": "return", "app": "WhatsApp"})


@pytest.mark.asyncio
async def test_guards_and_stale_ref_message():
    gw = FakeGateway({"desktop.desktop_click": {"ok": False, "error": {"code": "STALE_REF", "message": "gone"}}})
    d = Desktop(gw)
    assert "needs a ref" in await d.run("click")
    assert "needs the app name" in await d.run("look")
    assert "Unknown action" in await d.run("teleport")
    assert "Look again" in await d.run("click", ref="@s9:e1")


def _snap(title, sent="", compose=True, results=()):
    kids = [{"role": "group", "name": f"\u200eMessages in chat with {title}", "children": []}]
    kids.append({"role": "button", "name": title, "ref_id": "@s2:e70", "available_actions": ["Click"]})  # header
    for i, name in enumerate(results):
        kids.append({"role": "button", "name": name, "ref_id": f"@s2:e{22 + i}", "available_actions": ["Click"]})
    if sent:
        kids[0]["children"].append({"role": "statictext", "name": f"\u200eYour message, {sent}, 4 Nov"})
    if compose:
        kids.append({"role": "textfield", "name": "\u200eCompose message", "ref_id": "@s2:e72"})
    kids.append({"role": "textfield", "name": "\u200eSearch", "ref_id": "@s2:e16"})
    return {"ok": True, "data": {"snapshot_id": "s2", "tree": {"role": "window", "children": kids}}}


class ScriptedGateway(FakeGateway):
    """Replies to snapshots in order; every other tool succeeds."""

    def __init__(self, snaps, fail=None):
        super().__init__({})
        self.snaps, self.fail = list(snaps), fail or {}

    async def call(self, specialist, tool, args, summary=None):
        self.calls.append((specialist, tool, args))
        if tool in self.fail:
            return ToolOutcome(ok=False, text="The tool failed: " + json.dumps(self.fail[tool]))
        env = self.snaps.pop(0) if tool == "desktop.desktop_snapshot" else {"ok": True, "data": {}}
        return ToolOutcome(ok=True, text="(wrapped)", raw=_Raw(env))


@pytest.mark.asyncio
async def test_send_clicks_the_matching_result_not_the_top_one(monkeypatch):
    monkeypatch.setattr("rex_agent.desktop.SETTLE_S", 0)
    text = "Top 5 flights:\n- IndiGo 6E 2034 Rs 5,800\n- Air India Rs 6,100"
    gw = ScriptedGateway(
        [
            _snap("Sunday ki paneer"),  # another chat is open, no Shanky in the visible list
            _snap("Sunday ki paneer", results=["Sunday ki paneer group", "Shankyy", "From Shankyy"]),
            _snap("Shankyy"),
            _snap("Shankyy", sent="Top 5 flights: - IndiGo"),
        ]
    )
    out = await Desktop(gw).run("send", app="WhatsApp", to="Shanky", text=text)
    assert out.startswith("SENT and verified") and "Shankyy" in out
    tools = [c[1].removeprefix("desktop.desktop_") for c in gw.calls]
    # escape, click the search box, select all, copy + paste the name, look, click the matching result
    assert tools == ["snapshot", "press", "click", "press", "clipboard_set", "press", "snapshot", "click",
                     "snapshot", "set_value", "press", "snapshot"]  # fmt: skip
    assert gw.calls[2][2] == {"ref_id": "@s2:e16"}
    assert gw.calls[4][2] == {"text": "Shanky"}
    assert gw.calls[7][2] == {"ref_id": "@s2:e23"}  # "Shankyy", not the group listed first
    assert gw.calls[9][2] == {"ref_id": "@s2:e72", "value": text}  # one message, line breaks kept


@pytest.mark.asyncio
async def test_send_uses_the_chat_list_when_the_contact_is_visible(monkeypatch):
    monkeypatch.setattr("rex_agent.desktop.SETTLE_S", 0)
    gw = ScriptedGateway(
        [_snap("Sunday ki paneer", results=["Shankyy"]), _snap("Shankyy"), _snap("Shankyy", sent="hi there")]
    )
    assert (await Desktop(gw).run("send", app="WhatsApp", to="shanky", text="hi there")).startswith("SENT")
    assert [c[1].removeprefix("desktop.desktop_") for c in gw.calls][:2] == ["snapshot", "click"]


@pytest.mark.asyncio
async def test_send_refuses_the_wrong_chat_and_reports_unverified(monkeypatch):
    monkeypatch.setattr("rex_agent.desktop.SETTLE_S", 0)
    gw = ScriptedGateway([_snap("Sunday ki paneer"), _snap("Sunday ki paneer")])
    out = await Desktop(gw).run("send", app="WhatsApp", to="Shanky", text="hi")
    assert out.startswith("NOT SENT") and "no chat named 'Shanky'" in out
    assert "desktop.desktop_set_value" not in [c[1] for c in gw.calls]

    # The click lands in the wrong chat: stop before writing anything.
    gw = ScriptedGateway([_snap("Work", results=["Shankyy"]), _snap("Sunday ki paneer")])
    out = await Desktop(gw).run("send", app="WhatsApp", to="Shanky", text="hi")
    assert out.startswith("NOT SENT") and "Sunday ki paneer" in out
    assert "desktop.desktop_set_value" not in [c[1] for c in gw.calls]

    gw = ScriptedGateway([_snap("Shankyy"), _snap("Shankyy", sent="something older")])
    assert (await Desktop(gw).run("send", app="WhatsApp", to="Shanky", text="hi there")).startswith("UNVERIFIED")


@pytest.mark.asyncio
async def test_closed_window_is_reopened_and_error_codes_survive(monkeypatch):
    monkeypatch.setattr("rex_agent.desktop.SETTLE_S", 0)
    closed = {"ok": False, "error": {"code": "WINDOW_NOT_FOUND", "message": "no matching window"}}

    class Gw(ScriptedGateway):
        async def call(self, specialist, tool, args, summary=None):
            if tool == "desktop.desktop_snapshot" and len([c for c in self.calls if c[1] == tool]) == 0:
                self.calls.append((specialist, tool, args))
                return ToolOutcome(ok=False, text="The tool failed: " + json.dumps(closed))
            return await super().call(specialist, tool, args, summary)

    gw = Gw([_snap("Shankyy")])
    assert "Messages in chat with Shankyy" in await Desktop(gw).run("look", app="WhatsApp")
    assert [c[1] for c in gw.calls] == [
        "desktop.desktop_snapshot",
        "desktop.desktop_launch",
        "desktop.desktop_snapshot",
    ]

    gw = ScriptedGateway([], fail={"desktop.desktop_focus_window": closed, "desktop.desktop_launch": closed})
    assert "no open window" in await Desktop(gw).run("focus", app="WhatsApp")


@pytest.mark.asyncio
async def test_multiline_type_sets_the_value_in_one_go():
    gw = FakeGateway({})
    d = Desktop(gw)
    d.snapshot_id = "s1"
    out = await d.run("type", app="WhatsApp", ref="e9", text="Sites:\n- TeePublic", submit=True)
    assert "pressed Return" in out
    assert [c[1] for c in gw.calls] == ["desktop.desktop_set_value", "desktop.desktop_press"]
