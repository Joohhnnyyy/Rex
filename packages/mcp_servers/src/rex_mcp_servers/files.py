"""Rex's file library: things Rex downloads or writes for the user, sorted into folders.

Everything lives in one folder the user can open in Finder (~/Documents/Rex, REX_FILES_DIR overrides):
    Documents/  Images/  Spreadsheets/  Presentations/  Audio/  Video/  Archives/  Notes/  <your folders>/
with an index at .rex-library.json. Downloads are untrusted: public http(s) only (every redirect re-checked),
an allowlist of file types, a size cap, sanitised names, and nothing is ever opened or run.

MCP tools (Rex): save_from_url [W], save_note [W], list_files [R], move_file [W]. Deleting is done from the
dashboard, and moves files to the macOS Trash rather than erasing them.
"""

from __future__ import annotations

import json
import mimetypes
import os
import re
import uuid
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import unquote, urljoin, urlparse

import httpx
from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError

from rex_mcp_servers.browser import check_url

MAX_BYTES = 50 * 1024 * 1024
MAX_REDIRECTS = 5
INDEX = ".rex-library.json"

KINDS: dict[str, tuple[str, ...]] = {
    "Images": ("png", "jpg", "jpeg", "gif", "webp", "avif", "heic", "svg"),
    "Documents": ("pdf", "doc", "docx", "txt", "md", "rtf", "odt", "pages", "epub"),
    "Spreadsheets": ("csv", "xls", "xlsx", "ods", "numbers", "json"),
    "Presentations": ("ppt", "pptx", "key", "odp"),
    "Audio": ("mp3", "wav", "m4a", "ogg", "flac"),
    "Video": ("mp4", "mov", "webm", "mkv"),
    "Archives": ("zip", "tar", "gz", "tgz", "7z"),
    "Web pages": ("html", "htm"),
}
EXT_KIND = {ext: kind for kind, exts in KINDS.items() for ext in exts}


def root() -> Path:
    override = os.environ.get("REX_FILES_DIR")
    path = Path(override).expanduser() if override else Path.home() / "Documents" / "Rex"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _index_path() -> Path:
    return root() / INDEX


def load() -> list[dict]:
    try:
        return json.loads(_index_path().read_text())
    except (FileNotFoundError, ValueError):
        return []


def _save(entries: list[dict]) -> None:
    tmp = _index_path().with_suffix(".tmp")
    tmp.write_text(json.dumps(entries, ensure_ascii=False, indent=1))
    os.replace(tmp, _index_path())


def safe_name(name: str, fallback: str = "file") -> str:
    """A file or folder name that can't escape the library or confuse Finder."""
    name = unquote(name).replace("/", " ").replace("\\", " ").replace(":", " ")
    name = re.sub(r"[\x00-\x1f<>\"|?*]", "", name).strip(" .")
    return name[:120] or fallback


def _folder(folder: str, kind: str) -> str:
    return safe_name(folder) if folder.strip() else kind


def _unique(directory: Path, name: str) -> Path:
    stem, suffix = os.path.splitext(name)
    path, n = directory / name, 2
    while path.exists():
        path = directory / f"{stem} ({n}){suffix}"
        n += 1
    return path


def _ext_for(url: str, content_type: str, disposition: str, name: str) -> tuple[str, str, str]:
    """(base name, extension, extension as named) from the user's name, Content-Disposition, URL or MIME type."""
    m = re.search(r"filename\*?=(?:UTF-8'')?\"?([^\";]+)", disposition or "", re.I)
    candidates = [name, m.group(1) if m else "", Path(urlparse(url).path).name]
    base = next((c for c in candidates if c and c.strip()), "download")
    stem, ext = os.path.splitext(safe_name(base, "download"))
    ext = named = ext.lstrip(".").lower()
    if ext not in EXT_KIND:
        for candidate in candidates[1:]:
            e = os.path.splitext(candidate)[1].lstrip(".").lower()
            if e in EXT_KIND:
                ext = e
                break
        else:
            guessed = mimetypes.guess_extension((content_type or "").split(";")[0].strip()) or ""
            ext = {"jpe": "jpg", "htm": "html"}.get(guessed.lstrip("."), guessed.lstrip("."))
    return stem, ext, named


def _entry(path: Path, kind: str, source: str, note: str) -> dict:
    rel = path.relative_to(root())
    return {
        "id": uuid.uuid4().hex[:10],
        "name": path.name,
        "folder": str(rel.parent),
        "path": str(rel),
        "kind": kind,
        "mime": mimetypes.guess_type(path.name)[0] or "application/octet-stream",
        "size": path.stat().st_size,
        "source": source,
        "note": note[:300],
        "saved_at": datetime.now(UTC).isoformat(timespec="seconds"),
    }


def _add(entry: dict) -> dict:
    entries = load()
    entries.append(entry)
    _save(entries)
    return entry


