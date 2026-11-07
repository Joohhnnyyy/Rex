"""Rex's file library: safe downloads sorted into folders, notes, moves and Trash."""

from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import pytest
import yaml
from mcp.server.mcpserver.exceptions import ToolError

from rex_mcp_servers import files

REPO_ROOT = Path(__file__).resolve().parents[3]
PNG = b"\x89PNG\r\n\x1a\n" + b"0" * 64
ROUTES = {
    "/brochure.pdf": ("application/pdf", b"%PDF-1.4 brochure", {}),
    "/photo": ("image/png", PNG, {}),  # no extension in the URL: the type comes from Content-Type
    "/go": (None, b"", {"Location": "/brochure.pdf"}),  # a redirect, re-checked before following
    "/setup.exe": ("application/octet-stream", b"MZ", {}),
    "/report": ("application/octet-stream", b"x", {"Content-Disposition": 'attachment; filename="Q3 report.xlsx"'}),
}


class _Handler(BaseHTTPRequestHandler):
    def do_GET(self):  # noqa: N802
        mime, body, headers = ROUTES.get(self.path, ("text/plain", b"missing", {}))
        self.send_response(302 if "Location" in headers else 200 if self.path in ROUTES else 404)
        if mime:
            self.send_header("Content-Type", mime)
        for k, v in headers.items():
            self.send_header(k, v)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *a):
        pass


@pytest.fixture
def site(tmp_path, monkeypatch):
    monkeypatch.setenv("REX_FILES_DIR", str(tmp_path / "Rex"))
    monkeypatch.setenv("REX_BROWSER_ALLOW_LOCAL", "1")  # the test server is local
    monkeypatch.setenv("HOME", str(tmp_path))
    (tmp_path / ".Trash").mkdir()
    srv = HTTPServer(("127.0.0.1", 0), _Handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{srv.server_port}"
    srv.shutdown()


@pytest.mark.asyncio
async def test_downloads_sort_by_type_or_folder_and_follow_safe_redirects(site):
    pdf = await files.download(f"{site}/go", note="hotel brochure")
    assert (pdf["folder"], pdf["name"], pdf["kind"]) == ("Documents", "brochure.pdf", "Documents")
    assert pdf["source"].endswith("/brochure.pdf") and pdf["note"] == "hotel brochure"

    img = await files.download(f"{site}/photo", name="Goa beach", folder="Goa trip")
    assert (img["folder"], img["name"], img["kind"]) == ("Goa trip", "Goa beach.png", "Images")
    assert (files.root() / img["path"]).read_bytes() == PNG

    xlsx = await files.download(f"{site}/report")
    assert (xlsx["folder"], xlsx["name"]) == ("Spreadsheets", "Q3 report.xlsx")

    again = await files.download(f"{site}/brochure.pdf")
    assert again["name"] == "brochure (2).pdf"  # never overwrites
    assert files.folders() == ["Documents", "Goa trip", "Spreadsheets"]


@pytest.mark.asyncio
async def test_refuses_programs_big_files_and_private_addresses(site, monkeypatch):
    with pytest.raises(ToolError, match=r"not \.exe"):
        await files.download(f"{site}/setup.exe")
    monkeypatch.setattr(files, "MAX_BYTES", 10)
    with pytest.raises(ToolError, match="too big"):
        await files.download(f"{site}/photo")
    monkeypatch.delenv("REX_BROWSER_ALLOW_LOCAL")
    with pytest.raises(ToolError, match="private or local"):
        await files.download(f"{site}/brochure.pdf")
    assert files.load() == [] and not list(files.root().rglob("*.part"))


def test_notes_moves_trash_and_names_cannot_escape(site, tmp_path):
    note = files.write_note("Delhi flights", "- IndiGo: Rs 5,800 - https://x.com", folder="../../etc")
    assert note["folder"] == "etc" and (files.root() / "etc" / "Delhi flights.md").read_text().startswith("# Delhi")
    moved = files.move(note["id"], "Delhi trip")
    assert moved["path"] == "Delhi trip/Delhi flights.md" and (files.root() / moved["path"]).exists()
    files.trash(note["id"])
    assert files.load() == [] and (tmp_path / ".Trash" / "Delhi flights.md").exists()


@pytest.mark.asyncio
async def test_mcp_tools_and_tiers(site):
    server = files.build_server()
    out = json.loads((await server.call_tool("save_note", {"title": "Plan", "text": "Pack"})).content[0].text)
    assert out["saved"]["folder"] == "Notes" and out["where"] == "Documents/Rex/Notes/Plan.md"
    listed = json.loads((await server.call_tool("list_files", {"query": "plan"})).content[0].text)
    assert [f["name"] for f in listed["files"]] == ["Plan.md"]

    cfg = yaml.safe_load((REPO_ROOT / "infra" / "mcp_servers.yaml").read_text())
    tiers = {k: v["tier"] for k, v in cfg["servers"]["files"]["tools"].items()}
    assert tiers == {"save_from_url": "W", "save_note": "W", "list_files": "R", "move_file": "W"}
    assert "files" in cfg["allowlists"]["rex"]
