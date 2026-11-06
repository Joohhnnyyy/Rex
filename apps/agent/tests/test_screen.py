"""look_at_screen plumbing: frame -> JPEG -> vision request, answer wrapped as untrusted data."""

from __future__ import annotations

import base64
from types import SimpleNamespace

import pytest
from livekit import rtc

from rex_agent.screen import ScreenWatcher, control_screen, describe_screen, parse_point


def _frame(w: int = 64, h: int = 40) -> rtc.VideoFrame:
    return rtc.VideoFrame(w, h, rtc.VideoBufferType.RGBA, bytes([200, 40, 40, 255]) * (w * h))


def test_watcher_encodes_latest_frame_as_jpeg():
    w = ScreenWatcher()
    assert w.jpeg() is None  # not sharing
    w.frame = _frame()
    assert w.jpeg()[:2] == b"\xff\xd8"


@pytest.mark.asyncio
async def test_describe_screen_sends_image_and_wraps_answer():
    seen = {}

    class FakeLLM:
        async def complete(self, task_kind, messages, **params):
            seen.update(kind=task_kind, messages=messages)
            return SimpleNamespace(text="  The error says file not found.  ")

    out = await describe_screen(b"\xff\xd8jpeg", "What does the error say?", llm=FakeLLM())
    assert seen["kind"] == "vision"
    parts = seen["messages"][1]["content"]
    assert parts[0] == {"type": "text", "text": "What does the error say?"}
    assert parts[1]["image_url"]["url"] == "data:image/jpeg;base64," + base64.b64encode(b"\xff\xd8jpeg").decode()
    assert out.startswith('<untrusted_data source="screen.look">') and "file not found" in out


class FakeMouse:
    def __init__(self, w=1680, h=1050):
        self.w, self.h, self.calls = w, h, []

    def size(self):
        return self.w, self.h

    def __getattr__(self, name):  # click, moveTo, dragTo, scroll, hscroll
        return lambda *a, **k: self.calls.append((name, a, k))


class PointLLM:
    """Answers each locate() with the next queued reply."""

    def __init__(self, *replies):
        self.replies = list(replies)

    async def complete(self, task_kind, messages, **params):
        return SimpleNamespace(text=self.replies.pop(0))


def _sharing(w=1680, h=1050) -> ScreenWatcher:
    s = ScreenWatcher()
    s.frame = _frame(w // 10, h // 10)
    return s


@pytest.mark.asyncio
async def test_click_maps_vision_point_to_screen_points():
    m = FakeMouse()
    llm = PointLLM('{"found": true, "point": [500, 250], "label": "Submit button"}')
    ok, msg = await control_screen(_sharing(), "click", "the Submit button", llm=llm, mouse=m)
    assert ok and msg == "Clicked Submit button."
    assert m.calls == [("click", (420.0, 525.0), {"clicks": 1, "button": "left"})]


@pytest.mark.asyncio
async def test_drag_and_scroll():
    m = FakeMouse()
    llm = PointLLM(
        '{"found": true, "point": [100, 100], "label": "file"}',
        '{"found": true, "point": [900, 900], "label": "Trash"}',
    )
    ok, msg = await control_screen(_sharing(), "drag", "report.pdf", "the Trash", llm=llm, mouse=m)
    assert ok and msg == "Dragged file to Trash."
    assert m.calls[-1] == ("dragTo", (1512.0, 945.0), {"duration": 0.6, "button": "left"})

    ok, _ = await control_screen(_sharing(), "scroll", direction="down", amount=2, mouse=m)
    assert ok and m.calls[-1] == ("scroll", (-6,), {})


@pytest.mark.asyncio
async def test_refuses_window_share_missing_target_and_no_share():
    m = FakeMouse()
    ok, msg = await control_screen(_sharing(800, 800), "click", "x", mouse=m)  # square = a window, not the screen
    assert not ok and "entire screen" in msg
    missing = PointLLM('{"found": false, "reason": "no such button"}')
    ok, msg = await control_screen(_sharing(), "click", "Pay", llm=missing, mouse=m)
    assert not ok and "no such button" in msg
    ok, msg = await control_screen(ScreenWatcher(), "click", "x", mouse=m)
    assert not ok and "not sharing" in msg
    assert m.calls == []  # nothing was clicked


@pytest.mark.asyncio
async def test_type_into_target_and_send_in_one_call():
    m = FakeMouse()
    llm = PointLLM('{"found": true, "point": [950, 500], "label": "message box"}')
    ok, msg = await control_screen(
        _sharing(), "type", "the message box", text="are you awake?", submit=True, llm=llm, mouse=m
    )
    assert ok and msg == "Typed into message box and pressed Enter."
    assert [c[0] for c in m.calls] == ["click", "write", "press"]
    assert m.calls[1] == ("write", ("are you awake?",), {"interval": 0.01})
    assert m.calls[2] == ("press", ("enter",), {})


@pytest.mark.asyncio
async def test_press_maps_key_names():
    m = FakeMouse()
    ok, msg = await control_screen(_sharing(), "press", keys="cmd+a", mouse=m)
    assert ok and m.calls == [("hotkey", ("command", "a"), {})]
    ok, msg = await control_screen(_sharing(), "type", mouse=m)  # nothing to type
    assert not ok


@pytest.mark.parametrize(
    "answer",
    [
        '{"found": true, "point": [900, 500], "label": "box"}',
        '```json\n{"found": true, "point": [900, 500]}\n```',
        '[{"found": true, "point": [900, 500]}]',
        '{"found": true, "box_2d": [880, 300, 920, 700]}',
        '{"found": true, "point": {"y": 900, "x": 500}}',
        'Here it is: {"x": 500, "y": 900}',
        '{"found": true, "point": [0.9, 0.5]}',
        '{"found": true, "point": [900, 500, "the message box in Asmi\'s chat"] }',  # real Gemini answer
    ],
)
def test_parse_point_accepts_common_answer_shapes(answer):
    x, y, _ = parse_point(answer, "the message box")
    assert (round(x, 3), round(y, 3)) == (0.5, 0.9)


def test_parse_point_not_found_and_garbage():
    assert parse_point('{"found": false, "reason": "no box"}', "x") == "no box"
    assert parse_point("I can't tell", "x") == "unreadable"


def test_clean_screen_args_normalises_llm_noise():
    from rex_agent.main import _clean_screen_args

    a = _clean_screen_args("Type a message", "none", "none", "none", None, "true", "null")
    assert a == {
        "target": "Type a message",
        "to_target": "",
        "direction": "down",
        "amount": 5,
        "text": "",
        "submit": True,
        "keys": "",
    }
