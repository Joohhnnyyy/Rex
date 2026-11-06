"""Browser MCP server (T-38): a real Chromium driven by Playwright.

Tiers (infra/mcp_servers.yaml):
- R: navigate, read_page
- W: fill_form
- A: click, submit_form (can buy, book or send, so always asks first)

The window is visible by default so the user can watch Rex browse; set
REX_BROWSER_HEADLESS=1 for tests/CI. The profile persists in
~/.config/rex/browser-profile, so sign-ins the user does there stick.

Pages can contain text aimed at the model, and a model-chosen URL can point at the
user's own machine or LAN. So only http(s) to public addresses is allowed, unless
REX_BROWSER_ALLOW_LOCAL=1 (tests, local demos).
"""

from __future__ import annotations

import argparse
import asyncio
import ipaddress
import json
import logging
import os
import socket
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError

logger = logging.getLogger("rex.mcp.browser")

MAX_TEXT = 3000  # chars of page text sent back to the LLM
# Live view for the dashboard: the newest JPEG of the page plus {url, title, ts}. The agent (our parent
# process, same machine) watches this folder and streams frames into the LiveKit room.
LIVE_DIR = Path(os.environ.get("REX_BROWSER_LIVE_DIR", Path.home() / ".config" / "rex" / "browser-live"))
LIVE_INTERVAL_S = 1.0
MAX_LINKS = 25
NAV_TIMEOUT_MS = 20_000


def check_url(url: str, allow_local: bool | None = None) -> str:
    """Return a normalised URL or raise ToolError if Rex may not open it."""
    if allow_local is None:
        allow_local = os.environ.get("REX_BROWSER_ALLOW_LOCAL") == "1"
    if "://" not in url:
        url = "https://" + url
    p = urlparse(url)
    if p.scheme not in ("http", "https") or not p.hostname:
        raise ToolError(f"Only http(s) web pages can be opened, not {url!r}.")
    if allow_local:
        return url
    try:
        infos = socket.getaddrinfo(p.hostname, None)
    except socket.gaierror as e:
        raise ToolError(f"Could not find the site {p.hostname}.") from e
    for info in infos:
        ip = ipaddress.ip_address(info[4][0])
        if not ip.is_global:
            raise ToolError(f"{p.hostname} is a private or local address; Rex only opens public sites.")
    # ponytail: checks DNS once before loading; a rebinding site or a redirect to a LAN host
    # is not re-checked. Add a page.route() guard if the browser ever runs on a shared network.
    return url


# Runs in the page: visible text, links and form fields, all trimmed for the LLM.
SNAPSHOT_JS = """([maxText, maxLinks]) => {
  const vis = (el) => !!(el.offsetWidth || el.offsetHeight || el.getClientRects().length);
  const text = (document.body?.innerText || '').replace(/\\n{3,}/g, '\\n\\n').trim().slice(0, maxText);
  const links = [...document.querySelectorAll('a[href]')]
    .filter((a) => vis(a) && a.innerText.trim() && a.href.startsWith('http'))
    .slice(0, maxLinks)
    .map((a) => ({ text: a.innerText.trim().slice(0, 80), url: a.href }));
  const label = (el) =>
    (el.labels && el.labels[0]?.innerText.trim()) || el.getAttribute('aria-label') ||
    el.placeholder || el.name || el.id || '';
  const fields = [...document.querySelectorAll('input, textarea, select')]
    .filter((el) => vis(el) && !['hidden', 'submit', 'button'].includes(el.type))
    .map((el) => ({ field: label(el), type: el.type || el.tagName.toLowerCase() }))
    .filter((f) => f.field);
  const buttons = [...document.querySelectorAll('button, input[type=submit]')]
    .filter(vis).map((b) => (b.innerText || b.value || '').trim()).filter(Boolean).slice(0, 15);
  return { text, links, fields, buttons };
}"""


