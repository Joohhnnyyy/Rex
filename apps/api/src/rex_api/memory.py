"""Memory router: what Rex remembers about the user (facts + past call summaries), for the dashboard."""

from __future__ import annotations

from fastapi import APIRouter

from rex_mcp_servers import memory

router = APIRouter(prefix="/v1/memory", tags=["memory"])


@router.get("")
async def get_memory() -> dict:
    data = memory.load()
    return {"facts": data["facts"], "episodes": data["episodes"][::-1]}  # newest call first
