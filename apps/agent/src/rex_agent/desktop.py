"""Mac apps and windows through the accessibility tree (vercel-labs/agent-desktop), not screenshots.

Rex gets one tool, `use_desktop`, instead of agent-desktop's 67: it looks at an app as a short list of
elements (`e7 button "Send"`), acts on an element by its ref, and looks again to check. Chat messages use
`send`, which does every step in code and checks the message really landed in the right chat: a voice
model doing those steps one by one picked the wrong chat and reported messages it never sent.

Every call goes through the MCP gateway's `desktop` server, so tiers and timeline events still apply.
Snapshots hold private desktop content: they go to the LLM as untrusted data and are never logged.
"""

from __future__ import annotations

import asyncio
import json
import re
from collections.abc import Iterator
from typing import Any

from rex_mcp_gateway.gateway import Gateway, NeedsApproval, wrap_untrusted

SPECIALIST = "screen"  # the gateway allowlist that may use the desktop server (Rex itself doesn't see its 67 tools)
ACTIONS = ("windows", "open", "focus", "look", "click", "type", "press", "scroll", "send")
MAX_LINES = 160
MAX_TEXT = 90
SETTLE_S = 1.2  # time for a chat app to open a chat or show a sent message


def walk(node: dict) -> Iterator[dict]:
    yield node
    for child in node.get("children") or []:
        yield from walk(child)


def flatten(tree: dict, find: str = "") -> list[str]:
    """One line per element worth knowing: refs for what can be acted on, text for what can be read."""
    lines: list[str] = []
    needle = find.lower().strip()
    for node in walk(tree):
        name = " ".join(str(node.get("name") or "").split())[:MAX_TEXT]
        value = " ".join(str(node.get("value") or "").split())[:MAX_TEXT]
        ref = str(node.get("ref_id") or "")
        if ref or name or value:
            short = ref.rsplit(":", 1)[-1] if ref else "-"
            line = f"{short} {node.get('role', '')}"
            if name:
                line += f' "{name}"'
            if value and value != name:
                line += f" = {value!r}"
            if not needle or needle in line.lower():
                lines.append(line)
    return lines


def norm(text: str) -> str:
    """Compare names and messages without case, spacing, emoji or WhatsApp's invisible direction marks."""
    return re.sub(r"[\W_]+", "", str(text).lower())


def _envelope(raw: Any) -> dict:
    text = "\n".join(getattr(c, "text", "") for c in getattr(raw, "content", []) if getattr(c, "text", None))
    try:
        return json.loads(text)
    except ValueError:
        return {"ok": False, "error": {"message": text[:300]}}


def _failure(text: str) -> dict:
    """The gateway reports a failed tool as 'The tool failed: {json envelope}'; keep its error code."""
    start = text.find("{")
    if start >= 0:
        try:
            env = json.loads(text[start:])
            if isinstance(env, dict) and env.get("error"):
                return {"ok": False, "error": env["error"]}
        except ValueError:
            pass
    return {"ok": False, "error": {"message": text[:300]}}


def chat_title(tree: dict) -> str:
    """The open chat's name, from WhatsApp's "Messages in chat with <name>" group."""
    for node in walk(tree):
        name = str(node.get("name") or "").replace("‎", "").strip()
        if name.lower().startswith("messages in chat with "):
            return name[len("messages in chat with ") :].strip()
    return ""


def chat_button(tree: dict, to: str) -> str:
    """The chat-list or search-result button for `to`: exact name first, then the shortest name starting
    with it ("Shanky" -> "Shankyy"), never the open chat's header, call buttons or "From …" filters."""
    want = norm(to)
    header = chat_title(tree)
    best: tuple[int, str] | None = None
    for node in walk(tree):
        if node.get("role") != "button" or "Click" not in (node.get("available_actions") or []):
            continue
        name = norm(node.get("name") or "")
        if not want or not name.startswith(want) or (header and name == norm(header)):
            continue
        rank = (0 if name == want else 1, len(name))
        if best is None or rank < best[0]:
            best = (rank, str(node.get("ref_id") or ""))
    return best[1] if best else ""


def search_ref(tree: dict) -> str:
    for node in walk(tree):
        if node.get("role") in ("textfield", "searchfield") and norm(node.get("name") or "") == "search":
            return str(node.get("ref_id") or "")
    return ""


def compose_ref(tree: dict) -> str:
    for node in walk(tree):
        if node.get("role") in ("textfield", "textarea") and "compose" in str(node.get("name") or "").lower():
            return str(node.get("ref_id") or "")
    return ""


def last_sent(tree: dict) -> str:
    """Text of the newest message the user sent in the open chat ("Your message, <text>, <time>")."""
    sent = ""
    for node in walk(tree):
        name = str(node.get("name") or "").replace("‎", "").replace("⁠", "")
        if name.startswith("Your message,"):
            sent = name[len("Your message,") :]
    return sent


