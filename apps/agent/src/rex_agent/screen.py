"""Let Rex look at the user's shared screen.

The dashboard's "Share screen" button publishes a screen-share track into the room. We keep only the
latest decoded frame (nothing is stored or sent anywhere) and, when the user asks, encode that one frame
as JPEG and ask the vision model about it.
"""

from __future__ import annotations

import asyncio
import base64
import ctypes
import json
import logging
import re
import sys
from typing import Any

from livekit import rtc
from livekit.agents.utils import images

from rex_llm_router.client import LLMClient
from rex_mcp_gateway.gateway import wrap_untrusted

logger = logging.getLogger("rex.screen")

NOT_SHARING = "The user is not sharing their screen. Ask them to press 'Share screen' on the dashboard, then try again."
VISION_PROMPT = (
    "You are looking at a screenshot of the user's screen for a voice assistant. Answer the question about it "
    "in at most three short sentences that can be spoken aloud: no markdown, no URLs. Quote on-screen text only "
    "when it matters (an error message, a number, a name). If something is unreadable, say so."
)


class ScreenWatcher:
    """Tracks the newest frame of any screen share in the room."""

    def __init__(self) -> None:
        self.frame: rtc.VideoFrame | None = None
        self._task: asyncio.Task | None = None

    def attach(self, room: rtc.Room) -> None:
        room.on("track_subscribed", self._on_subscribed)
        room.on("track_unsubscribed", self._on_unsubscribed)

    def _on_subscribed(self, track: rtc.Track, pub: rtc.RemoteTrackPublication, _p: rtc.RemoteParticipant) -> None:
        if pub.source == rtc.TrackSource.SOURCE_SCREENSHARE and track.kind == rtc.TrackKind.KIND_VIDEO:
            if self._task:
                self._task.cancel()
            self._task = asyncio.create_task(self._read(track))

    def _on_unsubscribed(self, _t: rtc.Track, pub: rtc.RemoteTrackPublication, _p: rtc.RemoteParticipant) -> None:
        if pub.source == rtc.TrackSource.SOURCE_SCREENSHARE:
            if self._task:
                self._task.cancel()
                self._task = None
            self.frame = None

    async def _read(self, track: rtc.Track) -> None:
        logger.info("screen share started")
        async for ev in rtc.VideoStream(track):
            self.frame = ev.frame  # ponytail: decodes every frame to keep one; sample if CPU becomes an issue

    def jpeg(self) -> bytes | None:
        if self.frame is None:
            return None
        opts = images.EncodeOptions(
            format="JPEG",
            quality=75,
            resize_options=images.ResizeOptions(width=1600, height=1000, strategy="scale_aspect_fit"),
        )
        return images.encode(self.frame, opts)


async def describe_screen(jpeg: bytes, question: str, llm: LLMClient | None = None) -> str:
    """Ask the vision model about one screenshot; the answer is wrapped as untrusted data."""
    url = "data:image/jpeg;base64," + base64.b64encode(jpeg).decode()
    out = await (llm or LLMClient()).complete(
        "vision",
        [
            {"role": "system", "content": VISION_PROMPT},
            {
                "role": "user",
                "content": [{"type": "text", "text": question}, {"type": "image_url", "image_url": {"url": url}}],
            },
        ],
        reasoning_effort="none",  # Gemini: thinking off, this is a quick look
    )
    return wrap_untrusted("screen.look", out.text.strip())


# --- Acting on the screen (click / scroll / drag) ---------------------------------------------------------

LOCATE_PROMPT = (
    "You are given a screenshot of a computer screen. Find the single UI element the user describes. Reply with "
    'JSON only: {"found": true, "point": [y, x], "label": "<what you found>"} where y and x are the centre of '
    'the element on a 0-1000 scale (0,0 = top-left), or {"found": false, "reason": "<short reason>"}.'
)
ACTIONS = ("click", "double_click", "right_click", "scroll", "drag", "type", "press")
_KEY_ALIASES = {"cmd": "command", "control": "ctrl", "opt": "option", "alt": "option", "return": "enter"}


async def locate(jpeg: bytes, target: str, llm: LLMClient | None = None) -> tuple[float, float, str] | str:
    """Where `target` is, as (x, y) fractions of the screen plus a label, or a reason it wasn't found."""
    url = "data:image/jpeg;base64," + base64.b64encode(jpeg).decode()
    out = await (llm or LLMClient()).complete(
        "vision",
        [
            {"role": "system", "content": LOCATE_PROMPT},
            {
                "role": "user",
                "content": [{"type": "text", "text": target}, {"type": "image_url", "image_url": {"url": url}}],
            },
        ],
        reasoning_effort="none",
        response_format={"type": "json_object"},
    )
    found = parse_point(out.text, target)
    if isinstance(found, str) and found.startswith("unreadable"):
        logger.warning("locate %r: unreadable vision answer: %.300s", target, out.text)
        return "the vision model gave an unreadable answer"
    return found