async def download(
    url: str, name: str = "", folder: str = "", note: str = "", http: httpx.AsyncClient | None = None
) -> dict:
    """Fetch a public file into the library. Raises ToolError with a reason the user can act on."""
    own = http is None
    http = http or httpx.AsyncClient(timeout=60)
    try:
        current = check_url(url)
        for _ in range(MAX_REDIRECTS + 1):
            async with http.stream("GET", current, follow_redirects=False, headers={"User-Agent": "Rex/1.0"}) as resp:
                if resp.is_redirect:
                    current = check_url(urljoin(current, resp.headers.get("location", "")))
                    continue
                if resp.status_code >= 400:
                    raise ToolError(f"The site answered {resp.status_code}; the file isn't available there.")
                if int(resp.headers.get("content-length") or 0) > MAX_BYTES:
                    raise ToolError(f"That file is over {MAX_BYTES // 2**20} MB; too big to save.")
                stem, ext, named = _ext_for(
                    current, resp.headers.get("content-type", ""), resp.headers.get("content-disposition", ""), name
                )
                kind = EXT_KIND.get(ext)
                if not kind:
                    raise ToolError(
                        f"Rex only saves documents, images, spreadsheets, slides, audio, video and archives, "
                        f"not .{named or ext or 'unknown'} files."
                    )
                directory = root() / _folder(folder, kind)
                directory.mkdir(parents=True, exist_ok=True)
                path = _unique(directory, f"{stem}.{ext}")
                size = 0
                partial = path.with_name(path.name + ".part")
                with partial.open("wb") as out:
                    async for chunk in resp.aiter_bytes():
                        size += len(chunk)
                        if size > MAX_BYTES:
                            out.close()
                            partial.unlink(missing_ok=True)
                            raise ToolError(f"That file is over {MAX_BYTES // 2**20} MB; too big to save.")
                        out.write(chunk)
                os.replace(partial, path)
                return _add(_entry(path, kind, current, note))
        raise ToolError("Too many redirects; the link doesn't lead to a file.")
    except httpx.HTTPError as e:
        raise ToolError(f"Couldn't download it ({type(e).__name__}).") from e
    finally:
        if own:
            await http.aclose()


def write_note(title: str, text: str, folder: str = "") -> dict:
    """Save text Rex wrote (a summary, a list, research) as a Markdown document."""
    if not text.strip():
        raise ToolError("There's nothing to save.")
    directory = root() / _folder(folder, "Notes")
    directory.mkdir(parents=True, exist_ok=True)
    path = _unique(directory, safe_name(title, "Note") + ".md")
    path.write_text(f"# {title.strip() or 'Note'}\n\n{text.strip()}\n")
    return _add(_entry(path, "Notes", "rex", title))


def resolve(file_id: str) -> tuple[dict, Path]:
    for entry in load():
        if entry["id"] == file_id:
            path = (root() / entry["path"]).resolve()
            if root().resolve() not in path.parents:
                break
            return entry, path
    raise KeyError(file_id)


def move(file_id: str, folder: str) -> dict:
    entry, path = resolve(file_id)
    directory = root() / _folder(folder, entry["kind"])
    directory.mkdir(parents=True, exist_ok=True)
    target = _unique(directory, path.name)
    os.replace(path, target)
    entries = [e for e in load() if e["id"] != file_id]
    moved = {**entry, "name": target.name, "folder": str(target.parent.relative_to(root())),
             "path": str(target.relative_to(root()))}  # fmt: skip
    _save([*entries, moved])
    return moved


def trash(file_id: str) -> dict:
    """Move the file to the macOS Trash (recoverable) and drop it from the library."""
    entry, path = resolve(file_id)
    bin_ = Path.home() / ".Trash"
    if bin_.is_dir():
        os.replace(path, _unique(bin_, path.name))
    else:
        path.unlink(missing_ok=True)
    _save([e for e in load() if e["id"] != file_id])
    return entry


def folders() -> list[str]:
    return sorted({e["folder"] for e in load()})


def _brief(e: dict) -> dict:
    return {k: e[k] for k in ("id", "name", "folder", "kind", "size", "saved_at", "note")}


def build_server() -> MCPServer:
    server = MCPServer("files")

    @server.tool()
    async def save_from_url(url: str, name: str = "", folder: str = "", note: str = "") -> str:
        """Download a document, image, PDF, spreadsheet, slide deck, audio, video or archive from a public link
        into the user's Rex library (Documents/Rex in Finder), sorted into a folder [Tier W].

        Args:
            url: direct link to the file
            name: optional file name to save it as (the extension is kept)
            folder: optional folder, e.g. "Delhi trip" or "Naruto"; default is by type (Images, Documents…)
            note: optional one line on what it is, shown in the dashboard
        """
        entry = await download(url, name=name, folder=folder, note=note)
        return json.dumps({"saved": _brief(entry), "where": f"Documents/Rex/{entry['path']}"}, ensure_ascii=False)

    @server.tool()
    async def save_note(title: str, text: str, folder: str = "") -> str:
        """Save text you wrote for the user (a summary, list, research, plan) as a document in their Rex library
        [Tier W].

        Args:
            title: document title, also the file name
            text: the content; Markdown lists and links are fine
            folder: optional folder; default is Notes
        """
        entry = write_note(title, text, folder)
        return json.dumps({"saved": _brief(entry), "where": f"Documents/Rex/{entry['path']}"}, ensure_ascii=False)

    @server.tool()
    async def list_files(folder: str = "", query: str = "") -> str:
        """List what's in the user's Rex library, newest first [Tier R].

        Args:
            folder: optional folder to look in
            query: optional words to match in names and notes
        """
        words = query.lower().split()
        found = [
            _brief(e)
            for e in reversed(load())
            if (not folder or e["folder"].lower() == folder.lower())
            and all(w in f"{e['name']} {e['note']}".lower() for w in words)
        ]
        return json.dumps({"folders": folders(), "files": found[:25]}, ensure_ascii=False)

    @server.tool()
    async def move_file(file_id: str, folder: str) -> str:
        """Move a file in the user's Rex library into another folder (created if needed) [Tier W].

        Args:
            file_id: the id from list_files
            folder: the folder to move it to
        """
        try:
            entry = move(file_id, folder)
        except KeyError as e:
            raise ToolError("No file with that id; call list_files first.") from e
        return json.dumps({"moved": _brief(entry)}, ensure_ascii=False)

    return server


if __name__ == "__main__":
    build_server().run()