class Browser:
    """One Chromium window shared by every tool call; started on first use."""

    def __init__(self, headless: bool | None = None, profile_dir: Path | None = None) -> None:
        self.headless = os.environ.get("REX_BROWSER_HEADLESS") == "1" if headless is None else headless
        self.profile_dir = profile_dir or Path.home() / ".config" / "rex" / "browser-profile"
        self._pw: Any = None
        self._ctx: Any = None
        self._lock = asyncio.Lock()  # one action at a time on the one page
        self._last_field: Any = None
        self._live_task: asyncio.Task | None = None
        self.live_dir = LIVE_DIR

    async def page(self) -> Any:
        if self._ctx is None:
            from playwright.async_api import async_playwright

            self._pw = await async_playwright().start()
            self.profile_dir.mkdir(parents=True, exist_ok=True)
            self._ctx = await self._pw.chromium.launch_persistent_context(
                str(self.profile_dir), headless=self.headless, viewport={"width": 1280, "height": 800}
            )
            self._ctx.set_default_timeout(NAV_TIMEOUT_MS)
            self._live_task = asyncio.create_task(self._live_loop())
        pages = self._ctx.pages
        return pages[-1] if pages else await self._ctx.new_page()

    async def _live_loop(self) -> None:
        """Save a JPEG of the current page about once a second, only when it changed."""
        self.live_dir.mkdir(parents=True, exist_ok=True)
        last = b""
        while self._ctx is not None:
            try:
                pages = self._ctx.pages
                if pages:
                    page = pages[-1]
                    shot = await page.screenshot(type="jpeg", quality=55, timeout=3000)
                    if shot != last:
                        last = shot
                        write_live_frame(self.live_dir, shot, page.url, await page.title())
            except Exception as e:  # page mid-navigation or closing: try again next tick
                logger.debug("live frame skipped: %s", e)
            await asyncio.sleep(LIVE_INTERVAL_S)

    async def close(self) -> None:
        if self._live_task is not None:
            self._live_task.cancel()
            self._live_task = None
        if self._ctx is not None:
            await self._ctx.close()
            await self._pw.stop()
            self._ctx = self._pw = None

    async def snapshot(self, page: Any) -> dict[str, Any]:
        data = await page.evaluate(SNAPSHOT_JS, [MAX_TEXT, MAX_LINKS])
        return {"url": page.url, "title": await page.title(), **data}

    async def _settle(self, page: Any) -> None:
        try:
            await page.wait_for_load_state("domcontentloaded", timeout=NAV_TIMEOUT_MS)
        except Exception:  # slow page: report what is there
            pass

    async def navigate(self, url: str) -> dict[str, Any]:
        url = check_url(url)
        async with self._lock:
            page = await self.page()
            try:
                resp = await page.goto(url, wait_until="domcontentloaded")
            except Exception as e:
                raise ToolError(f"Could not open {url}: {str(e).splitlines()[0]}") from e
            out = await self.snapshot(page)
            out["status"] = resp.status if resp else None
            return out

    async def read_page(self) -> dict[str, Any]:
        async with self._lock:
            return await self.snapshot(await self.page())

    async def _find(self, page: Any, target: str, kinds: tuple[str, ...]) -> Any:
        """First visible element matching a label/placeholder/name/text, or a CSS selector."""
        candidates = []
        if "field" in kinds:
            candidates += [
                page.get_by_label(target, exact=False),
                page.get_by_placeholder(target, exact=False),
                page.locator(f'[name="{target}"]'),
            ]
        if "clickable" in kinds:
            candidates += [
                page.get_by_role("button", name=target, exact=False),
                page.get_by_role("link", name=target, exact=False),
                page.get_by_text(target, exact=False),
            ]
        try:
            candidates.append(page.locator(target))  # a CSS selector, if the model gave one
        except Exception:
            pass
        for loc in candidates:
            try:
                if await loc.count() and await loc.first.is_visible():
                    return loc.first
            except Exception:  # invalid selector etc.
                continue
        raise ToolError(f"Could not find {target!r} on the page. Call read_page to see what is there.")

    async def fill_form(self, field: str, value: str) -> dict[str, Any]:
        async with self._lock:
            page = await self.page()
            el = await self._find(page, field, ("field",))
            tag = await el.evaluate("e => e.tagName.toLowerCase()")
            if tag == "select":
                await el.select_option(label=value)
            else:
                await el.fill(value)
            self._last_field = el
            return {"ok": True, "field": field, "value": value, "url": page.url}

    async def click(self, target: str) -> dict[str, Any]:
        async with self._lock:
            page = await self.page()
            el = await self._find(page, target, ("clickable",))
            await el.click()
            await self._settle(page)
            return {"ok": True, "clicked": target, **await self.snapshot(page)}

    async def submit_form(self, button: str = "") -> dict[str, Any]:
        async with self._lock:
            page = await self.page()
            if button:
                await (await self._find(page, button, ("clickable",))).click()
            elif self._last_field is not None:
                await self._last_field.press("Enter")
            else:
                raise ToolError("Nothing to submit: fill a field first or name the submit button.")
            self._last_field = None
            await self._settle(page)
            return {"ok": True, "submitted": button or "Enter", **await self.snapshot(page)}


