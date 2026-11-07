"use client";

import {
  BarChart3,
  Bell,
  Box,
  Command,
  Database,
  Folder,
  Home,
  Layers,
  Search,
  Settings,
  Sparkles,
  Workflow,
  X,
  type LucideIcon,
} from "lucide-react";
import { useEffect, useLayoutEffect, useMemo, useRef, useState, type ReactNode } from "react";

import { MascotFace } from "@/components/dash/Mascot";
import type { View } from "@/lib/dashboard";

export const TABS: [View, string, LucideIcon][] = [
  ["overview", "Overview", Home],
  ["discover", "Discover", Sparkles],
  ["files", "Files", Folder],
  ["agents", "Agents", Workflow],
  ["analysis", "Analysis", BarChart3],
  ["settings", "Settings", Settings],
];

const RAIL: [View, string, LucideIcon][] = [
  ["overview", "Overview", Home],
  ["discover", "Discover", Sparkles],
  ["files", "Files", Folder],
  ["agents", "Agents", Layers],
  ["analysis", "Analysis", BarChart3],
  ["projects", "Projects", Box],
  ["lab", "Lab", Command],
  ["memory", "Memory", Database],
  ["settings", "Settings", Settings],
];

export type PaletteCommand = { id: string; label: string; hint?: string; run: () => void };

