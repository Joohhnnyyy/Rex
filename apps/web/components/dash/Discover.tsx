"use client";

import { ExternalLink, Loader2, Plus, Sparkles, X } from "lucide-react";
import { useCallback, useEffect, useState } from "react";

import { Panel } from "@/components/dash/Panels";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export type Find = { id: string; topic: string; title: string; url: string; why: string; found_at: string; seen: boolean };
type Data = {
  items: Find[];
  interests: string[];
  active_interests: string[];
  last_run: string | null;
  running: boolean;
  ready: boolean;
};

function ago(iso: string | null) {
  if (!iso) return "never";
  const m = Math.round((Date.now() - new Date(iso).getTime()) / 60000);
  return m < 1 ? "just now" : m < 60 ? `${m} min ago` : m < 1440 ? `${Math.round(m / 60)} h ago` : `${Math.round(m / 1440)} d ago`;
}

function host(url: string) {
  try {
    return new URL(url).host.replace(/^www\./, "");
  } catch {
    return url;
  }
}

// Rex's own research: what it looked into for the user, why each find matters, and what to look into next.
export function Discover({ onSeen }: { onSeen: () => void }) {
  const [data, setData] = useState<Data | null>(null);
  const [failed, setFailed] = useState(false);
  const [busy, setBusy] = useState(false);
  const [note, setNote] = useState("");
  const [draft, setDraft] = useState("");

  const load = useCallback(async () => {
    try {
      const res = await fetch(`${API_URL}/v1/discoveries`);
      if (!res.ok) throw new Error();
      setData(await res.json());
      setFailed(false);
    } catch {
      setFailed(true);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  // Opening the section counts as seeing the new finds (after a moment, so the "New" tags are noticed).
  useEffect(() => {
    if (!data?.items.some((i) => !i.seen)) return;
    const t = setTimeout(async () => {
      await fetch(`${API_URL}/v1/discoveries/seen`, { method: "POST" }).catch(() => {});
      onSeen();
    }, 4000);
    return () => clearTimeout(t);
  }, [data, onSeen]);

  async function saveInterests(next: string[]) {
    setData((d) => (d ? { ...d, interests: next } : d));
    await fetch(`${API_URL}/v1/discoveries/interests`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ interests: next }),
    }).catch(() => {});
    load();
  }

  async function research() {
    setBusy(true);
    setNote("");
    try {
      const res = await fetch(`${API_URL}/v1/discoveries/run`, { method: "POST" });
      const body = await res.json();
      if (!res.ok) setNote(body.detail ?? "Research failed.");
      else
        setNote(
          body.added
            ? `Found ${body.added} new thing${body.added === 1 ? "" : "s"}.`
            : "Nothing new worth showing this time.",
        );
    } catch {
      setNote("Can't reach the Rex API.");
    } finally {
      setBusy(false);
      load();
    }
  }

  if (failed) return <p className="text-sm text-[var(--danger)]">Can&apos;t reach the Rex API at {API_URL}.</p>;
  if (!data) return <p className="text-sm text-[var(--text-2)]">Loading…</p>;

  const fromMemory = data.active_interests.filter((t) => !data.interests.some((i) => i.toLowerCase() === t.toLowerCase()));
  const fresh = data.items.filter((i) => !i.seen);
  const older = data.items.filter((i) => i.seen);

  return (
    <div className="stagger flex flex-col gap-4">
      <section className="panel flex flex-col gap-4 p-5 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="flex items-center gap-2 text-2xl font-semibold tracking-tight">
            <Sparkles className="size-5 text-[var(--red-hi)]" aria-hidden /> Rex&apos;s research
          </h1>
          <p className="mt-1 max-w-xl text-sm text-[var(--text-2)]">
            Every few hours Rex searches the web for what you&apos;re into and keeps only what&apos;s new and worth your
            time. Last looked {ago(data.last_run)}.
          </p>
        </div>
        <div className="flex flex-col items-start gap-1 sm:items-end">
          <button
            onClick={research}
            disabled={busy || data.running || !data.ready || !data.active_interests.length}
            className="flex items-center gap-2 rounded-[12px] bg-[var(--red)] px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
          >
            {busy || data.running ? <Loader2 className="size-4 animate-spin" aria-hidden /> : <Sparkles className="size-4" aria-hidden />}
            {busy || data.running ? "Researching…" : "Research now"}
          </button>
          <span className="text-xs text-[var(--text-2)]" aria-live="polite">
            {!data.ready ? "Needs FIRECRAWL_API_KEY in .env" : !data.active_interests.length ? "Add an interest first" : note}
          </span>
        </div>
      </section>

      <Panel title="What Rex looks into">
        <ul className="flex flex-wrap gap-2">
          {data.interests.map((t) => (
            <li key={t} className="flex items-center gap-1 rounded-full border border-[var(--line-active)] bg-[var(--red-glow)] py-1 pl-3 pr-1 text-sm">
              {t}
              <button onClick={() => saveInterests(data.interests.filter((i) => i !== t))} aria-label={`Stop researching ${t}`} className="grid size-6 place-items-center rounded-full hover:bg-white/10">
                <X className="size-3.5" />
              </button>
            </li>
          ))}
          {fromMemory.map((t) => (
            <li key={t} className="rounded-full border border-[var(--line)] px-3 py-1 text-sm text-[var(--text-2)]" title="Rex remembered this from your calls">
              {t} <span className="text-[11px] text-[var(--faint)]">· from your calls</span>
            </li>
          ))}
          <li>
            <form
              onSubmit={(e) => {
                e.preventDefault();
                if (draft.trim()) saveInterests([...data.interests, draft.trim()]);
                setDraft("");
              }}
              className="flex items-center gap-1 rounded-full border border-dashed border-[var(--line)] py-0.5 pl-3 pr-1"
            >
              <label className="sr-only" htmlFor="interest">
                Add an interest
              </label>
              <input
                id="interest"
                value={draft}
                onChange={(e) => setDraft(e.target.value)}
                placeholder="Add an interest, e.g. Naruto, IPL, AI agents"
                className="w-56 bg-transparent text-sm outline-none placeholder:text-[var(--faint)]"
              />
              <button type="submit" aria-label="Add interest" className="grid size-7 place-items-center rounded-full hover:bg-white/10">
                <Plus className="size-4" />
              </button>
            </form>
          </li>
        </ul>
        <p className="mt-3 text-xs text-[var(--faint)]">
          Rex researches up to four at a time. Tell it in a call (&quot;I&apos;m really into F1&quot;) and it adds them itself.
        </p>
      </Panel>

      {data.items.length === 0 ? (
        <Panel title="Finds">
          <p className="text-sm text-[var(--text-2)]">Nothing yet. Add what you&apos;re into, then press Research now.</p>
        </Panel>
      ) : (
        <>
          {fresh.length > 0 && <FindGrid title={`New for you · ${fresh.length}`} items={fresh} fresh />}
          {older.length > 0 && <FindGrid title="Earlier finds" items={older} />}
        </>
      )}
    </div>
  );
}

