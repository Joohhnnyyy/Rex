"""Files router: the user's Rex library (see rex_mcp_servers.files) for the dashboard."""

from __future__ import annotations

import subprocess
import sys

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from mcp.server.mcpserver.exceptions import ToolError
from pydantic import BaseModel

from rex_mcp_servers import files

router = APIRouter(prefix="/v1/files", tags=["files"])

# Shown inside the dashboard; everything else (HTML, SVG, Office files…) is only ever downloaded, because a
# downloaded page or SVG can carry scripts that would run on this API's origin.
INLINE = {"image/png", "image/jpeg", "image/gif", "image/webp", "image/avif", "application/pdf"}


class SaveUrl(BaseModel):
    url: str
    folder: str = ""
    name: str = ""


class Move(BaseModel):
    folder: str


def _get(file_id: str):
    try:
        return files.resolve(file_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="No such file in the library.") from None


@router.get("")
async def list_library() -> dict:
    return {"root": str(files.root()), "folders": files.folders(), "files": list(reversed(files.load()))}


@router.get("/{file_id}/content")
async def content(file_id: str) -> FileResponse:
    entry, path = _get(file_id)
    if not path.exists():
        raise HTTPException(status_code=410, detail="The file was moved or deleted outside Rex.")
    inline = entry["mime"] in INLINE
    return FileResponse(
        path,
        media_type=entry["mime"] if inline else "application/octet-stream",
        filename=entry["name"],
        content_disposition_type="inline" if inline else "attachment",
        headers={"X-Content-Type-Options": "nosniff", "Content-Security-Policy": "sandbox"},
    )


@router.post("/save")
async def save(body: SaveUrl) -> dict:
    try:
        return await files.download(body.url, name=body.name, folder=body.folder)
    except ToolError as e:
        raise HTTPException(status_code=400, detail=str(e)) from None


@router.post("/{file_id}/move")
async def move(file_id: str, body: Move) -> dict:
    _get(file_id)
    return files.move(file_id, body.folder)


@router.delete("/{file_id}")
async def delete(file_id: str) -> dict:
    _get(file_id)
    return {"trashed": files.trash(file_id)["name"]}


@router.post("/{file_id}/reveal")
def reveal(file_id: str) -> dict:
    """Show the file in Finder (the API runs on the user's own Mac)."""
    _, path = _get(file_id)
    if sys.platform != "darwin":
        raise HTTPException(status_code=501, detail="Reveal works on macOS only.")
    subprocess.Popen(["open", "-R", str(path)])  # returns at once; Finder opens on its own
    return {"ok": True}
