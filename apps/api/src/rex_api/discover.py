"""Discover router: Rex's own research for the user (see rex_mcp_servers.discoveries).

Runs every few hours in the background (REX_DISCOVER_EVERY_H, default 6; 0 turns it off) and on demand from
the dashboard. Needs FIRECRAWL_API_KEY for search; the LLM picks what's worth showing.
"""

from __future__ import annotations

import asyncio
import logging
import os
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from rex_llm_router.client import LLMClient
from rex_mcp_servers import discoveries

router = APIRouter(prefix="/v1/discoveries", tags=["discoveries"])
logger = logging.getLogger("rex.discover")
_lock = asyncio.Lock()


class Interests(BaseModel):
    interests: list[str]


async def _write(system: str, user: str) -> str:
    out = await LLMClient().complete(
        "supervise", [{"role": "system", "content": system}, {"role": "user", "content": user}]
    )
    return out.text


async def run_now() -> dict:
    key = os.environ.get("FIRECRAWL_API_KEY")
    if not key:
        raise HTTPException(status_code=503, detail="Set FIRECRAWL_API_KEY in .env so Rex can search the web.")
    if _lock.locked():
        raise HTTPException(status_code=409, detail="Rex is already researching; give it a minute.")
    async with _lock:
        return await discoveries.run(_write, key)


@router.get("")
async def list_discoveries() -> dict:
    data = discoveries.load()
    return {
        "items": list(reversed(data["items"])),  # newest first
        "interests": data["interests"],
        "active_interests": discoveries.interests(data),
        "last_run": data["last_run"],
        "running": _lock.locked(),
        "ready": bool(os.environ.get("FIRECRAWL_API_KEY")),
    }


@router.post("/run")
async def run() -> dict:
    return await run_now()


@router.put("/interests")
async def put_interests(body: Interests) -> dict:
    return {"interests": discoveries.set_interests(body.interests)}


@router.post("/seen")
async def seen() -> dict:
    discoveries.mark_seen()
    return {"ok": True}


async def background_loop() -> None:
    """Research whenever the last run is older than the interval; checks every 30 minutes."""
    every = float(os.environ.get("REX_DISCOVER_EVERY_H", "6"))
    if every <= 0 or not os.environ.get("FIRECRAWL_API_KEY"):
        return
    while True:
        last = discoveries.load()["last_run"]
        due = not last or datetime.now(UTC) - datetime.fromisoformat(last) > timedelta(hours=every)
        if due and discoveries.interests() and not _lock.locked():
            try:
                result = await run_now()
                logger.info("discovery run: %s new from %s", result["added"], result["searched"])
            except Exception:
                logger.exception("discovery run failed")
        await asyncio.sleep(1800)
