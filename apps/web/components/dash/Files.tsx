"use client";

import {
  Archive,
  Download,
  ExternalLink,
  File,
  FileAudio,
  FileSpreadsheet,
  FileText,
  FileVideo,
  Folder,
  FolderInput,
  FolderSearch,
  Globe,
  Loader2,
  Presentation,
  Trash2,
  type LucideIcon,
} from "lucide-react";
import { useCallback, useEffect, useState } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

type Entry = {
  id: string;
  name: string;
  folder: string;
  kind: string;
  mime: string;
  size: number;
  source: string;
  note: string;
  saved_at: string;
};
type Library = { root: string; folders: string[]; files: Entry[] };

const KIND_ICON: Record<string, LucideIcon> = {
  Documents: FileText,
  Notes: FileText,
  Spreadsheets: FileSpreadsheet,
  Presentations: Presentation,
  Audio: FileAudio,
  Video: FileVideo,
  Archives: Archive,
  "Web pages": Globe,
};
const PREVIEW = new Set(["image/png", "image/jpeg", "image/gif", "image/webp", "image/avif"]);

const size = (n: number) =>
  n < 1024 ? `${n} B` : n < 1024 ** 2 ? `${(n / 1024).toFixed(0)} KB` : `${(n / 1024 ** 2).toFixed(1)} MB`;
const date = (iso: string) => new Date(iso).toLocaleDateString(undefined, { day: "numeric", month: "short" });
const contentUrl = (id: string) => `${API_URL}/v1/files/${id}/content`;

