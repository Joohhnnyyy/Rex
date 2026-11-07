// Typed data for the control-center dashboard. Live data (voice state, actions, connections, memory)
// comes from LiveKit and the Rex API; everything in DEMO below is illustrative and shown with a "Demo" tag.

export type MascotState =
  | "idle"
  | "listening"
  | "thinking"
  | "speaking"
  | "happy"
  | "confused"
  | "surprised"
  | "error"
  | "sleeping"
  | "success";

export type View = "overview" | "discover" | "agents" | "projects" | "analysis" | "lab" | "memory" | "settings";

export type Tier = "R" | "W" | "A";
export type ActionStatus = "started" | "succeeded" | "failed" | "awaiting_approval" | "denied" | "undone";

// Mirrors rex_shared.schemas.ActionEvent (sent by the agent on the "rex.timeline" text stream).
export type ActionEvent = {
  type: "action_event";
  id: string;
  ts: string;
  tool: string;
  tier: Tier;
  status: ActionStatus;
  summary: string;
  trace_id?: string | null; // action_id for approvals
  result_redacted?: { text?: string; error?: string } | null;
};

export type SystemMetrics = {
  health: number; // 0-100
  cpu: number; // %
  memoryUsedGb: number;
  memoryTotalGb: number;
  gpu: number; // %
  networkMbps: number;
};

export type TaskSummary = { completed: number; inProgress: number; queued: number };
export type TaskPeriod = "session" | "today" | "week";

export type AgentStatus = "running" | "idle" | "paused" | "error";
export type AgentInfo = { id: string; name: string; role: string; servers: string[] };

export type Project = {
  id: string;
  name: string;
  description: string;
  progress: number;
  status: "active" | "review" | "paused";
  icon: "sprout" | "zap" | "droplet" | "circle" | "layers" | "box";
};

export type ResourceSample = { t: string; cpu: number; memory: number; gpu: number };
export type ResourceRange = "30m" | "1h" | "24h";

export type DemoActivity = { id: string; kind: "validation" | "review" | "code" | "deploy" | "workflow"; text: string; minutesAgo: number };

// Rex's real agents: the voice operator and the background specialists it can delegate to.
export const AGENTS: AgentInfo[] = [
  { id: "rex", name: "Rex", role: "Voice & Orchestration", servers: [] },
  { id: "desktop", name: "Desktop", role: "Mac apps like WhatsApp", servers: ["desktop", "screen"] },
  { id: "web", name: "Research", role: "Web search & reading", servers: ["firecrawl", "browser"] },
  { id: "comms", name: "Comms", role: "Gmail, Slack & Calendar", servers: ["gmail", "slack", "calendar", "notion"] },
];

// Deterministic pseudo-random numbers so server and client render the same demo values (no hydration drift).
function seeded(seed: number) {
  let s = seed;
  return () => {
    s = (s * 16807) % 2147483647;
    return (s - 1) / 2147483646;
  };
}

function resourceSeries(range: ResourceRange): ResourceSample[] {
  const n = range === "24h" ? 24 : 7;
  const rand = seeded(range === "30m" ? 7 : range === "1h" ? 11 : 13);
  const step = range === "30m" ? 5 : range === "1h" ? 10 : 60;
  const end = new Date(2026, 10, 7, 13, 40);
  return Array.from({ length: n }, (_, i) => {
    const t = new Date(end.getTime() - (n - 1 - i) * step * 60_000);
    const wave = Math.sin(i / 1.6);
    return {
      t: range === "24h" ? `${String(t.getHours()).padStart(2, "0")}:00` : t.toTimeString().slice(0, 5),
      cpu: Math.round(38 + wave * 14 + rand() * 10),
      memory: Math.round(52 + Math.cos(i / 2.1) * 9 + rand() * 6),
      gpu: Math.round(30 + Math.sin(i / 1.2 + 1) * 12 + rand() * 8),
    };
  });
}

export const DEMO = {
  metrics: { health: 97, cpu: 28, memoryUsedGb: 6.4, memoryTotalGb: 32, gpu: 42, networkMbps: 182 } as SystemMetrics,
  tasks: {
    session: { completed: 32, inProgress: 10, queued: 4 },
    today: { completed: 118, inProgress: 12, queued: 9 },
    week: { completed: 604, inProgress: 21, queued: 17 },
  } as Record<TaskPeriod, TaskSummary>,
  globe: { tasks: "14.2K", tasksDelta: 12, data: "3.8 TB", dataDelta: 6, workflows: 42, workflowsDelta: 18 },
  projects: [
    { id: "seedsync", name: "SeedSync", description: "Agri ML Platform", progress: 92, status: "active", icon: "sprout" },
    { id: "navswap", name: "NavSwap", description: "EV Battery Network", progress: 76, status: "active", icon: "zap" },
    { id: "aquavigil", name: "AquaVigil", description: "Flood Management", progress: 68, status: "review", icon: "droplet" },
    { id: "oru", name: "Oru", description: "Product Suite", progress: 54, status: "active", icon: "circle" },
    { id: "gnani", name: "Gnani", description: "Multi-Agent System", progress: 88, status: "active", icon: "layers" },
    { id: "woblo", name: "Woblo Clone", description: "Chrome Extension", progress: 73, status: "paused", icon: "box" },
  ] as Project[],
  activity: [
    { id: "a1", kind: "validation", text: "Validation passed", minutesAgo: 2 },
    { id: "a2", kind: "review", text: "Code review completed", minutesAgo: 5 },
    { id: "a3", kind: "code", text: "Code generated", minutesAgo: 8 },
    { id: "a4", kind: "deploy", text: "Deployed to staging", minutesAgo: 12 },
    { id: "a5", kind: "workflow", text: "Morning workflow finished", minutesAgo: 26 },
  ] as DemoActivity[],
  resources: { "30m": resourceSeries("30m"), "1h": resourceSeries("1h"), "24h": resourceSeries("24h") } as Record<
    ResourceRange,
    ResourceSample[]
  >,
};

export const completion = (t: TaskSummary) => {
  const total = t.completed + t.inProgress + t.queued;
  return total ? Math.round((t.completed / total) * 100) : 0;
};

// Live task counts for this call, from the action timeline.
export function summarise(events: ActionEvent[]): TaskSummary {
  const latest = new Map<string, ActionEvent>();
  for (const e of events) latest.set(e.trace_id || e.id, e);
  let completed = 0;
  let inProgress = 0;
  let queued = 0;
  for (const e of latest.values()) {
    if (e.status === "succeeded") completed++;
    else if (e.status === "started") inProgress++;
    else if (e.status === "awaiting_approval") queued++;
  }
  return { completed, inProgress, queued };
}

export const greeting = (d: Date) => (d.getHours() < 12 ? "Good Morning" : d.getHours() < 17 ? "Good Afternoon" : "Good Evening");