function FindGrid({ title, items, fresh = false }: { title: string; items: Find[]; fresh?: boolean }) {
  return (
    <section aria-label={title}>
      <h2 className="mb-3 px-1 text-sm font-semibold text-[var(--text-2)]">{title}</h2>
      <ul className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
        {items.map((f) => (
          <li key={f.id} className="rise">
            <a
              href={f.url}
              target="_blank"
              rel="noreferrer noopener"
              className="lift panel flex h-full flex-col gap-2 p-4 hover:bg-[var(--panel-hover)]"
            >
              <span className="flex items-center justify-between gap-2 text-[11px]">
                <span className="rounded-full bg-[var(--red-glow)] px-2 py-0.5 text-[var(--red-hi)]">{f.topic}</span>
                <span className="flex items-center gap-2 text-[var(--text-2)]">
                  {fresh && <span className="live-dot rounded-full bg-[var(--red)] px-1.5 py-0.5 font-medium text-white">New</span>}
                  {ago(f.found_at)}
                </span>
              </span>
              <span className="text-[15px] font-medium leading-snug">{f.title}</span>
              <span className="text-sm leading-relaxed text-[var(--text-2)]">{f.why}</span>
              <span className="mt-auto flex items-center gap-1 pt-1 text-xs text-[var(--faint)]">
                {host(f.url)} <ExternalLink className="size-3" aria-hidden />
              </span>
            </a>
          </li>
        ))}
      </ul>
    </section>
  );
}