def write_live_frame(live_dir: Path, jpeg: bytes, url: str, title: str) -> None:
    """Write frame.jpg then state.json (atomically), so a reader never sees a half-written pair."""
    import time

    state = json.dumps({"url": url, "title": title, "ts": time.time()}).encode()
    for name, data in (("frame.jpg", jpeg), ("state.json", state)):
        tmp = live_dir / f".{name}.tmp"
        tmp.write_bytes(data)
        tmp.replace(live_dir / name)


def read_live_frame(live_dir: Path = LIVE_DIR) -> tuple[dict[str, Any], bytes] | None:
    """Latest (state, jpeg) or None if the browser hasn't drawn anything yet."""
    try:
        state = json.loads((live_dir / "state.json").read_text())
        return state, (live_dir / "frame.jpg").read_bytes()
    except (OSError, ValueError):
        return None


def build_server(browser: Browser | None = None) -> MCPServer:
    b = browser or Browser()
    server = MCPServer("browser")

    def out(d: dict[str, Any]) -> str:
        return json.dumps(d, ensure_ascii=False)

    @server.tool()
    async def navigate(url: str) -> str:
        """Open a public web page and return its title, visible text, links, form fields and buttons [Tier R].

        Args:
            url: the http(s) address, e.g. https://example.com
        """
        return out(await b.navigate(url))

    @server.tool()
    async def read_page() -> str:
        """Re-read the current page: title, visible text, links, form fields and buttons [Tier R]."""
        return out(await b.read_page())

    @server.tool()
    async def fill_form(field: str, value: str) -> str:
        """Type into a form field on the current page [Tier W]. Nothing is sent until submit_form.

        Args:
            field: the field's label, placeholder or name as listed by navigate/read_page
            value: the text to enter (or the option to choose in a dropdown)
        """
        return out(await b.fill_form(field, value))

    @server.tool()
    async def click(target: str) -> str:
        """Click a button or link by its visible text [Tier A: may buy, book or send].

        Args:
            target: the button or link text as listed by navigate/read_page
        """
        return out(await b.click(target))

    @server.tool()
    async def submit_form(button: str = "") -> str:
        """Submit the form on the current page [Tier A: requires the user's approval].

        Args:
            button: the submit button's text; empty presses Enter in the last filled field
        """
        return out(await b.submit_form(button))

    return server


def main() -> None:
    parser = argparse.ArgumentParser(description="Rex Browser MCP Server (Playwright)")
    parser.parse_args()
    build_server().run(transport="stdio")


if __name__ == "__main__":
    main()
