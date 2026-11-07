"use client";

import { useCallback, useEffect, useState } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

type Connection = {
  id: string;
  name: string;
  status: "ok" | "off" | "error";
  detail: string;
};

const DOT = {
  ok: "bg-[var(--ok)]",
  off: "bg-[var(--muted)]",
  error: "bg-[var(--danger)]",
} as const;
const WORD = {
  ok: "Connected",
  off: "Not set up",
  error: "Needs attention",
} as const;

// T-25: what Rex can reach right now (GET /v1/connections). Hover or tap a chip for the fix.
export function Connections() {
  const [items, setItems] = useState<Connection[] | null>(null);
  const [failed, setFailed] = useState(false);
  const [open, setOpen] = useState<string | null>(null);

  const load = useCallback(async () => {
    setFailed(false);
    try {
      const res = await fetch(`${API_URL}/v1/connections`);
      if (!res.ok) throw new Error(String(res.status));
      setItems(await res.json());
    } catch {
      setFailed(true);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const detail = items?.find((c) => c.id === open);

  return (
    <section className="w-full rounded-2xl bg-[var(--surface)] p-4 shadow-sm">
      <div className="mb-3 flex items-center justify-between">
        <h2 className="text-sm font-semibold text-[var(--muted)]">
          Connections
        </h2>
        <button
          onClick={load}
          className="text-xs text-[var(--muted)] underline-offset-2 hover:underline"
        >
          Refresh
        </button>
      </div>
      {failed && (
        <p className="text-sm text-[var(--danger)]">
          Can&apos;t reach the Rex API at {API_URL}.
        </p>
      )}
      {!items && !failed && (
        <p className="text-sm text-[var(--muted)]">Checking…</p>
      )}
      {items && (
        <ul className="flex flex-wrap gap-2">
          {items.map((c) => (
            <li key={c.id}>
              <button
                onClick={() => setOpen(open === c.id ? null : c.id)}
                title={`${WORD[c.status]}: ${c.detail}`}
                aria-label={`${c.name}: ${WORD[c.status]}`}
                aria-expanded={open === c.id}
                className="flex items-center gap-2 rounded-full border border-[var(--muted)]/25 px-3 py-1.5 text-sm"
              >
                <span
                  className={`h-2 w-2 rounded-full ${DOT[c.status]}`}
                  aria-hidden
                />
                {c.name}
              </button>
            </li>
          ))}
        </ul>
      )}
      {detail && (
        <p className="mt-3 break-words text-xs text-[var(--muted)]">
          <span className="font-medium text-[var(--text)]">{detail.name}</span>{" "}
          · {WORD[detail.status]} · {detail.detail}
        </p>
      )}
    </section>
  );
}