export function TopBar({
  view,
  onView,
  onSearch,
  notifications,
  name,
  menu,
  badges = {},
}: {
  badges?: Partial<Record<View, number>>;
  view: View;
  onView: (v: View) => void;
  onSearch: () => void;
  notifications: { id: string; text: string; when: string }[];
  name: string;
  menu: ReactNode;
}) {
  const [open, setOpen] = useState<"bell" | "me" | null>(null);
  const ref = useRef<HTMLDivElement>(null);
  // The active-tab highlight is one element that slides between tabs.
  const tabRefs = useRef<Partial<Record<View, HTMLButtonElement | null>>>({});
  const [pill, setPill] = useState<{ left: number; width: number } | null>(null);
  useLayoutEffect(() => {
    const place = () => {
      const el = tabRefs.current[view];
      setPill(el ? { left: el.offsetLeft, width: el.offsetWidth } : null);
    };
    place();
    addEventListener("resize", place);
    return () => removeEventListener("resize", place);
  }, [view]);
  useEffect(() => {
    if (!open) return;
    const close = (e: MouseEvent | KeyboardEvent) => {
      if (e instanceof KeyboardEvent ? e.key === "Escape" : !ref.current?.contains(e.target as Node)) setOpen(null);
    };
    document.addEventListener("mousedown", close);
    document.addEventListener("keydown", close);
    return () => {
      document.removeEventListener("mousedown", close);
      document.removeEventListener("keydown", close);
    };
  }, [open]);

  return (
    <header className="flex items-center gap-4 px-4 py-3 lg:px-6">
      <a href="#" onClick={(e) => (e.preventDefault(), onView("overview"))} className="flex shrink-0 items-center gap-3">
        <MascotFace size={40} animate={false} className="drop-shadow-[0_0_10px_rgba(255,64,85,0.5)]" />
        <span className="hidden leading-tight sm:block">
          <span className="block text-[22px] font-semibold tracking-[0.42em] text-[var(--text)]">REX</span>
          <span className="block text-[9px] tracking-[0.32em] text-[var(--text-2)]">INTELLIGENT CONTROL CENTER</span>
        </span>
      </a>

      <nav aria-label="Main" className="mx-auto min-w-0 overflow-x-auto">
        <ul className="relative flex items-center gap-1 rounded-[14px] border border-[var(--line)] bg-white/[0.02] p-1">
          {pill && (
            <li
              aria-hidden
              className="pointer-events-none absolute top-1 bottom-1 rounded-[10px] border border-[var(--line-active)] bg-[var(--red-glow)] shadow-[0_0_18px_rgba(255,64,85,0.18)] transition-[left,width] duration-300 ease-[cubic-bezier(0.2,0.8,0.2,1)]"
              style={{ left: pill.left, width: pill.width }}
            />
          )}
          {TABS.map(([v, label, Icon]) => (
            <li key={v}>
              <button
                ref={(el) => {
                  tabRefs.current[v] = el;
                }}
                onClick={() => onView(v)}
                aria-current={view === v ? "page" : undefined}
                className={`relative flex items-center gap-2 whitespace-nowrap rounded-[10px] border border-transparent px-3.5 py-2 text-sm transition-colors ${
                  view === v ? "text-[var(--text)]" : "text-[var(--text-2)] hover:text-[var(--text)]"
                }`}
              >
                <Icon className="size-4" aria-hidden />
                <span className="hidden md:inline">{label}</span>
                {!!badges[v] && (
                  <span className="grid min-w-5 place-items-center rounded-full bg-[var(--red)] px-1.5 text-[10px] font-semibold text-white" aria-label={`${badges[v]} new`}>
                    {badges[v]}
                  </span>
                )}
              </button>
            </li>
          ))}
        </ul>
      </nav>

      <div ref={ref} className="flex shrink-0 items-center gap-3">
        <button
          onClick={onSearch}
          className="hidden items-center gap-2 rounded-[12px] border border-[var(--line)] bg-white/[0.02] px-3 py-2 text-sm text-[var(--text-2)] hover:text-[var(--text)] xl:flex"
        >
          <Search className="size-4" aria-hidden />
          <span className="w-44 whitespace-nowrap text-left">Search or run a command…</span>
          <kbd className="rounded-md border border-[var(--line)] px-1.5 text-[11px]">⌘K</kbd>
        </button>
        <button onClick={onSearch} aria-label="Search or run a command" className="xl:hidden">
          <Search className="size-5 text-[var(--text-2)]" />
        </button>
        <div className="relative">
          <button onClick={() => setOpen(open === "bell" ? null : "bell")} aria-label="Notifications" aria-expanded={open === "bell"} className="relative grid size-9 place-items-center">
            <Bell className="size-5 text-[var(--text-2)]" />
            {notifications.length > 0 && <span className="absolute right-1.5 top-1.5 size-2 rounded-full bg-[var(--red)]" aria-hidden />}
          </button>
          {open === "bell" && (
            <div className="pop-in panel absolute right-0 top-11 z-40 w-80 p-3" role="dialog" aria-label="Notifications">
              <p className="mb-2 text-sm font-medium">Notifications</p>
              {notifications.length === 0 ? (
                <p className="text-sm text-[var(--text-2)]">You&apos;re all caught up.</p>
              ) : (
                <ul className="flex max-h-72 flex-col gap-2 overflow-y-auto">
                  {notifications.map((n) => (
                    <li key={n.id} className="rounded-lg bg-white/[0.03] px-3 py-2 text-[13px]">
                      {n.text}
                      <span className="mt-0.5 block text-[11px] text-[var(--text-2)]">{n.when}</span>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          )}
        </div>
        <div className="relative">
          <button
            onClick={() => setOpen(open === "me" ? null : "me")}
            aria-label="Account menu"
            aria-expanded={open === "me"}
            className="grid size-10 place-items-center rounded-full border border-[var(--line-active)] bg-gradient-to-br from-[#3a1a20] to-[#16121a] text-sm font-semibold"
          >
            {name.slice(0, 1).toUpperCase()}
          </button>
          {open === "me" && (
            <div className="pop-in panel absolute right-0 top-12 z-40 w-60 p-2" role="menu" onClick={() => setOpen(null)}>
              {menu}
            </div>
          )}
        </div>
      </div>
    </header>
  );
}

export function Rail({ view, onView }: { view: View; onView: (v: View) => void }) {
  return (
    <nav aria-label="Sections" className="panel sticky top-4 hidden w-[68px] shrink-0 flex-col items-center gap-3 self-start py-4 lg:flex">
      {RAIL.map(([v, label, Icon]) => (
        <button
          key={v}
          onClick={() => onView(v)}
          aria-label={label}
          aria-current={view === v ? "page" : undefined}
          className={`group relative grid size-11 place-items-center rounded-[12px] border transition-colors ${
            view === v
              ? "border-[var(--line-active)] bg-[var(--red-glow)] text-[var(--red-hi)] shadow-[0_0_18px_rgba(255,64,85,0.25)]"
              : "border-transparent text-[var(--text-2)] hover:text-[var(--text)]"
          }`}
        >
          <Icon className="size-5" aria-hidden />
          <span className="pointer-events-none absolute left-14 z-30 whitespace-nowrap rounded-md bg-[var(--elevated)] px-2 py-1 text-xs text-[var(--text)] opacity-0 transition-opacity group-hover:opacity-100 group-focus-visible:opacity-100">
            {label}
          </span>
        </button>
      ))}
    </nav>
  );
}

export function Drawer({ title, onClose, children, wide = false }: { title: string; onClose: () => void; children: ReactNode; wide?: boolean }) {
  const ref = useRef<HTMLDivElement>(null);
  // Set up once: during a call the parent re-renders many times a second (voice levels), and re-running this
  // on every render kept moving focus and re-adding the Esc listener.
  const close = useRef(onClose);
  close.current = onClose;
  useEffect(() => {
    const prev = document.activeElement as HTMLElement | null;
    ref.current?.focus();
    const esc = (e: KeyboardEvent) => e.key === "Escape" && close.current();
    document.addEventListener("keydown", esc);
    return () => {
      document.removeEventListener("keydown", esc);
      prev?.focus();
    };
  }, []);
  return (
    <div className="fixed inset-0 z-50 flex justify-end" role="dialog" aria-modal="true" aria-label={title}>
      <button className="absolute inset-0 bg-black/55" aria-label="Close" onClick={onClose} tabIndex={-1} />
      <div
        ref={ref}
        tabIndex={-1}
        className={`drawer-in relative flex h-full w-full flex-col border-l border-[var(--line)] bg-[var(--bg-2)] outline-none ${wide ? "max-w-2xl" : "max-w-md"}`}
      >
        <header className="flex items-center justify-between border-b border-[var(--line)] px-5 py-4">
          <h2 className="text-lg font-semibold">{title}</h2>
          <button onClick={onClose} aria-label="Close" className="grid size-8 place-items-center rounded-lg hover:bg-white/5">
            <X className="size-4" />
          </button>
        </header>
        <div className="min-h-0 flex-1 overflow-y-auto p-5">{children}</div>
      </div>
    </div>
  );
}

export function CommandPalette({ commands, onClose, onAsk }: { commands: PaletteCommand[]; onClose: () => void; onAsk: (q: string) => void }) {
  const [q, setQ] = useState("");
  const [i, setI] = useState(0);
  const list = useMemo(() => {
    const hits = commands.filter((c) => c.label.toLowerCase().includes(q.toLowerCase()));
    return q.trim() ? [...hits, { id: "ask", label: `Ask Rex: “${q.trim()}”`, run: () => onAsk(q.trim()) }] : hits;
  }, [commands, q, onAsk]);
  const run = (c: PaletteCommand | undefined) => {
    if (!c) return;
    onClose();
    c.run();
  };
  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center px-4 pt-[14vh]" role="dialog" aria-modal="true" aria-label="Command palette">
      <button className="absolute inset-0 bg-black/60" aria-label="Close" onClick={onClose} tabIndex={-1} />
      <div className="pop-in panel relative w-full max-w-lg overflow-hidden">
        <div className="flex items-center gap-3 border-b border-[var(--line)] px-4">
          <Search className="size-4 text-[var(--text-2)]" aria-hidden />
          <input
            autoFocus
            value={q}
            onChange={(e) => (setQ(e.target.value), setI(0))}
            onKeyDown={(e) => {
              if (e.key === "Escape") onClose();
              else if (e.key === "ArrowDown") {
                e.preventDefault();
                setI((n) => Math.min(n + 1, list.length - 1));
              } else if (e.key === "ArrowUp") {
                e.preventDefault();
                setI((n) => Math.max(n - 1, 0));
              }
              else if (e.key === "Enter") run(list[i]);
            }}
            placeholder="Type a command or ask Rex…"
            aria-label="Command"
            className="h-12 flex-1 bg-transparent text-sm outline-none placeholder:text-[var(--faint)]"
          />
          <kbd className="rounded-md border border-[var(--line)] px-1.5 text-[11px] text-[var(--text-2)]">Esc</kbd>
        </div>
        <ul className="max-h-80 overflow-y-auto p-2" role="listbox">
          {list.map((c, n) => (
            <li key={c.id} role="option" aria-selected={n === i}>
              <button
                onMouseEnter={() => setI(n)}
                onClick={() => run(c)}
                className={`flex w-full items-center justify-between rounded-lg px-3 py-2 text-left text-sm ${n === i ? "bg-[var(--red-glow)]" : ""}`}
              >
                {c.label}
                {c.hint && <span className="text-xs text-[var(--text-2)]">{c.hint}</span>}
              </button>
            </li>
          ))}
          {list.length === 0 && <li className="px-3 py-2 text-sm text-[var(--text-2)]">No matching command.</li>}
        </ul>
      </div>
    </div>
  );
}
