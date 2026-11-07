"""Connections router (T-25): which services Rex can use right now, for the dashboard."""

from __future__ import annotations

import asyncio
import os
from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel

from rex_mcp_servers.calendar import LOGIN_HINT, SCOPES, default_token_path, google_creds

router = APIRouter(prefix="/v1/connections", tags=["connections"])

GMAIL_SCOPES = {s for s in SCOPES if "gmail" in s}


class Connection(BaseModel):
    id: str
    name: str
    status: Literal["ok", "off", "error"]
    detail: str


def _env(*names: str) -> bool:
    return all(os.environ.get(n) for n in names)


def _keyed(id_: str, name: str, ok_detail: str, *names: str) -> Connection:
    if _env(*names):
        return Connection(id=id_, name=name, status="ok", detail=ok_detail)
    return Connection(id=id_, name=name, status="off", detail=f"Set {', '.join(names)} in .env")


def _google() -> list[Connection]:
    """Calendar and Gmail share one login; refreshing it is the real check (it fails once the login expires)."""
    if not default_token_path().exists():
        off = f"Not logged in. {LOGIN_HINT.removeprefix('Ask the user to run: ')}"
        return [
            Connection(id=i, name=n, status="off", detail=off)
            for i, n in (("calendar", "Calendar"), ("gmail", "Gmail"))
        ]
    try:
        creds = google_creds()
    except Exception as e:  # ToolError carries the re-login hint
        msg = str(e)
        return [
            Connection(id=i, name=n, status="error", detail=msg)
            for i, n in (("calendar", "Calendar"), ("gmail", "Gmail"))
        ]
    granted = set(creds.scopes or [])
    gmail_ok = not granted or GMAIL_SCOPES <= granted  # older tokens don't list scopes; Gmail tools report it then
    return [
        Connection(id="calendar", name="Calendar", status="ok", detail="Logged in"),
        Connection(
            id="gmail",
            name="Gmail",
            status="ok" if gmail_ok else "error",
            detail="Logged in" if gmail_ok else f"Login lacks Gmail access. {LOGIN_HINT}",
        ),
    ]


def _browser() -> Connection:
    from playwright.sync_api import sync_playwright

    try:
        with sync_playwright() as p:
            path = p.chromium.executable_path
    except Exception as e:
        return Connection(id="browser", name="Browser", status="error", detail=f"Playwright failed: {e}")
    if os.path.exists(path):
        return Connection(id="browser", name="Browser", status="ok", detail="Chromium ready")
    return Connection(id="browser", name="Browser", status="off", detail="Run: uv run playwright install chromium")


@router.get("", response_model=list[Connection])
async def list_connections() -> list[Connection]:
    google, browser = await asyncio.gather(asyncio.to_thread(_google), asyncio.to_thread(_browser))
    return [
        _keyed("voice", "Voice", "Gnani + LiveKit", "GNANI_API_KEY", "LIVEKIT_URL", "LIVEKIT_API_KEY"),
        *google,
        _keyed("slack", "Slack", "Bot token set", "SLACK_BOT_TOKEN"),
        _keyed("notion", "Notion", "Token set", "NOTION_TOKEN"),
        _keyed("firecrawl", "Web research", "Firecrawl key set", "FIRECRAWL_API_KEY"),
        browser,
    ]