// The user's Rex library: what Rex downloaded or wrote, sorted into folders (Documents/Rex in Finder).
export function Files() {
  const [lib, setLib] = useState<Library | null>(null);
  const [failed, setFailed] = useState(false);
  const [folder, setFolder] = useState<string | null>(null);
  const [url, setUrl] = useState("");
  const [into, setInto] = useState("");
  const [busy, setBusy] = useState(false);
  const [note, setNote] = useState("");
  const [moving, setMoving] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      const res = await fetch(`${API_URL}/v1/files`);
      if (!res.ok) throw new Error();
      setLib(await res.json());
      setFailed(false);
    } catch {
      setFailed(true);
    }
  }, []);
  useEffect(() => {
    load();
  }, [load]);

  async function save(e: React.FormEvent) {
    e.preventDefault();
    if (!url.trim()) return;
    setBusy(true);
    setNote("");
    try {
      const res = await fetch(`${API_URL}/v1/files/save`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url: url.trim(), folder: into.trim() }),
      });
      const body = await res.json();
      setNote(res.ok ? `Saved ${body.name} to ${body.folder}.` : (body.detail ?? "Couldn't save it."));
      if (res.ok) setUrl("");
    } catch {
      setNote("Can't reach the Rex API.");
    } finally {
      setBusy(false);
      load();
    }
  }

  async function act(id: string, what: "reveal" | "delete" | "move", target = "") {
    if (what === "delete" && !confirm("Move this file to the Trash?")) return;
    await fetch(`${API_URL}/v1/files/${id}${what === "delete" ? "" : `/${what}`}`, {
      method: what === "delete" ? "DELETE" : "POST",
      headers: { "Content-Type": "application/json" },
      body: what === "move" ? JSON.stringify({ folder: target }) : undefined,
    }).catch(() => {});
    setMoving(null);
    if (what !== "reveal") load();
  }

  if (failed) return <p className="text-sm text-[var(--danger)]">Can&apos;t reach the Rex API at {API_URL}.</p>;
  if (!lib) return <p className="text-sm text-[var(--text-2)]">Loading…</p>;

  const counts = lib.files.reduce<Record<string, number>>((m, f) => ({ ...m, [f.folder]: (m[f.folder] ?? 0) + 1 }), {});
  const shown = folder ? lib.files.filter((f) => f.folder === folder) : lib.files;
  const home = lib.root.replace(/^\/Users\/[^/]+/, "~");

  return (
    <div className="stagger flex flex-col gap-4">
      <section className="panel flex flex-col gap-4 p-5 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <h1 className="flex items-center gap-2 text-2xl font-semibold tracking-tight">
            <Folder className="size-5 text-[var(--red-hi)]" aria-hidden /> Files
          </h1>
          <p className="mt-1 text-sm text-[var(--text-2)]">
            What Rex downloads or writes for you, sorted into folders. On your Mac: <span className="font-mono text-xs">{home}</span>
          </p>
        </div>
        <form onSubmit={save} className="flex w-full flex-col gap-2 sm:flex-row lg:w-auto">
          <label className="sr-only" htmlFor="file-url">Link to a file</label>
          <input
            id="file-url"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="Paste a link to a PDF, image, doc…"
            className="min-w-0 flex-1 rounded-[12px] border border-[var(--line)] bg-transparent px-3 py-2 text-sm outline-none placeholder:text-[var(--faint)] lg:w-80"
          />
          <label className="sr-only" htmlFor="file-folder">Folder</label>
          <input
            id="file-folder"
            value={into}
            onChange={(e) => setInto(e.target.value)}
            placeholder="Folder (optional)"
            list="rex-folders"
            className="rounded-[12px] border border-[var(--line)] bg-transparent px-3 py-2 text-sm outline-none placeholder:text-[var(--faint)] sm:w-40"
          />
          <button disabled={busy || !url.trim()} className="flex items-center justify-center gap-2 rounded-[12px] bg-[var(--red)] px-4 py-2 text-sm font-medium text-white disabled:opacity-50">
            {busy ? <Loader2 className="size-4 animate-spin" aria-hidden /> : <Download className="size-4" aria-hidden />}
            Save
          </button>
        </form>
      </section>
      <datalist id="rex-folders">
        {lib.folders.map((f) => (
          <option key={f} value={f} />
        ))}
      </datalist>
      {note && <p className="-mt-2 px-1 text-sm text-[var(--text-2)]" aria-live="polite">{note}</p>}

      <div className="grid gap-4 lg:grid-cols-[220px_minmax(0,1fr)]">
        <nav aria-label="Folders" className="panel h-fit p-2">
          {[null, ...lib.folders].map((f) => (
            <button
              key={f ?? "all"}
              onClick={() => setFolder(f)}
              aria-current={folder === f ? "true" : undefined}
              className={`flex w-full items-center gap-2 rounded-[10px] px-3 py-2 text-left text-sm ${folder === f ? "bg-[var(--red-glow)] text-[var(--text)]" : "text-[var(--text-2)] hover:bg-white/[0.03] hover:text-[var(--text)]"}`}
            >
              <Folder className="size-4 shrink-0" aria-hidden />
              <span className="flex-1 truncate">{f ?? "All files"}</span>
              <span className="tabular text-xs text-[var(--faint)]">{f ? counts[f] : lib.files.length}</span>
            </button>
          ))}
        </nav>

        {shown.length === 0 ? (
          <section className="panel p-6 text-sm text-[var(--text-2)]">
            Nothing here yet. Paste a link above, or ask Rex: &quot;save that PDF&quot;, &quot;download these photos into a Goa
            trip folder&quot;, &quot;save this research as a doc&quot;.
          </section>
        ) : (
          <ul className="grid gap-3 sm:grid-cols-2 2xl:grid-cols-3" aria-label="Files">
            {shown.map((f) => {
              const Icon = KIND_ICON[f.kind] ?? File;
              return (
                <li key={f.id} className="rise panel flex flex-col overflow-hidden">
                  <a href={contentUrl(f.id)} target="_blank" rel="noreferrer noopener" className="group block" aria-label={`Open ${f.name}`}>
                    {PREVIEW.has(f.mime) ? (
                      // eslint-disable-next-line @next/next/no-img-element -- served by the local Rex API
                      <img src={contentUrl(f.id)} alt="" loading="lazy" className="h-36 w-full object-cover transition-transform duration-300 group-hover:scale-[1.03]" />
                    ) : (
                      <span className="grid h-36 place-items-center bg-white/[0.02]">
                        <Icon className="size-10 text-[var(--red-hi)]/80" aria-hidden />
                      </span>
                    )}
                  </a>
                  <div className="flex flex-1 flex-col gap-1 p-3">
                    <p className="truncate text-sm font-medium" title={f.name}>{f.name}</p>
                    <p className="text-xs text-[var(--text-2)]">
                      {f.folder} · {size(f.size)} · {date(f.saved_at)}
                    </p>
                    {f.note && <p className="line-clamp-2 text-xs text-[var(--faint)]">{f.note}</p>}
                    {moving === f.id ? (
                      <form
                        onSubmit={(e) => {
                          e.preventDefault();
                          const target = new FormData(e.currentTarget).get("to")?.toString().trim();
                          if (target) act(f.id, "move", target);
                        }}
                        className="mt-2 flex gap-1"
                      >
                        <label className="sr-only" htmlFor={`move-${f.id}`}>Move to folder</label>
                        <input id={`move-${f.id}`} name="to" autoFocus list="rex-folders" placeholder="Folder name" className="min-w-0 flex-1 rounded-lg border border-[var(--line)] bg-transparent px-2 py-1 text-xs outline-none" />
                        <button className="rounded-lg bg-[var(--red)] px-2 text-xs text-white">Move</button>
                      </form>
                    ) : (
                      <div className="mt-auto flex gap-1 pt-2">
                        <IconButton label="Open" icon={ExternalLink} href={contentUrl(f.id)} />
                        <IconButton label="Show in Finder" icon={FolderSearch} onClick={() => act(f.id, "reveal")} />
                        <IconButton label="Move to folder" icon={FolderInput} onClick={() => setMoving(f.id)} />
                        <IconButton label="Move to Trash" icon={Trash2} onClick={() => act(f.id, "delete")} danger />
                      </div>
                    )}
                  </div>
                </li>
              );
            })}
          </ul>
        )}
      </div>
    </div>
  );
}

function IconButton({ label, icon: Icon, onClick, href, danger = false }: { label: string; icon: LucideIcon; onClick?: () => void; href?: string; danger?: boolean }) {
  const cls = `grid size-8 place-items-center rounded-lg text-[var(--text-2)] hover:bg-white/5 ${danger ? "hover:text-[var(--danger)]" : "hover:text-[var(--text)]"}`;
  return href ? (
    <a href={href} target="_blank" rel="noreferrer noopener" aria-label={label} title={label} className={cls}>
      <Icon className="size-4" />
    </a>
  ) : (
    <button onClick={onClick} aria-label={label} title={label} className={cls}>
      <Icon className="size-4" />
    </button>
  );
}