class Desktop:
    def __init__(self, gw: Gateway) -> None:
        self.gw = gw
        self.snapshot_id = ""  # refs from the last look; actions take the short "e7" form

    async def _run(self, tool: str, args: dict, summary: str) -> dict:
        out = await self.gw.call(SPECIALIST, f"desktop.desktop_{tool}", args, summary=summary)
        if isinstance(out, NeedsApproval):
            return {"ok": False, "error": {"message": f"needs approval ({out.action_id})"}}
        if not out.ok:
            return _failure(out.text)
        return _envelope(out.raw)

    async def _snapshot(self, app: str) -> dict:
        """A snapshot, reopening the app's window first if it was closed (the app keeps running on macOS)."""
        env = await self._run("snapshot", {"app": app, "compact": True}, f"look at {app}")
        if (env.get("error") or {}).get("code") in ("WINDOW_NOT_FOUND", "APP_NOT_FOUND"):
            await self._run("launch", {"app": app, "activate": True}, f"open {app}")
            await asyncio.sleep(SETTLE_S)
            env = await self._run("snapshot", {"app": app, "compact": True}, f"look at {app}")
        if env.get("ok"):
            self.snapshot_id = (env.get("data") or {}).get("snapshot_id", "")
        return env

    def _ref(self, ref: str) -> str:
        ref = ref.strip()
        if ref.startswith("@"):
            return ref
        return f"@{self.snapshot_id}:{ref.lstrip('@')}" if self.snapshot_id else ref

    async def _put_text(self, ref: str, text: str, app: str) -> dict:
        """Put text in a field: set its value, else type it, else click and paste (also keeps line breaks)."""
        env = await self._run("set_value", {"ref_id": ref, "value": text}, f"write into {ref}: {text[:60]}")
        if env.get("ok"):
            return env
        if "\n" not in text:
            env = await self._run("type", {"ref_id": ref, "text": text}, f"type into {ref}: {text[:60]}")
            if env.get("ok"):
                return env
        target = {"app": app} if app else {}
        for tool, args, summary in (
            ("click", {"ref_id": ref}, f"click {ref}"),
            ("clipboard_set", {"text": text}, "copy the text"),
            ("press", {"combo": "cmd+v", **target}, f"paste into {ref}: {text[:60]}"),
        ):
            env = await self._run(tool, args, summary)
            if not env.get("ok"):
                return env
        return env

    async def open_chat(self, app: str, to: str) -> tuple[dict, str]:
        """Make the chat with `to` the open one; returns (tree, problem).

        Clicks the chat whose name matches, from the chat list or else from search results. Pressing Return
        on search results opened the top hit, which for "Shanky" was a group he's in, not his chat."""
        env = await self._snapshot(app)
        if not env.get("ok"):
            return {}, _error(env)
        tree = (env.get("data") or {}).get("tree") or {}
        if norm(to) and norm(to) in norm(chat_title(tree)):
            return tree, ""
        button = chat_button(tree, to)
        if not button:
            # Search: WhatsApp's search box refuses accessibility typing, so click it and paste the name.
            search = search_ref(tree)
            if not search:
                return {}, "couldn't find the chat search box."
            for tool, args, summary in (
                ("press", {"combo": "escape", "app": app}, "close any open search"),
                ("click", {"ref_id": search}, "click the chat search box"),
                ("press", {"combo": "cmd+a", "app": app}, "select the search text"),
                ("clipboard_set", {"text": to}, f"copy {to!r}"),
                ("press", {"combo": "cmd+v", "app": app}, f"search {to!r}"),
            ):
                env = await self._run(tool, args, summary)
                if not env.get("ok"):
                    return {}, "couldn't search for the chat. " + _error(env)
            await asyncio.sleep(SETTLE_S)
            env = await self._snapshot(app)
            tree = (env.get("data") or {}).get("tree") or {}
            button = chat_button(tree, to)
            if not button:
                await self._run("press", {"combo": "escape", "app": app}, "close search")
                return {}, f"no chat named {to!r} in the search results. Ask the user for the exact chat name."
        await self._run("click", {"ref_id": button}, f"open the chat with {to}")
        await asyncio.sleep(SETTLE_S)
        env = await self._snapshot(app)
        tree = (env.get("data") or {}).get("tree") or {}
        title = chat_title(tree)
        if norm(to) in norm(title):
            return tree, ""
        found = f"the open chat is {title!r}" if title else "no chat opened"
        return {}, f"couldn't open a chat named {to!r} ({found}). Ask the user for the exact chat name."

    async def send(self, app: str, to: str, text: str) -> str:
        """Open the chat with `to`, check it's the right one, send `text`, and check it arrived."""
        app = app or "WhatsApp"
        if not to or not text.strip():
            return "NOT SENT: 'send' needs to= (the chat name) and text= (the message)."
        tree, problem = await self.open_chat(app, to)
        if problem:
            return "NOT SENT: " + problem
        title = chat_title(tree)
        box = compose_ref(tree)
        if not box:
            return f"NOT SENT: found the chat {title!r} but not its message box."
        env = await self._put_text(box, text, app)
        if not env.get("ok"):
            return "NOT SENT: couldn't write the message. " + _error(env)
        env = await self._run("press", {"combo": "return", "app": app}, f"send to {title}")
        if not env.get("ok"):
            return "NOT SENT: the message is written but pressing Return failed. " + _error(env)
        await asyncio.sleep(SETTLE_S)
        env = await self._snapshot(app)
        tree = (env.get("data") or {}).get("tree") or {}
        first_line = norm(next((line for line in text.splitlines() if line.strip()), text))[:24]
        if first_line and first_line in norm(last_sent(tree)):
            return f"SENT and verified: it's now the newest message in the chat with {title}."
        return (
            f"UNVERIFIED: pressed Return in the chat with {title}, but the newest message there doesn't match. "
            "Look at the app before telling the user anything, and don't resend blindly."
        )

    async def run(
        self,
        action: str,
        app: str = "",
        ref: str = "",
        text: str = "",
        keys: str = "",
        direction: str = "down",
        amount: int = 3,
        find: str = "",
        submit: bool = False,
        to: str = "",
    ) -> str:
        if action not in ACTIONS:
            return f"Unknown action {action!r}. Use one of: {', '.join(ACTIONS)}."
        if action == "send":
            return await self.send(app, to, text)
        if action in ("click", "type", "scroll") and not ref:
            return f"'{action}' needs a ref from a look, e.g. ref='e7'. Look at the app first."
        if action in ("open", "focus", "look") and not app:
            return f"'{action}' needs the app name, e.g. app='WhatsApp' or app='Google Chrome'."

        if action == "windows":
            env = await self._run("list_windows", {}, "list open windows")
            if not env.get("ok"):
                return _error(env)
            wins = [w for w in env.get("data") or [] if w.get("visible", True) and not w.get("minimized")]
            return wrap_untrusted(
                "desktop.windows", "\n".join(f"{w.get('app_name')}: {w.get('title') or '(untitled)'}" for w in wins)
            )
        if action == "open":
            env = await self._run("launch", {"app": app, "activate": True}, f"open {app}")
            return f"Opened {app}. Look at it to see what's there." if env.get("ok") else _error(env)
        if action == "focus":
            env = await self._run("focus_window", {"app": app}, f"bring {app} to the front")
            if (env.get("error") or {}).get("code") == "WINDOW_NOT_FOUND":
                env = await self._run("launch", {"app": app, "activate": True}, f"open {app}")
            return f"{app} is in front." if env.get("ok") else _error(env)
        if action == "look":
            env = await self._snapshot(app)
            if not env.get("ok"):
                return _error(env)
            lines = flatten((env.get("data") or {}).get("tree") or {}, find)
            more = len(lines) - MAX_LINES
            body = "\n".join(lines[:MAX_LINES]) + (
                f"\n… {more} more; look again with find='…' to narrow" if more > 0 else ""
            )
            return wrap_untrusted(f"desktop.look {app}", body or "(nothing readable; try another app name)")
        if action == "click":
            env = await self._run("click", {"ref_id": self._ref(ref)}, f"click {ref} in {app or 'the app'}")
            return "Clicked. Look again to check the result." if env.get("ok") else _error(env)
        if action == "type":
            env = await self._put_text(self._ref(ref), text, app)
            if not env.get("ok"):
                return _error(env)
            if submit:
                env = await self._run("press", {"combo": "return", **({"app": app} if app else {})}, "press Return")
                if not env.get("ok"):
                    return "Typed it, but pressing Return failed: " + _error(env)
            return "Typed" + (" and pressed Return." if submit else ".") + " Look again to check it worked."
        if action == "press":
            combo = keys or "return"
            env = await self._run("press", {"combo": combo, **({"app": app} if app else {})}, f"press {combo}")
            return f"Pressed {combo}." if env.get("ok") else _error(env)
        # scroll
        env = await self._run(
            "scroll", {"ref_id": self._ref(ref), "direction": direction, "amount": amount}, f"scroll {direction}"
        )
        return "Scrolled. Look again to see the new content." if env.get("ok") else _error(env)


def _error(env: dict) -> str:
    err = env.get("error") or {}
    code = str(err.get("code", ""))
    msg = str(err.get("message", "") or json.dumps(err)[:200])
    if code in ("STALE_REF", "AMBIGUOUS_TARGET"):
        return f"{code}: the app changed since the last look. Look again and use the new refs."
    if code == "WINDOW_NOT_FOUND":
        return "The app has no open window. Use action=open to bring it up, then look again."
    if code in ("PERM_DENIED", "PERMISSION_DENIED", "ACCESSIBILITY_DENIED"):
        return "Accessibility permission is missing for the app running Rex (System Settings > Privacy & Security)."
    return f"That didn't work: {code} {msg}".strip()
