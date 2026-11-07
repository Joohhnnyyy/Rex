"""Mac apps and windows through the accessibility tree (vercel-labs/agent-desktop), not screenshots.

Rex gets one tool, `use_desktop`, instead of agent-desktop's 67: it looks at an app as a short list of
elements (`e7 button "Send"`), acts on an element by its ref, and looks again to check. Every call goes
through the MCP gateway's `desktop` server, so tiers and timeline events still apply. Snapshots hold
private desktop content: they go to the LLM as untrusted data and are never logged.
"""

from __future__ import annotations

import json
from typing import Any

from rex_mcp_gateway.gateway import Gateway, NeedsApproval, wrap_untrusted

SPECIALIST = "screen"  # the gateway allowlist that may use the desktop server (Rex itself doesn't see its 67 tools)
ACTIONS = ("windows", "open", "focus", "look", "click", "type", "press", "scroll")
MAX_LINES = 160
MAX_TEXT = 90


def flatten(tree: dict, find: str = "") -> list[str]:
    """One line per element worth knowing: refs for what can be acted on, text for what can be read."""
    lines: list[str] = []
    needle = find.lower().strip()

    def walk(node: dict) -> None:
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
        for child in node.get("children") or []:
            walk(child)

    walk(tree)
    return lines


def _envelope(raw: Any) -> dict:
    text = "\n".join(getattr(c, "text", "") for c in getattr(raw, "content", []) if getattr(c, "text", None))
    try:
        return json.loads(text)
    except ValueError:
        return {"ok": False, "error": {"message": text[:300]}}


class Desktop:
    def __init__(self, gw: Gateway) -> None:
        self.gw = gw
        self.snapshot_id = ""  # refs from the last look; actions take the short "e7" form

    async def _run(self, tool: str, args: dict, summary: str) -> dict:
        out = await self.gw.call(SPECIALIST, f"desktop.desktop_{tool}", args, summary=summary)
        if isinstance(out, NeedsApproval):
            return {"ok": False, "error": {"message": f"needs approval ({out.action_id})"}}
        if not out.ok:
            return {"ok": False, "error": {"message": out.text[:300]}}
        return _envelope(out.raw)

    def _ref(self, ref: str) -> str:
        ref = ref.strip()
        if ref.startswith("@"):
            return ref
        return f"@{self.snapshot_id}:{ref.lstrip('@')}" if self.snapshot_id else ref

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
    ) -> str:
        if action not in ACTIONS:
            return f"Unknown action {action!r}. Use one of: {', '.join(ACTIONS)}."
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
            return f"{app} is in front." if env.get("ok") else _error(env)
        if action == "look":
            env = await self._run("snapshot", {"app": app, "compact": True}, f"look at {app}")
            if not env.get("ok"):
                return _error(env)
            data = env.get("data") or {}
            self.snapshot_id = data.get("snapshot_id", "")
            lines = flatten(data.get("tree") or {}, find)
            more = len(lines) - MAX_LINES
            body = "\n".join(lines[:MAX_LINES]) + (
                f"\n… {more} more; look again with find='…' to narrow" if more > 0 else ""
            )
            return wrap_untrusted(f"desktop.look {app}", body or "(nothing readable; try another app name)")
        if action == "click":
            env = await self._run("click", {"ref_id": self._ref(ref)}, f"click {ref} in {app or 'the app'}")
            return "Clicked. Look again to check the result." if env.get("ok") else _error(env)
        if action == "type":
            target = {"app": app} if app else {}
            if "\n" in text:
                # Typing a newline presses Return, which sends a chat message early; paste multi-line text.
                steps = [
                    ("click", {"ref_id": self._ref(ref)}, f"click {ref}"),
                    ("clipboard_set", {"text": text}, "copy the message"),
                    ("press", {"combo": "cmd+v", **target}, f"paste into {ref}: {text[:60]}"),
                ]
                for tool, args, summary in steps:
                    env = await self._run(tool, args, summary)
                    if not env.get("ok"):
                        return _error(env)
            else:
                env = await self._run("type", {"ref_id": self._ref(ref), "text": text}, f"type into {ref}: {text[:60]}")
                if not env.get("ok"):
                    return _error(env)
            if submit:
                env = await self._run("press", {"combo": "return", **target}, "press Return")
                if not env.get("ok"):
                    return "Typed it, but pressing Return failed: " + _error(env)
            return "Typed" + (" and pressed Return." if submit else ".") + " Look again to check."
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
    code = err.get("code", "")
    msg = err.get("message", "") or json.dumps(err)[:200]
    if code in ("STALE_REF", "AMBIGUOUS_TARGET"):
        return f"{code}: the app changed since the last look. Look again and use the new refs."
    if code == "PERM_DENIED" or "accessibility" in msg.lower():
        return "Accessibility permission is missing for the app running Rex (System Settings > Privacy & Security)."
    return f"That didn't work: {code} {msg}".strip()