def parse_point(text: str, target: str) -> tuple[float, float, str] | str:
    """Read the vision model's answer. Accepts {"point": [y, x]}, {"box_2d": [y0, x0, y1, x1]}, {"x":, "y":},
    a list wrapping the object, code fences or extra prose around the JSON. Coordinates are on a 0-1000 scale."""
    m = re.search(r"[\[{].*[\]}]", text, re.S)
    try:
        data = json.loads(m.group(0)) if m else None
    except ValueError:
        data = None
    if isinstance(data, list) and data and isinstance(data[0], dict):
        data = data[0]
    if not isinstance(data, dict):
        return "unreadable"
    if data.get("found") is False:
        return str(data.get("reason") or "not visible on the screen")
    label = str(data.get("label") or target)
    pt, box = data.get("point"), data.get("box_2d") or data.get("box")
    try:
        if isinstance(pt, dict):
            y, x = float(pt["y"]), float(pt["x"])
        elif isinstance(pt, (list, tuple)) and len(pt) >= 2:  # seen live: [962, 497, "<label>"]
            y, x = float(pt[0]), float(pt[1])
        elif isinstance(box, (list, tuple)) and len(box) == 4:
            y, x = (float(box[0]) + float(box[2])) / 2, (float(box[1]) + float(box[3])) / 2
        elif "x" in data and "y" in data:
            y, x = float(data["y"]), float(data["x"])
        else:
            return "unreadable"
    except (TypeError, ValueError, KeyError):
        return "unreadable"
    if max(x, y) <= 1.0:  # some answers come back as 0-1 fractions
        x, y = x * 1000, y * 1000
    return min(max(x / 1000, 0.0), 1.0), min(max(y / 1000, 0.0), 1.0), label


def accessibility_allowed() -> bool:
    """macOS silently drops synthetic mouse events unless the host app has Accessibility permission."""
    if sys.platform != "darwin":
        return True
    try:
        lib = ctypes.cdll.LoadLibrary("/System/Library/Frameworks/ApplicationServices.framework/ApplicationServices")
        lib.AXIsProcessTrusted.restype = ctypes.c_bool
        return bool(lib.AXIsProcessTrusted())
    except OSError:
        return True  # can't tell; let pyautogui try


def type_text(mouse: Any, text: str) -> None:
    """Type text into the focused field. Non-ASCII (Hindi, emoji) goes via the clipboard, which pyautogui can't type."""
    if text.isascii():
        mouse.write(text, interval=0.01)
        return
    import subprocess

    subprocess.run(["pbcopy"], input=text.encode(), check=True)  # ponytail: replaces the user's clipboard
    mouse.hotkey("command", "v")


def _mouse():
    import pyautogui

    pyautogui.FAILSAFE = True  # slam the pointer into a screen corner to abort
    return pyautogui


async def control_screen(
    watcher: ScreenWatcher,
    action: str,
    target: str = "",
    to_target: str = "",
    direction: str = "down",
    amount: int = 5,
    text: str = "",
    submit: bool = False,
    keys: str = "",
    llm: LLMClient | None = None,
    mouse: Any = None,
) -> tuple[bool, str]:
    """Do one mouse/keyboard action on the user's real screen. Returns (ok, sentence for the model).

    type: clicks `target` first if given, types `text`, then presses Enter if `submit`.
    press: a key or combo such as "enter", "esc", "cmd+a".
    """
    if action not in ACTIONS:
        return False, f"Unknown action {action!r}; use one of {', '.join(ACTIONS)}."
    if watcher.frame is None:
        return False, NOT_SHARING
    real_mouse = mouse is None
    mouse = mouse or _mouse()
    sw, sh = mouse.size()
    fw, fh = watcher.frame.width, watcher.frame.height
    if abs(fw / fh - sw / sh) > 0.03:
        return False, (
            "The shared view is a window or tab, not the whole screen, so positions can't be mapped. Ask the user "
            "to stop sharing and share their entire screen."
        )
    if real_mouse and not accessibility_allowed():
        return False, (
            "macOS is blocking mouse control. The user must allow it in System Settings, Privacy and Security, "
            "Accessibility, for the app running Rex's agent, then restart the agent."
        )
    jpeg = watcher.jpeg()

    async def point(what: str) -> tuple[float, float, str] | str:
        found = await locate(jpeg, what, llm)
        if isinstance(found, str):
            return f"Couldn't find {what!r}: {found}."
        x, y, label = found
        return x * sw, y * sh, label

    if action == "press":
        combo = [_KEY_ALIASES.get(k.strip().lower(), k.strip().lower()) for k in keys.split("+") if k.strip()]
        if not combo:
            return False, "Say which key to press, e.g. enter, esc or cmd+a."
        await asyncio.to_thread(mouse.hotkey, *combo)
        return True, f"Pressed {keys}."

    if action == "type":
        if not text:
            return False, "Nothing to type: pass the text."
        where = ""
        if target:
            p = await point(target)
            if isinstance(p, str):
                return False, p
            await asyncio.to_thread(mouse.click, p[0], p[1])
            await asyncio.sleep(0.3)  # let the field take focus
            where = f" into {p[2]}"
        await asyncio.to_thread(type_text, mouse, text)
        if submit:
            await asyncio.to_thread(mouse.press, "enter")
        return True, f"Typed{where}" + (" and pressed Enter." if submit else ".")

    if action == "scroll":
        if target:
            p = await point(target)
            if isinstance(p, str):
                return False, p
            await asyncio.to_thread(mouse.moveTo, p[0], p[1], duration=0.2)
        steps = max(1, min(int(amount), 20)) * 3
        if direction in ("up", "down"):
            await asyncio.to_thread(mouse.scroll, steps if direction == "up" else -steps)
        else:
            await asyncio.to_thread(mouse.hscroll, steps if direction == "right" else -steps)
        return True, f"Scrolled {direction}."

    p = await point(target)
    if isinstance(p, str):
        return False, p
    x, y, label = p
    if action == "drag":
        q = await point(to_target)
        if isinstance(q, str):
            return False, q
        await asyncio.to_thread(mouse.moveTo, x, y, duration=0.2)
        await asyncio.to_thread(mouse.dragTo, q[0], q[1], duration=0.6, button="left")
        return True, f"Dragged {label} to {q[2]}."
    await asyncio.to_thread(
        mouse.click,
        x,
        y,
        clicks=2 if action == "double_click" else 1,
        button="right" if action == "right_click" else "left",
    )
    return True, f"{action.replace('_', ' ').capitalize()}ed {label}."
