"use client";

import {
  Activity,
  Bot,
  Box,
  ChevronDown,
  Circle,
  CircleCheck,
  CircleX,
  Clock,
  Cloud,
  Code2,
  Cpu,
  Droplet,
  HardDrive,
  Layers,
  MemoryStick,
  MonitorSmartphone,
  Rocket,
  Search,
  ShieldCheck,
  Sprout,
  Wifi,
  Workflow,
  Zap,
} from "lucide-react";
import { useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import {
  DEMO,
  completion,
  type ActionEvent,
  type AgentInfo,
  type AgentStatus,
  type DemoActivity,
  type Project,
  type ResourceRange,
  type TaskPeriod,
  type TaskSummary,
} from "@/lib/dashboard";

export function Panel({
  title,
  right,
  children,
  className = "",
  label,
}: {
  title: string;
  right?: ReactNode;
  children: ReactNode;
  className?: string;
  label?: string;
}) {
  return (
    <section className={`panel flex min-w-0 flex-col p-5 ${className}`} aria-label={label ?? title}>
      <header className="mb-3.5 flex items-center justify-between gap-3">
        <h2 className="text-[17px] font-semibold tracking-tight text-[var(--text)]">{title}</h2>
        {right}
      </header>
      {children}
    </section>
  );
}

export const DemoTag = () => (
  <span
    className="rounded-md border border-[var(--line)] px-1.5 py-0.5 text-[10px] font-medium uppercase tracking-wider text-[var(--faint)]"
    title="Illustrative data: no live source is connected for this panel yet"
  >
    Demo
  </span>
);

export const StatusDot = ({ tone = "ok", pulse = false }: { tone?: "ok" | "warn" | "danger" | "idle"; pulse?: boolean }) => (
  <span
    aria-hidden
    className={`inline-block size-2 rounded-full ${pulse ? "live-dot" : ""} ${
      { ok: "bg-[var(--ok)]", warn: "bg-[var(--warn)]", danger: "bg-[var(--danger)]", idle: "bg-[var(--faint)]" }[tone]
    }`}
  />
);

function Ring({ value, size, stroke, children }: { value: number; size: number; stroke: number; children?: ReactNode }) {
  const r = (size - stroke) / 2;
  const c = 2 * Math.PI * r;
  const [shown, setShown] = useState(0);
  useEffect(() => {
    const id = requestAnimationFrame(() => setShown(value));
    return () => cancelAnimationFrame(id);
  }, [value]);
  return (
    <div className="relative shrink-0" style={{ width: size, height: size }}>
      <svg viewBox={`0 0 ${size} ${size}`} className="-rotate-90" aria-hidden>
        <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth={stroke} />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={r}
          fill="none"
          stroke="var(--red)"
          strokeWidth={stroke}
          strokeLinecap="round"
          strokeDasharray={c}
          strokeDashoffset={c * (1 - shown / 100)}
          style={{ transition: "stroke-dashoffset 1100ms cubic-bezier(0.2,0.8,0.2,1)", filter: "drop-shadow(0 0 6px rgba(255,64,85,0.45))" }}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center text-center">{children}</div>
    </div>
  );
}

function useMounted() {
  const [on, setOn] = useState(false);
  useEffect(() => {
    const id = requestAnimationFrame(() => setOn(true));
    return () => cancelAnimationFrame(id);
  }, []);
  return on;
}

// Counts a number up from 0 (or from its last value) so metrics settle in instead of popping.
export function useCountUp(target: number, ms = 900) {
  const [shown, setShown] = useState(0);
  const from = useRef(0);
  useEffect(() => {
    if (matchMedia("(prefers-reduced-motion: reduce)").matches) {
      setShown(target);
      from.current = target;
      return;
    }
    const start = performance.now();
    const a = from.current;
    let raf = 0;
    const tick = (now: number) => {
      const p = Math.min(1, (now - start) / ms);
      const v = a + (target - a) * (1 - Math.pow(1 - p, 3));
      setShown(v);
      if (p < 1) raf = requestAnimationFrame(tick);
      else from.current = target;
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [target, ms]);
  return shown;
}

function CountUp({ value, decimals = 0 }: { value: number; decimals?: number }) {
  return <>{useCountUp(value).toFixed(decimals)}</>;
}

function Bar({ value }: { value: number }) {
  const on = useMounted();
  return (
    <div className="h-[5px] w-full rounded-full bg-white/[0.06]">
      <div
        className="grow h-full rounded-full bg-gradient-to-r from-[var(--red-deep)] to-[var(--red)]"
        style={{ width: `${on ? value : 0}%` }}
      />
    </div>
  );
}

// ---------- System Health (demo: a browser can't read the OS's CPU/GPU) ----------
export function SystemHealth() {
  const [m, setM] = useState(DEMO.metrics);
  useEffect(() => {
    const id = setInterval(
      () =>
        setM((p) => ({
          ...p,
          cpu: clamp(p.cpu + rnd(4), 12, 70),
          gpu: clamp(p.gpu + rnd(5), 15, 80),
          networkMbps: clamp(p.networkMbps + rnd(18), 90, 260),
        })),
      3000,
    );
    return () => clearInterval(id);
  }, []);
  const rows = [
    { icon: Cpu, label: "CPU", value: m.cpu, text: `${m.cpu}%` },
    { icon: MemoryStick, label: "Memory", value: (m.memoryUsedGb / m.memoryTotalGb) * 100, text: `${m.memoryUsedGb} / ${m.memoryTotalGb} GB` },
    { icon: HardDrive, label: "GPU", value: m.gpu, text: `${m.gpu}%` },
    { icon: Wifi, label: "Network", value: (m.networkMbps / 300) * 100, text: `${m.networkMbps} Mbps` },
  ];
  return (
    <Panel
      title="System Health"
      right={
        <span className="flex items-center gap-2 text-xs text-[var(--text-2)]">
          <DemoTag />
          <StatusDot /> Optimal
        </span>
      }
    >
      <div className="flex items-center gap-6">
        <Ring value={m.health} size={116} stroke={9}>
          <span className="tabular text-[28px] font-semibold leading-none">
            <CountUp value={m.health} />%
          </span>
          <span className="mt-1 text-[11px] text-[var(--text-2)]">Health Score</span>
        </Ring>
        <ul className="flex min-w-0 flex-1 flex-col gap-3">
          {rows.map(({ icon: Icon, label, value, text }) => (
            <li key={label} className="grid grid-cols-[18px_64px_1fr] items-center gap-x-2 gap-y-1 text-[13px]">
              <Icon className="size-4 text-[var(--text-2)]" aria-hidden />
              <span>{label}</span>
              <span className="tabular text-right text-xs text-[var(--text-2)]">{text}</span>
              <span className="col-start-3">
                <Bar value={value} />
              </span>
            </li>
          ))}
        </ul>
      </div>
    </Panel>
  );
}

// ---------- Task Progress (session = live from Rex's actions when connected) ----------
export function TaskProgress({ live }: { live: TaskSummary | null }) {
  const [period, setPeriod] = useState<TaskPeriod>("session");
  const isLive = period === "session" && live !== null;
  const t = isLive ? live : DEMO.tasks[period];
  const rows = [
    { label: "Completed", n: t.completed, cls: "bg-[var(--red)]" },
    { label: "In Progress", n: t.inProgress, cls: "bg-[var(--red-hi)]/60" },
    { label: "Queued", n: t.queued, cls: "bg-[var(--faint)]" },
  ];
  return (
    <Panel
      title="Task Progress"
      right={
        <span className="flex items-center gap-2">
          {!isLive && <DemoTag />}
          <label className="relative flex items-center text-xs text-[var(--text-2)]">
            <span className="sr-only">Period</span>
            <select
              value={period}
              onChange={(e) => setPeriod(e.target.value as TaskPeriod)}
              className="appearance-none bg-transparent pr-5 outline-none"
            >
              <option value="session">This Session</option>
              <option value="today">Today</option>
              <option value="week">This Week</option>
            </select>
            <ChevronDown className="pointer-events-none absolute right-0 size-3.5" aria-hidden />
          </label>
        </span>
      }
    >
      <div className="flex items-center gap-6">
        <Ring value={completion(t)} size={96} stroke={8}>
          <span className="tabular text-[22px] font-semibold leading-none">
            <CountUp value={completion(t)} />%
          </span>
          <span className="mt-1 text-[10px] text-[var(--text-2)]">Completed</span>
        </Ring>
        <ul className="flex flex-1 flex-col gap-2.5 text-[13px]">
          {rows.map((r) => (
            <li key={r.label} className="flex items-center gap-2.5">
              <span className={`size-2.5 rounded-[3px] ${r.cls}`} aria-hidden />
              <span className="flex-1">{r.label}</span>
              <span className="tabular text-[var(--text-2)]">{r.n}</span>
            </li>
          ))}
        </ul>
      </div>
    </Panel>
  );
}

// ---------- Active Agents ----------
export type AgentRow = AgentInfo & { status: AgentStatus; spark: number[]; current: string };

const STATUS_TONE: Record<AgentStatus, "ok" | "warn" | "danger" | "idle"> = {
  running: "ok",
  idle: "idle",
  paused: "warn",
  error: "danger",
};
const AGENT_ICON: Record<string, typeof Bot> = { rex: Bot, desktop: MonitorSmartphone, web: Search, comms: Workflow };

function Sparkline({ data }: { data: number[] }) {
  const max = Math.max(1, ...data);
  const idle = data.every((v) => v === 0);
  const pts = data.map((v, i) => `${(i / (data.length - 1)) * 100},${22 - (v / max) * 18}`).join(" ");
  return (
    <svg viewBox="0 0 100 24" className="h-6 w-24 shrink-0" preserveAspectRatio="none" aria-hidden>
      {idle ? (
        <line x1="0" x2="100" y1="20" y2="20" stroke="var(--faint)" strokeWidth="1" strokeDasharray="2 4" vectorEffect="non-scaling-stroke" />
      ) : (
        <polyline points={pts} fill="none" stroke="var(--red)" strokeWidth="1.5" vectorEffect="non-scaling-stroke" />
      )}
    </svg>
  );
}

export function StatusPill({ status }: { status: AgentStatus }) {
  return (
    <span className="flex items-center gap-1.5 rounded-full bg-white/[0.04] px-2.5 py-1 text-xs capitalize text-[var(--text-2)]">
      <StatusDot tone={STATUS_TONE[status]} pulse={status === "running"} />
      {status}
    </span>
  );
}

export function ActiveAgents({ rows, onSelect }: { rows: AgentRow[]; onSelect: (id: string) => void }) {
  const running = rows.filter((r) => r.status === "running").length;
  return (
    <Panel
      title="Active Agents"
      right={
        <span className="flex items-center gap-2 text-xs text-[var(--text-2)]">
          <StatusDot tone={running ? "ok" : "idle"} /> {running} Running
        </span>
      }
    >
      <ul className="flex flex-col divide-y divide-[var(--line)]">
        {rows.map((a) => {
          const Icon = AGENT_ICON[a.id] ?? Bot;
          return (
            <li key={a.id}>
              <button
                onClick={() => onSelect(a.id)}
                className="flex w-full items-center gap-3 rounded-lg py-2 text-left transition-colors hover:bg-white/[0.025]"
              >
                <span className="grid size-9 shrink-0 place-items-center rounded-[10px] border border-[var(--line)] bg-white/[0.03]">
                  <Icon className="size-4 text-[var(--text-2)]" aria-hidden />
                </span>
                <span className="min-w-0 flex-1">
                  <span className="block text-sm font-medium">{a.name}</span>
                  <span className="block truncate text-xs text-[var(--text-2)]">{a.role}</span>
                </span>
                <StatusPill status={a.status} />
                <span className="hidden 2xl:block">
                  <Sparkline data={a.spark} />
                </span>
              </button>
            </li>
          );
        })}
      </ul>
    </Panel>
  );
}

// ---------- Global Activity (SVG orthographic globe) ----------
const CITIES: [number, number][] = [
  [12.97, 77.59], [19.07, 72.88], [28.61, 77.21], [1.35, 103.82], [25.2, 55.27], [51.51, -0.13], [50.11, 8.68],
  [40.71, -74.0], [37.77, -122.42], [35.68, 139.69], [-33.87, 151.21], [-23.55, -46.63], [-1.29, 36.82],
  [37.57, 126.98], [43.65, -79.38], [22.32, 114.17],
];
const RAD = Math.PI / 180;

function project(lat: number, lon: number, rot: number, tilt: number, r: number): [number, number, boolean] {
  const φ = lat * RAD;
  const λ = (lon + rot) * RAD;
  const φ0 = tilt * RAD;
  const x = Math.cos(φ) * Math.sin(λ);
  const y = Math.cos(φ0) * Math.sin(φ) - Math.sin(φ0) * Math.cos(φ) * Math.cos(λ);
  const z = Math.sin(φ0) * Math.sin(φ) + Math.cos(φ0) * Math.cos(φ) * Math.cos(λ);
  return [r + x * r, r - y * r, z > 0];
}

function Globe({ animate }: { animate: boolean }) {
  const [rot, setRot] = useState(-78);
  useEffect(() => {
    if (!animate) return;
    let raf = 0;
    let last = performance.now();
    const tick = (now: number) => {
      if (now - last > 50) {
        setRot((r) => r - ((now - last) / 1000) * 4); // 4°/s: slow, subtle
        last = now;
      }
      raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [animate]);

  const R = 90;
  const tilt = 18;
  const line = (pts: [number, number, boolean][]) => {
    let d = "";
    let pen = false;
    for (const [x, y, v] of pts) {
      d += v ? `${pen ? "L" : "M"}${x.toFixed(1)} ${y.toFixed(1)}` : "";
      pen = v;
    }
    return d;
  };
  const grid: string[] = [];
  for (let lon = -180; lon < 180; lon += 30)
    grid.push(line(Array.from({ length: 37 }, (_, i) => project(-90 + i * 5, lon, rot, tilt, R))));
  for (let lat = -60; lat <= 60; lat += 30)
    grid.push(line(Array.from({ length: 73 }, (_, i) => project(lat, -180 + i * 5, rot, tilt, R))));
  const hub = CITIES[0];
  const arcs = CITIES.slice(1).map(([lat, lon]) =>
    line(
      Array.from({ length: 25 }, (_, i) => {
        const t = i / 24;
        return project(hub[0] + (lat - hub[0]) * t, hub[1] + (lon - hub[1]) * t, rot, tilt, R);
      }),
    ),
  );
  return (
    <svg viewBox={`-6 -6 ${2 * R + 12} ${2 * R + 12}`} className="size-full" aria-hidden>
      <defs>
        <radialGradient id="globe-fill" cx="0.4" cy="0.35" r="0.75">
          <stop offset="0" stopColor="#3a1a20" />
          <stop offset="1" stopColor="#0c0a0d" />
        </radialGradient>
      </defs>
      <circle cx={R} cy={R} r={R} fill="url(#globe-fill)" stroke="var(--red)" strokeOpacity="0.35" />
      {grid.map((d, i) => (
        <path key={i} d={d} fill="none" stroke="var(--red)" strokeOpacity="0.14" strokeWidth="0.7" />
      ))}
      {arcs.map((d, i) => (
        <path key={i} d={d} fill="none" stroke="var(--red-hi)" strokeOpacity="0.55" strokeWidth="0.9" />
      ))}
      {CITIES.map(([lat, lon], i) => {
        const [x, y, v] = project(lat, lon, rot, tilt, R);
        return v ? <circle key={i} cx={x} cy={y} r={i === 0 ? 3 : 1.8} fill={i === 0 ? "#fff" : "var(--red-hi)"} /> : null;
      })}
      <ellipse cx={R} cy={R} rx={R + 14} ry={22} fill="none" stroke="var(--red)" strokeOpacity="0.25" transform={`rotate(-14 ${R} ${R})`} />
    </svg>
  );
}

export function GlobalActivity({ animate }: { animate: boolean }) {
  const g = DEMO.globe;
  const stats = [
    { icon: ShieldCheck, value: g.tasks, label: "Tasks Processed", delta: g.tasksDelta },
    { icon: Cloud, value: g.data, label: "Data Handled", delta: g.dataDelta },
    { icon: Workflow, value: String(g.workflows), label: "Active Workflows", delta: g.workflowsDelta },
  ];
  return (
    <Panel title="Global Activity" right={<DemoTag />}>
      <div className="flex flex-col items-center gap-4 sm:flex-row">
        <div className="aspect-square w-[60%] max-w-[190px] shrink-0 sm:w-[34%]">
          <Globe animate={animate} />
        </div>
        <ul className="flex w-full min-w-0 flex-1 flex-col divide-y divide-[var(--line)]">
          {stats.map(({ icon: Icon, value, label, delta }) => (
            <li key={label} className="flex items-center gap-3 py-2">
              <span className="grid size-9 shrink-0 place-items-center rounded-[10px] border border-[var(--line)]">
                <Icon className="size-4 text-[var(--text-2)]" aria-hidden />
              </span>
              <span className="min-w-0 flex-1">
                <span className="tabular block text-xl font-semibold leading-tight">
                  <CountUp value={parseFloat(value)} decimals={value.includes(".") ? 1 : 0} />
                  {value.replace(/^[\d.]+/, "")}
                </span>
                <span className="block whitespace-nowrap text-xs text-[var(--text-2)]">{label}</span>
              </span>
              <span className="tabular text-xs text-[var(--ok)]">▲ +{delta}%</span>
            </li>
          ))}
        </ul>
      </div>
    </Panel>
  );
}

// ---------- Projects ----------
const PROJECT_ICON = { sprout: Sprout, zap: Zap, droplet: Droplet, circle: Circle, layers: Layers, box: Box };

export function Projects({ onSelect, onViewAll }: { onSelect: (p: Project) => void; onViewAll?: () => void }) {
  return (
    <Panel
      title="Projects"
      right={
        <span className="flex items-center gap-3">
          <DemoTag />
          {onViewAll && (
            <button onClick={onViewAll} className="text-xs text-[var(--text-2)] hover:text-[var(--text)]">
              View All →
            </button>
          )}
        </span>
      }
    >
      <ul className="grid grid-cols-2 gap-3 md:grid-cols-3">
        {DEMO.projects.map((p) => {
          const Icon = PROJECT_ICON[p.icon];
          return (
            <li key={p.id}>
              <button
                onClick={() => onSelect(p)}
                className="lift flex h-full w-full flex-col gap-2.5 rounded-[12px] border border-[var(--line)] bg-white/[0.02] p-3 text-left hover:bg-white/[0.035]"
              >
                <span className="flex items-center gap-2">
                  <Icon className="size-4 shrink-0 text-[var(--red-hi)]" aria-hidden />
                  <span className="text-[13px] font-medium leading-tight">{p.name}</span>
                </span>
                <span className="-mt-1 line-clamp-1 text-[11px] text-[var(--text-2)]">{p.description}</span>
                <span className="flex items-center gap-2">
                  <Bar value={p.progress} />
                  <span className="tabular text-xs text-[var(--text-2)]">{p.progress}%</span>
                </span>
              </button>
            </li>
          );
        })}
      </ul>
    </Panel>
  );
}

// ---------- Recent Activity (live actions; demo events until the first call) ----------
type Filter = "all" | "approval" | "done" | "failed";
const FILTERS: [Filter, string][] = [
  ["all", "All"],
  ["approval", "Needs OK"],
  ["done", "Done"],
  ["failed", "Failed"],
];
const DEMO_ICON = { validation: CircleCheck, review: Box, code: Code2, deploy: Rocket, workflow: Workflow };

function ago(ts: string | number) {
  const m = Math.round((Date.now() - new Date(ts).getTime()) / 60000);
  return m < 1 ? "just now" : m < 60 ? `${m} min ago` : `${Math.round(m / 60)} h ago`;
}

export function openApprovals(events: ActionEvent[]) {
  const closed = new Set(events.filter((e) => e.status !== "awaiting_approval" && e.trace_id).map((e) => e.trace_id));
  return new Set(events.filter((e) => e.status === "awaiting_approval" && e.trace_id && !closed.has(e.trace_id)).map((e) => e.id));
}

export function ActivityList({
  events,
  onDecide,
  deciding,
  limit,
}: {
  events: ActionEvent[];
  onDecide: (actionId: string, d: "approve" | "deny") => void;
  deciding: string | null;
  limit?: number;
}) {
  const [filter, setFilter] = useState<Filter>("all");
  const open = useMemo(() => openApprovals(events), [events]);
  const shown = events
    .filter((e) =>
      filter === "all"
        ? true
        : filter === "approval"
          ? open.has(e.id)
          : filter === "done"
            ? e.status === "succeeded"
            : e.status === "failed" || e.status === "denied",
    )
    .slice(0, limit);
  return (
    <>
      <div className="mb-3 flex gap-1" role="group" aria-label="Filter activity">
        {FILTERS.map(([f, label]) => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            aria-pressed={filter === f}
            className={`rounded-md px-2 py-1 text-[11px] ${filter === f ? "bg-[var(--red-glow)] text-[var(--text)]" : "text-[var(--text-2)] hover:text-[var(--text)]"}`}
          >
            {label}
            {f === "approval" && open.size > 0 && <span className="ml-1 text-[var(--red-hi)]">{open.size}</span>}
          </button>
        ))}
      </div>
      {shown.length === 0 && <p className="text-sm text-[var(--text-2)]">Nothing here yet.</p>}
      <ol className="relative flex flex-col">
        {shown.map((e) => {
          const Icon = e.status === "failed" ? CircleX : e.status === "awaiting_approval" ? Clock : e.status === "started" ? Activity : CircleCheck;
          return (
            <li key={e.id} className="rise relative flex gap-3 pb-3 pl-5 before:absolute before:left-[3px] before:top-3 before:h-full before:w-px before:bg-[var(--line)] last:before:hidden">
              <span className="absolute left-0 top-2.5 size-[7px] rounded-full bg-[var(--red)]" aria-hidden />
              <span className="grid size-8 shrink-0 place-items-center rounded-[9px] border border-[var(--line)]">
                <Icon className={`size-4 ${e.status === "failed" ? "text-[var(--danger)]" : "text-[var(--text-2)]"}`} aria-hidden />
              </span>
              <div className="min-w-0 flex-1">
                <p className="text-[13px] leading-snug">{e.summary}</p>
                <p className="mt-0.5 font-mono text-[10px] text-[var(--faint)]">{e.tool}</p>
                {e.result_redacted?.error && <p className="mt-1 text-xs text-[var(--danger)]">{e.result_redacted.error}</p>}
                {open.has(e.id) && (
                  <div className="mt-2 flex gap-2">
                    <button
                      onClick={() => onDecide(e.trace_id as string, "approve")}
                      disabled={deciding === e.trace_id}
                      className="rounded-lg bg-[var(--red)] px-3 py-1 text-xs font-medium text-white disabled:opacity-50"
                    >
                      Approve
                    </button>
                    <button
                      onClick={() => onDecide(e.trace_id as string, "deny")}
                      disabled={deciding === e.trace_id}
                      className="rounded-lg border border-[var(--line)] px-3 py-1 text-xs text-[var(--text-2)]"
                    >
                      Deny
                    </button>
                  </div>
                )}
              </div>
              <time className="tabular shrink-0 pt-0.5 text-[11px] text-[var(--text-2)]">{ago(e.ts)}</time>
            </li>
          );
        })}
      </ol>
    </>
  );
}

export function RecentActivity({
  events,
  onDecide,
  deciding,
  onViewAll,
}: {
  events: ActionEvent[];
  onDecide: (actionId: string, d: "approve" | "deny") => void;
  deciding: string | null;
  onViewAll: () => void;
}) {
  const live = events.length > 0;
  return (
    <Panel
      title="Recent Activity"
      right={
        <span className="flex items-center gap-3">
          {!live && <DemoTag />}
          <button onClick={onViewAll} className="text-xs text-[var(--text-2)] hover:text-[var(--text)]">
            View All →
          </button>
        </span>
      }
    >
      {live ? (
        <ActivityList events={events} onDecide={onDecide} deciding={deciding} limit={4} />
      ) : (
        <ol className="flex flex-col">
          {DEMO.activity.slice(0, 4).map((a: DemoActivity) => {
            const Icon = DEMO_ICON[a.kind];
            return (
              <li key={a.id} className="relative flex items-center gap-3 py-1.5 pl-5 before:absolute before:left-[3px] before:top-1/2 before:h-full before:w-px before:bg-[var(--line)] last:before:hidden">
                <span className="absolute left-0 top-1/2 size-[7px] -translate-y-1/2 rounded-full bg-[var(--red)]" aria-hidden />
                <span className="grid size-8 shrink-0 place-items-center rounded-[9px] border border-[var(--line)]">
                  <Icon className="size-4 text-[var(--text-2)]" aria-hidden />
                </span>
                <span className="flex-1 text-[13px]">{a.text}</span>
                <span className="tabular text-[11px] text-[var(--text-2)]">{a.minutesAgo} min ago</span>
              </li>
            );
          })}
        </ol>
      )}
    </Panel>
  );
}

// ---------- Resource Utilization ----------
const SERIES = [
  { key: "cpu", name: "CPU", color: "#ff4055" },
  { key: "memory", name: "Memory", color: "#c9a1a8" },
  { key: "gpu", name: "GPU", color: "#ff8c96" },
] as const;

export function ResourceChart({ tall = false }: { tall?: boolean }) {
  const [range, setRange] = useState<ResourceRange>("30m");
  const data = DEMO.resources[range];
  return (
    <Panel
      title="Resource Utilization"
      right={
        <span className="flex items-center gap-2">
          <DemoTag />
          <label className="relative flex items-center text-xs text-[var(--text-2)]">
            <span className="sr-only">Time range</span>
            <select value={range} onChange={(e) => setRange(e.target.value as ResourceRange)} className="appearance-none bg-transparent pr-5 outline-none">
              <option value="30m">Last 30 min</option>
              <option value="1h">Last hour</option>
              <option value="24h">Last 24 hours</option>
            </select>
            <ChevronDown className="pointer-events-none absolute right-0 size-3.5" aria-hidden />
          </label>
        </span>
      }
    >
      <div className={tall ? "h-72" : "h-36"}>
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data} margin={{ top: 4, right: 4, bottom: 0, left: -18 }}>
            <defs>
              {SERIES.map((s) => (
                <linearGradient key={s.key} id={`fill-${s.key}`} x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0" stopColor={s.color} stopOpacity={0.22} />
                  <stop offset="1" stopColor={s.color} stopOpacity={0} />
                </linearGradient>
              ))}
            </defs>
            <CartesianGrid stroke="rgba(255,255,255,0.05)" vertical={false} />
            <XAxis dataKey="t" tick={{ fill: "#8a8a96", fontSize: 10 }} axisLine={false} tickLine={false} interval="preserveStartEnd" />
            <YAxis domain={[0, 100]} ticks={[0, 25, 50, 75, 100]} tickFormatter={(v) => `${v}%`} tick={{ fill: "#8a8a96", fontSize: 10 }} axisLine={false} tickLine={false} />
            <Tooltip
              contentStyle={{ background: "#17171d", border: "1px solid rgba(255,255,255,0.09)", borderRadius: 10, fontSize: 12 }}
              labelStyle={{ color: "#a1a1ab" }}
              formatter={(v) => `${v}%`}
            />
            {SERIES.map((s) => (
              <Area key={s.key} type="monotone" dataKey={s.key} name={s.name} stroke={s.color} strokeWidth={1.6} fill={`url(#fill-${s.key})`} isAnimationActive={false} dot={false} />
            ))}
          </AreaChart>
        </ResponsiveContainer>
      </div>
      <ul className="mt-2 flex justify-center gap-5 text-xs text-[var(--text-2)]">
        {SERIES.map((s) => (
          <li key={s.key} className="flex items-center gap-1.5">
            <span className="size-2 rounded-full" style={{ background: s.color }} aria-hidden />
            {s.name}
          </li>
        ))}
      </ul>
    </Panel>
  );
}

const clamp = (v: number, lo: number, hi: number) => Math.max(lo, Math.min(hi, Math.round(v)));
const rnd = (spread: number) => (Math.random() - 0.5) * 2 * spread;
