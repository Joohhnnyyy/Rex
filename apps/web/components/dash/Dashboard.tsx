"use client";

import {
  RoomAudioRenderer,
  StartAudio,
  TrackToggle,
  useLocalParticipant,
  useRoomContext,
  useTextStream,
  useTrackVolume,
  useTranscriptions,
  useVoiceAssistant,
} from "@livekit/components-react";
import { Track, type LocalAudioTrack } from "livekit-client";
import { AudioLines, Maximize2, Mic, MonitorUp, PhoneOff, Send } from "lucide-react";
import { useCallback, useEffect, useId, useMemo, useRef, useState } from "react";

import { BrowserView, useBrowserFrame } from "@/components/BrowserView";
import { Connections } from "@/components/Connections";
import { Discover } from "@/components/dash/Discover";
import { Files } from "@/components/dash/Files";
import { Immersive } from "@/components/dash/Immersive";
import { MascotStage } from "@/components/dash/Mascot";
import { ANIMATIONS, EXPRESSIONS_LIST, type MascotAnimation, type MascotExpression } from "@/lib/mascot";
import { RichText } from "@/components/dash/RichText";
import {
  ActiveAgents,
  ActivityList,
  GlobalActivity,
  Panel,
  Projects,
  RecentActivity,
  ResourceChart,
  StatusPill,
  SystemHealth,
  TaskProgress,
  openApprovals,
  type AgentRow,
} from "@/components/dash/Panels";
import { CommandPalette, Drawer, Rail, TABS, TopBar, type PaletteCommand } from "@/components/dash/Shell";
import {
  AGENTS,
  greeting,
  summarise,
  type ActionEvent,
  type MascotState,
  type Project,
  type View,
} from "@/lib/dashboard";
import { LANG_NAME, langChip } from "@/lib/lang";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const SUGGESTIONS = [
  "Send Shanky Naruto t-shirt shops",
  "My calendar tomorrow?",
  "Unread emails today?",
];
const MASCOT_STATES: MascotState[] = ["idle", "listening", "thinking", "speaking", "happy", "confused", "surprised", "error", "sleeping", "success"];
const STATE_LABEL: Record<string, string> = {
  disconnected: "Offline",
  connecting: "Connecting…",
  initializing: "Waking up…",
  listening: "Listening",
  thinking: "Thinking",
  speaking: "Speaking",
};

function useReducedMotion() {
  const [reduced, setReduced] = useState(false);
  useEffect(() => {
    const mq = matchMedia("(prefers-reduced-motion: reduce)");
    setReduced(mq.matches);
    const on = (e: MediaQueryListEvent) => setReduced(e.matches);
    mq.addEventListener("change", on);
    return () => mq.removeEventListener("change", on);
  }, []);
  return reduced;
}

function useNow(ms: number) {
  const [now, setNow] = useState(0);
  useEffect(() => {
    setNow(Date.now());
    const id = setInterval(() => setNow(Date.now()), ms);
    return () => clearInterval(id);
  }, [ms]);
  return now;
}

function useActions(): ActionEvent[] {
  const { textStreams } = useTextStream("rex.timeline");
  return useMemo(() => {
    const out: ActionEvent[] = [];
    for (const s of textStreams) {
      try {
        const e = JSON.parse(s.text) as ActionEvent;
        if (e.type === "action_event") out.push(e);
      } catch {
        /* partial or non-JSON stream */
      }
    }
    return out.reverse(); // newest first
  }, [textStreams]);
}

export function Dashboard({
  identity,
  setIdentity,
  connected,
  busy,
  error,
  onStart,
  onEnd,
}: {
  identity: string;
  setIdentity: (s: string) => void;
  connected: boolean;
  busy: boolean;
  error: string | null;
  onStart: () => void;
  onEnd: () => void;
}) {
  const room = useRoomContext();
  const { state: agentState, audioTrack, agent } = useVoiceAssistant();
  const level = useTrackVolume(audioTrack);
  const { microphoneTrack, isScreenShareEnabled } = useLocalParticipant();
  const micLevel = useTrackVolume(microphoneTrack?.track as LocalAudioTrack | undefined);
  // One subscription per text-stream topic (LiveKit throws on a second handler); children get the data as props.
  const transcriptions = useTranscriptions();
  const browserFrame = useBrowserFrame();
  const events = useActions();
  const reduced = useReducedMotion();
  const now = useNow(20_000);

  const [view, setView] = useState<View>("overview");
  const [palette, setPalette] = useState(false);
  const [drawer, setDrawer] = useState<{ kind: "assistant" } | { kind: "agent"; id: string } | { kind: "project"; p: Project } | { kind: "activity" } | null>(null);
  const [deciding, setDeciding] = useState<string | null>(null);
  const [labState, setLabState] = useState<MascotState | null>(null);
  const [labAnimation, setLabAnimation] = useState<MascotAnimation | undefined>();
  const [labExpression, setLabExpression] = useState<MascotExpression | undefined>();
  const [labCycle, setLabCycle] = useState(false);
  const [labReplay, setLabReplay] = useState(0);
  const [flash, setFlash] = useState<MascotState | null>(null);
  const [draft, setDraft] = useState("");
  const [immersive, setImmersive] = useState(false);

  // Calls open in the immersive view; ending the call returns to the dashboard.
  useEffect(() => {
    setImmersive(connected);
  }, [connected]);
  const pending = useRef<string | null>(null);

  const name = identity ? identity[0].toUpperCase() + identity.slice(1) : "there";

  // New finds from Rex's own research, for the Discover badge and the bell.
  const [finds, setFinds] = useState<{ id: string; title: string }[]>([]);
  const loadFinds = useCallback(() => {
    fetch(`${API_URL}/v1/discoveries`)
      .then((r) => (r.ok ? r.json() : Promise.reject()))
      .then((d: { items: { id: string; title: string; seen: boolean }[] }) => setFinds(d.items.filter((i) => !i.seen)))
      .catch(() => {});
  }, []);
  useEffect(() => {
    loadFinds();
    const id = setInterval(loadFinds, 300_000);
    return () => clearInterval(id);
  }, [loadFinds]);

  // How many services Rex can reach, for the status line under the greeting.
  const [services, setServices] = useState<{ ok: number; total: number } | null>(null);
  useEffect(() => {
    fetch(`${API_URL}/v1/connections`)
      .then((r) => (r.ok ? r.json() : Promise.reject()))
      .then((list: { status: string }[]) => setServices({ ok: list.filter((c) => c.status === "ok").length, total: list.length }))
      .catch(() => setServices(null));
  }, []);

  // ⌘K / Ctrl+K
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        if (immersive) document.querySelector<HTMLTextAreaElement>(".immersive-scene textarea")?.focus();
        else setPalette((p) => !p);
      }
    };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [immersive]);

  // A brief reaction when an action finishes, fails or needs approval.
  const latest = events[0];
  useEffect(() => {
    if (!latest) return;
    const s: MascotState | null =
      latest.status === "succeeded" ? "success" : latest.status === "failed" ? "error" : latest.status === "awaiting_approval" ? "surprised" : null;
    if (!s) return;
    setFlash(s);
    const t = setTimeout(() => setFlash(null), 1800);
    return () => clearTimeout(t);
  }, [latest]);

  // Rex's emotion tags (<laugh>, <sigh> …) also show on the mascot's face while it says them.
  const lastRex = [...transcriptions].reverse().find((t) => t.participantInfo.identity !== identity);
  const mood: MascotState | null = !lastRex
    ? null
    : /<(laugh|giggle|excited)>/i.test(lastRex.text)
      ? "happy"
      : /<(sigh|exhales)>/i.test(lastRex.text)
        ? "confused"
        : /<whispers>/i.test(lastRex.text)
          ? "thinking"
          : null;

  const voiceMascot: MascotState = !connected
    ? "idle"
    : agentState === "listening"
      ? "listening"
      : agentState === "thinking" || agentState === "connecting" || agentState === "initializing"
        ? "thinking"
        : agentState === "speaking"
          ? (mood ?? "speaking")
          : "idle";
  const mascot = labState ?? flash ?? voiceMascot;

  const sendText = useCallback(
    async (text: string) => {
      await room.localParticipant.sendText(text, { topic: "lk.chat" });
    },
    [room],
  );

  // A command typed before the call is up is sent once Rex has joined.
  useEffect(() => {
    if (connected && agent && pending.current) {
      const t = pending.current;
      pending.current = null;
      sendText(t).catch(() => (pending.current = t));
    }
  }, [connected, agent, sendText]);

  const ask = useCallback(
    (text: string) => {
      const t = text.trim();
      if (!t) return;
      setDrawer({ kind: "assistant" });
      if (connected && agent) sendText(t).catch(() => {});
      else {
        pending.current = t;
        if (!connected) onStart();
      }
    },
    [connected, agent, sendText, onStart],
  );

  async function decide(actionId: string, decision: "approve" | "deny") {
    if (!agent) return;
    setDeciding(actionId);
    try {
      await room.localParticipant.performRpc({
        destinationIdentity: agent.identity,
        method: "rex.decide",
        payload: JSON.stringify({ action_id: actionId, decision }),
      });
    } finally {
      setDeciding(null);
    }
  }

  const agentRows: AgentRow[] = AGENTS.map((a) => {
    const mine = a.id === "rex" ? events : events.filter((e) => a.servers.includes(e.tool.split(".")[0]));
    const spark = Array.from({ length: 12 }, (_, i) => {
      const lo = now - (12 - i) * 60_000;
      return mine.filter((e) => {
        const t = new Date(e.ts).getTime();
        return t >= lo && t < lo + 60_000;
      }).length;
    });
    const recent = mine[0];
    const status =
      a.id === "rex"
        ? connected && agent
          ? "running"
          : "idle"
        : recent?.status === "failed"
          ? "error"
          : recent && now - new Date(recent.ts).getTime() < 90_000
            ? "running"
            : "idle";
    const current = a.id === "rex" ? (connected ? STATE_LABEL[agentState] ?? agentState : "Not in a call") : recent?.summary ?? "Waiting for work";
    return { ...a, status, spark, current };
  });

  const approvals = openApprovals(events);
  const notifications = [
    ...events.filter((e) => approvals.has(e.id)).map((e) => ({ id: e.id, text: `Needs your OK: ${e.summary}`, when: "Approve in Recent Activity" })),
    ...events.filter((e) => e.status === "failed").slice(0, 5).map((e) => ({ id: e.id, text: `Failed: ${e.summary}`, when: new Date(e.ts).toLocaleTimeString() })),
    ...(error ? [{ id: "err", text: error, when: "Connection" }] : []),
    ...finds.slice(0, 3).map((f) => ({ id: `find-${f.id}`, text: `Rex found: ${f.title}`, when: "In Discover" })),
  ];

  const lastMine = [...transcriptions].reverse().find((t) => t.participantInfo.identity === identity);
  const heard = lastMine ? langChip(lastMine.text) : null;

  const commands: PaletteCommand[] = [
    ...TABS.map(([v, label]) => ({ id: `go-${v}`, label: `Go to ${label}`, run: () => setView(v) })),
    { id: "go-memory", label: "Go to Memory", run: () => setView("memory") },
    { id: "go-projects", label: "Go to Projects", run: () => setView("projects") },
    { id: "go-lab", label: "Go to Lab", run: () => setView("lab") },
    connected
      ? { id: "end", label: "End call with Rex", hint: "voice", run: onEnd }
      : { id: "start", label: "Talk to Rex", hint: "voice", run: onStart },
    { id: "assistant", label: "Open conversation", run: () => setDrawer({ kind: "assistant" }) },
    { id: "immersive", label: immersive ? "Leave immersive view" : "Enter immersive view", run: () => setImmersive((v) => !v) },
    ...(connected
      ? [{ id: "share", label: isScreenShareEnabled ? "Stop sharing screen" : "Share screen with Rex", run: () => room.localParticipant.setScreenShareEnabled(!isScreenShareEnabled, { audio: false }) }]
      : []),
  ];

  const stage = (
    <div className="workspace-assistant relative flex h-full flex-col items-center justify-center gap-3 px-4 py-4 sm:px-7">
      <MascotStage state={mascot} level={level} micLevel={micLevel} animate={!reduced && !immersive} className="max-w-[270px]" />
      <p className="flex max-w-full items-center justify-center gap-2 text-center text-xs text-[var(--text-2)] sm:text-sm" aria-live="polite">
        {connected && <span className="live-dot size-2 rounded-full bg-[var(--red)]" aria-hidden />}
        {connected ? (agent ? STATE_LABEL[agentState] ?? agentState : "Waiting for Rex to join…") : "Rex is offline: press the mic or type to start"}
        {heard && <span className="rounded-full bg-[var(--red-glow)] px-2 py-0.5 text-xs text-[var(--red-hi)]">{LANG_NAME[heard] ?? heard}</span>}
        <button
          onClick={() => setImmersive(true)}
          aria-label="Immersive view"
          title="Immersive view"
          className="lift grid size-7 shrink-0 place-items-center rounded-full border border-[var(--line)] text-[var(--text-2)] hover:text-[var(--text)]"
        >
          <Maximize2 className="size-3.5" />
        </button>
      </p>
      <CommandBar
        draft={draft}
        setDraft={setDraft}
        onSubmit={() => (ask(draft), setDraft(""))}
        connected={connected}
        busy={busy}
        onStart={onStart}
        onEnd={onEnd}
      />
      {!transcriptions.length && (
        <ul className="flex max-w-[520px] flex-wrap justify-center gap-2" aria-label="Try asking">
          {SUGGESTIONS.map((s) => (
            <li key={s}>
              <button
                onClick={() => ask(s)}
                className="lift rounded-full border border-[var(--line)] bg-white/[0.02] px-3 py-1.5 text-xs text-[var(--text-2)] hover:text-[var(--text)]"
              >
                {s}
              </button>
            </li>
          ))}
        </ul>
      )}
      {error && <p className="text-center text-sm text-[var(--danger)]">{error}</p>}
      <StartAudio label="Tap to enable Rex's audio" className="rounded-full bg-[var(--red)] px-4 py-2 text-sm text-white" />
    </div>
  );

  const greetingBlock = (
    <div className="workspace-heading px-1 pb-4 pt-1">
      <h1 className="text-[30px] font-semibold leading-tight tracking-tight">
        {greeting(new Date(now || Date.now()))}, <span className="text-[var(--red)]">{name}</span>
      </h1>
      <p className="mt-1 flex items-center gap-2 text-[15px] text-[var(--text-2)]" aria-live="polite">
        <span className={`size-2 rounded-full ${connected ? "live-dot bg-[var(--red)]" : "bg-[var(--ok)]"}`} aria-hidden />
        {connected
          ? `In a call with Rex · ${agent ? (STATE_LABEL[agentState] ?? agentState).toLowerCase() : "joining"}`
          : services
            ? `Rex is ready · ${services.ok} of ${services.total} services connected`
            : "Rex Control Center"}
      </p>
      <svg viewBox="0 0 300 24" className="mt-2 h-5 w-full max-w-[300px]" aria-hidden>
        <line x1="0" y1="12" x2="40" y2="12" stroke="var(--red)" strokeWidth="2" />
        <path d="M60 12 C90 2 110 22 140 12 S190 2 220 12 S270 20 300 10" fill="none" stroke="var(--red)" strokeOpacity="0.35" strokeDasharray="1 3" />
      </svg>
    </div>
  );

  return (
    <div className="dashboard-shell mx-auto flex min-h-screen max-w-[1600px] flex-col">
      <TopBar
        view={view}
        onView={setView}
        onSearch={() => setPalette(true)}
        badges={{ discover: finds.length }}
        notifications={notifications}
        name={name}
        menu={
          <>
            <p className="px-3 py-2 text-sm">
              {name}
              <span className="block text-xs text-[var(--text-2)]">{connected ? "In a call with Rex" : "Not in a call"}</span>
            </p>
            <MenuItem onClick={() => setView("settings")}>Settings</MenuItem>
            <MenuItem onClick={() => setView("memory")}>What Rex remembers</MenuItem>
            {connected ? <MenuItem onClick={onEnd}>End call</MenuItem> : <MenuItem onClick={onStart}>Talk to Rex</MenuItem>}
          </>
        }
      />

      <div className="flex flex-1 flex-col gap-5 px-3 pb-5 md:flex-row lg:px-5">
        <Rail view={view} onView={setView} />
        <main className="min-w-0 flex-1" data-view={view}>
          {view === "overview" && (
            <div className="workspace-overview">
              {greetingBlock}
              <div className="workspace-grid grid grid-cols-1 items-start gap-4 lg:grid-cols-[minmax(260px,0.82fr)_minmax(0,1.8fr)]">
                <div className="workspace-stack workspace-support flex min-w-0 flex-col gap-4">
                  <ActiveAgents rows={agentRows} onSelect={(id) => setDrawer({ kind: "agent", id })} />
                  <TaskProgress live={connected ? summarise(events) : null} />
                  <RecentActivity events={events} onDecide={decide} deciding={deciding} onViewAll={() => setDrawer({ kind: "activity" })} />
                </div>
                <div className="workspace-stack workspace-primary flex min-w-0 flex-col gap-4">
                  <section className="workspace-stage relative overflow-hidden rounded-[24px] border border-[var(--line)]" aria-label="Rex workspace">
                    <div className="relative z-10 flex items-center justify-between border-b border-[var(--line)] px-5 py-3 text-xs text-[var(--text-2)]">
                      <span className="flex items-center gap-2"><span className={`size-1.5 rounded-full ${connected ? "live-dot bg-[var(--ok)]" : "bg-[var(--faint)]"}`} />Rex workspace</span>
                      <button onClick={() => setDrawer({ kind: "assistant" })} className="rounded-lg px-2 py-1 hover:bg-white/5 hover:text-white">Open conversation ↗</button>
                    </div>
                    {stage}
                  </section>
                  <div className="workspace-metrics grid min-w-0 grid-cols-1 gap-4 xl:grid-cols-2">
                    <SystemHealth />
                    <GlobalActivity animate={!reduced && !immersive} />
                  </div>
                </div>
              </div>
              <div className="workspace-footer mt-4 grid grid-cols-1 gap-4 xl:grid-cols-2">
                <Projects onSelect={(p) => setDrawer({ kind: "project", p })} onViewAll={() => setView("projects")} />
                <ResourceChart />
              </div>
            </div>
          )}

          {view === "agents" && (
            <div className="grid gap-5 xl:grid-cols-2">
              <ActiveAgents rows={agentRows} onSelect={(id) => setDrawer({ kind: "agent", id })} />
              <Connections />
            </div>
          )}

          {view === "projects" && <Projects onSelect={(p) => setDrawer({ kind: "project", p })} />}

          {view === "analysis" && (
            <div className="grid gap-5 xl:grid-cols-2">
              <SystemHealth />
              <TaskProgress live={connected ? summarise(events) : null} />
              <div className="xl:col-span-2">
                <ResourceChart tall />
              </div>
            </div>
          )}

          {view === "lab" && (
            <div className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_minmax(0,1fr)]">
              <Panel title="Mascot studio" right={<button onClick={() => { setLabState(null); setLabAnimation(undefined); setLabExpression(undefined); setLabCycle(false); }} className="text-xs text-[var(--text-2)]">Follow Rex</button>}>
                <MascotStage key={labReplay} state={mascot} level={level} micLevel={micLevel} animate={!reduced && !immersive} animation={labAnimation} expression={labExpression} cycle={labCycle} />
                <div className="mb-5 flex flex-wrap gap-2">
                  <button onClick={() => { setLabCycle((v) => !v); setLabReplay((v) => v + 1); }} disabled={reduced} aria-pressed={labCycle} className="rounded-lg bg-[var(--red)] px-3 py-2 text-xs disabled:opacity-40">{labCycle ? "Stop sequence" : "Play all animations"}</button>
                  <button onClick={() => setLabReplay((v) => v + 1)} disabled={reduced} className="rounded-lg border border-[var(--line)] px-3 py-2 text-xs disabled:opacity-40">Replay</button>
                </div>
                {reduced && <p className="mb-4 text-xs text-[var(--text-2)]">Reduced motion is on. Previews show a still frame.</p>}
                <h3 className="mb-2 text-sm font-medium">Live reactions</h3>
                <div className="mb-5 flex flex-wrap gap-2" role="group" aria-label="Preview a mascot state">
                  {MASCOT_STATES.map((s) => (
                    <button key={s} onClick={() => { setLabState(s); setLabAnimation(undefined); setLabExpression(undefined); setLabCycle(false); }} aria-pressed={!labAnimation && !labExpression && mascot === s} className="rounded-lg border border-[var(--line)] px-2.5 py-1.5 text-xs capitalize aria-pressed:border-[var(--red)] aria-pressed:bg-[var(--red-glow)]">{s}</button>
                  ))}
                </div>
                <h3 className="mb-2 text-sm font-medium">Animations <span className="text-[var(--text-2)]">15</span></h3>
                <div className="mb-5 flex flex-wrap gap-2" role="group" aria-label="Preview an animation">
                  {ANIMATIONS.map((id) => <button key={id} onClick={() => { setLabAnimation(id); setLabCycle(false); }} aria-pressed={!labCycle && labAnimation === id} className="rounded-lg border border-[var(--line)] px-2.5 py-1.5 text-xs capitalize aria-pressed:border-[var(--red)] aria-pressed:bg-[var(--red-glow)]">{id}</button>)}
                </div>
                <h3 className="mb-2 text-sm font-medium">Expressions <span className="text-[var(--text-2)]">16</span></h3>
                <div className="flex flex-wrap gap-2" role="group" aria-label="Preview an expression">
                  {EXPRESSIONS_LIST.map(([id, label]) => <button key={id} onClick={() => { setLabExpression(id); setLabAnimation("idle"); setLabCycle(false); }} aria-pressed={labExpression === id} className="rounded-lg border border-[var(--line)] px-2.5 py-1.5 text-xs aria-pressed:border-[var(--red)] aria-pressed:bg-[var(--red-glow)]">{label}</button>)}
                </div>
              </Panel>
              <div className="flex flex-col gap-5">
                <BrowserView frame={browserFrame} />
                <Panel title="Conversation">
                  <Transcript identity={identity} transcriptions={transcriptions} />
                </Panel>
              </div>
            </div>
          )}

          {view === "memory" && <MemoryView />}

          {view === "discover" && <Discover onSeen={loadFinds} />}

          {view === "files" && <Files />}

          {view === "settings" && (
            <div className="grid gap-5 xl:grid-cols-2">
              <Panel title="Profile">
                <label className="flex flex-col gap-2 text-sm">
                  Your name (used for your call identity)
                  <input
                    value={identity}
                    disabled={connected}
                    onChange={(e) => setIdentity(e.target.value.replace(/[^A-Za-z0-9_-]/g, ""))}
                    className="rounded-[10px] border border-[var(--line)] bg-transparent px-3 py-2 disabled:opacity-50"
                  />
                </label>
                {connected && <p className="mt-2 text-xs text-[var(--text-2)]">End the call to change it.</p>}
              </Panel>
              <Connections />
            </div>
          )}
        </main>
      </div>

      {palette && <CommandPalette commands={commands} onClose={() => setPalette(false)} onAsk={ask} />}

      {drawer?.kind === "assistant" && (
        <Drawer title="Conversation with Rex" onClose={() => setDrawer(null)} wide>
          <div className="flex flex-col gap-5">
            <BrowserView frame={browserFrame} />
            <Transcript identity={identity} transcriptions={transcriptions} />
            {events.length > 0 && (
              <section>
                <h3 className="mb-2 text-sm font-medium text-[var(--text-2)]">Actions</h3>
                <ActivityList events={events} onDecide={decide} deciding={deciding} />
              </section>
            )}
          </div>
        </Drawer>
      )}
      {drawer?.kind === "activity" && (
        <Drawer title="Recent Activity" onClose={() => setDrawer(null)}>
          {events.length ? <ActivityList events={events} onDecide={decide} deciding={deciding} /> : <p className="text-sm text-[var(--text-2)]">Rex&apos;s actions appear here during a call.</p>}
        </Drawer>
      )}
      {drawer?.kind === "agent" && (() => {
        const a = agentRows.find((r) => r.id === drawer.id)!;
        const mine = a.id === "rex" ? events : events.filter((e) => a.servers.includes(e.tool.split(".")[0]));
        return (
          <Drawer title={a.name} onClose={() => setDrawer(null)}>
            <dl className="grid grid-cols-[auto_1fr] gap-x-4 gap-y-3 text-sm">
              <dt className="text-[var(--text-2)]">Role</dt>
              <dd>{a.role}</dd>
              <dt className="text-[var(--text-2)]">Status</dt>
              <dd className="justify-self-start">
                <StatusPill status={a.status} />
              </dd>
              <dt className="text-[var(--text-2)]">Current</dt>
              <dd>{a.current}</dd>
            </dl>
            <h3 className="mb-2 mt-6 text-sm font-medium text-[var(--text-2)]">Recent actions</h3>
            {mine.length ? <ActivityList events={mine} onDecide={decide} deciding={deciding} /> : <p className="text-sm text-[var(--text-2)]">No actions this call.</p>}
            {a.id === "rex" && (
              <div className="mt-6">
                {connected ? <ActionButton onClick={onEnd}>End call</ActionButton> : <ActionButton onClick={onStart}>Talk to Rex</ActionButton>}
              </div>
            )}
          </Drawer>
        );
      })()}
      {drawer?.kind === "project" && (
        <Drawer title={drawer.p.name} onClose={() => setDrawer(null)}>
          <p className="text-sm text-[var(--text-2)]">{drawer.p.description}</p>
          <p className="mt-4 text-sm">
            Progress <span className="tabular font-semibold">{drawer.p.progress}%</span> · <span className="capitalize">{drawer.p.status}</span>
          </p>
          <p className="mt-6 rounded-lg border border-[var(--line)] p-3 text-xs text-[var(--text-2)]">
            Demo project data. Connect a project source (GitHub, Notion) to show real progress here.
          </p>
        </Drawer>
      )}

      {immersive && (
        <Immersive
          identity={identity}
          transcriptions={transcriptions}
          mascot={mascot}
          level={level}
          micLevel={micLevel}
          status={connected ? (agent ? (STATE_LABEL[agentState] ?? agentState) : "Waiting for Rex…") : "Offline"}
          language={heard ? (LANG_NAME[heard] ?? heard) : null}
          connected={connected}
          events={events}
          deciding={deciding}
          onDecide={decide}
          onExit={() => setImmersive(false)}
          onEnd={onEnd}
          animate={!reduced}
          bar={
            <CommandBar
              draft={draft}
              setDraft={setDraft}
              onSubmit={() => (ask(draft), setDraft(""))}
              connected={connected}
              busy={busy}
              onStart={onStart}
              onEnd={onEnd}
              compact
            />
          }
        />
      )}

      <RoomAudioRenderer />
    </div>
  );
}

function CommandBar({
  draft,
  setDraft,
  onSubmit,
  connected,
  busy,
  onStart,
  onEnd,
  compact = false,
}: {
  draft: string;
  setDraft: (s: string) => void;
  onSubmit: () => void;
  connected: boolean;
  busy: boolean;
  onStart: () => void;
  onEnd: () => void;
  compact?: boolean;
}) {
  const inputId = useId();
  return (
    <div className="w-full max-w-[520px]">
      <form
        onSubmit={(e) => (e.preventDefault(), onSubmit())}
        className="flex items-center gap-2 rounded-[16px] border border-[var(--line-active)] bg-[var(--panel)]/90 p-1.5 pl-2 shadow-[0_0_24px_rgba(255,64,85,0.12)]"
      >
        {connected ? (
          <TrackToggle source={Track.Source.Microphone} showIcon={false} className="grid size-10 shrink-0 place-items-center rounded-[12px] text-[var(--red-hi)] hover:bg-white/5" aria-label="Mute or unmute your microphone">
            <AudioLines className="size-5" />
          </TrackToggle>
        ) : (
          <button type="button" onClick={onStart} disabled={busy} aria-label="Start talking to Rex" className="grid size-10 shrink-0 place-items-center rounded-[12px] text-[var(--red-hi)] hover:bg-white/5 disabled:opacity-50">
            {busy ? <AudioLines className="live-dot size-5" /> : <Mic className="size-5" />}
          </button>
        )}
        <label className="sr-only" htmlFor={inputId}>
          Ask Rex
        </label>
        <textarea
          id={inputId}
          rows={1}
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              onSubmit();
            }
          }}
          placeholder="Ask Rex anything…"
          className="max-h-28 min-w-0 flex-1 resize-none bg-transparent py-2 text-sm outline-none placeholder:text-[var(--faint)]"
        />
        <button type="submit" disabled={!draft.trim()} aria-label="Send" className="grid size-10 shrink-0 place-items-center rounded-[12px] bg-[var(--red)] text-white transition-opacity disabled:opacity-40">
          <Send className="size-4" />
        </button>
      </form>
      {connected && !compact && (
        <div className="mt-2 flex justify-center gap-2">
          <TrackToggle source={Track.Source.ScreenShare} captureOptions={{ audio: false }} showIcon={false} className="flex items-center gap-1.5 rounded-[10px] border border-[var(--line)] px-3 py-1.5 text-xs text-[var(--text-2)] hover:text-[var(--text)] data-[lk-enabled=true]:border-[var(--line-active)] data-[lk-enabled=true]:text-[var(--red-hi)]">
            <MonitorUp className="size-3.5" /> Share screen
          </TrackToggle>
          <button onClick={onEnd} className="flex items-center gap-1.5 rounded-[10px] border border-[var(--line)] px-3 py-1.5 text-xs text-[var(--danger)] hover:border-[var(--danger)]">
            <PhoneOff className="size-3.5" /> End call
          </button>
        </div>
      )}
    </div>
  );
}

function Transcript({
  identity,
  transcriptions,
}: {
  identity: string;
  transcriptions: ReturnType<typeof useTranscriptions>;
}) {
  const end = useRef<HTMLDivElement>(null);
  useEffect(() => {
    // Braces matter: newer browsers return a Promise from scrollIntoView, and an effect may only return a cleanup.
    end.current?.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }, [transcriptions.length]);
  if (!transcriptions.length) return <p className="text-sm text-[var(--text-2)]">Say “Namaste Rex” or type a request.</p>;
  return (
    <ol className="flex max-h-[50vh] flex-col gap-3 overflow-y-auto" aria-live="polite">
      {transcriptions.map((t) => {
        const mine = t.participantInfo.identity === identity;
        return (
          <li key={t.streamInfo.id} className={`flex flex-col ${mine ? "items-end" : "items-start"}`}>
            <span className="mb-1 text-[11px] text-[var(--text-2)]">
              {mine ? "You" : "Rex"} · {LANG_NAME[langChip(t.text)] ?? langChip(t.text)}
            </span>
            <div className={`max-w-[85%] rounded-[14px] px-3.5 py-2 text-sm leading-relaxed ${mine ? "bg-[var(--red)] text-white" : "bg-white/[0.05]"}`}>
              {mine ? t.text : <RichText text={t.text} />}
            </div>
          </li>
        );
      })}
      <div ref={end} />
    </ol>
  );
}

type MemoryData = { facts: Record<string, { value: string; updated: string }>; episodes: { date: string; summary: string }[] };

function MemoryView() {
  const [data, setData] = useState<MemoryData | null>(null);
  const [failed, setFailed] = useState(false);
  const load = useCallback(async () => {
    setFailed(false);
    try {
      const res = await fetch(`${API_URL}/v1/memory`);
      if (!res.ok) throw new Error();
      setData(await res.json());
    } catch {
      setFailed(true);
    }
  }, []);
  useEffect(() => {
    load();
  }, [load]);
  const refresh = <button onClick={load} className="text-xs text-[var(--text-2)] hover:text-[var(--text)]">Refresh</button>;
  if (failed) return <p className="text-sm text-[var(--danger)]">Can&apos;t reach the Rex API at {API_URL}.</p>;
  if (!data) return <p className="text-sm text-[var(--text-2)]">Loading…</p>;
  const facts = Object.entries(data.facts);
  return (
    <div className="grid gap-5 xl:grid-cols-2">
      <Panel title="What Rex knows about you" right={refresh}>
        {facts.length === 0 ? (
          <p className="text-sm text-[var(--text-2)]">Nothing yet. Tell Rex something like “my manager is Shanky”.</p>
        ) : (
          <dl className="divide-y divide-[var(--line)] text-sm">
            {facts.map(([k, f]) => (
              <div key={k} className="grid grid-cols-[minmax(0,10rem)_1fr] gap-3 py-2.5">
                <dt className="capitalize text-[var(--text-2)]">{k.replace(/_/g, " ")}</dt>
                <dd>{f.value}</dd>
              </div>
            ))}
          </dl>
        )}
      </Panel>
      <Panel title="Past calls">
        {data.episodes.length === 0 ? (
          <p className="text-sm text-[var(--text-2)]">A short summary of each call appears here after it ends.</p>
        ) : (
          <ol className="flex flex-col gap-3 text-sm">
            {data.episodes.map((e, i) => (
              <li key={i} className="border-l-2 border-[var(--red)]/50 pl-3">
                <span className="tabular block text-[11px] text-[var(--text-2)]">{e.date}</span>
                {e.summary}
              </li>
            ))}
          </ol>
        )}
      </Panel>
    </div>
  );
}

const MenuItem = ({ onClick, children }: { onClick: () => void; children: React.ReactNode }) => (
  <button role="menuitem" onClick={onClick} className="block w-full rounded-lg px-3 py-2 text-left text-sm text-[var(--text-2)] hover:bg-white/5 hover:text-[var(--text)]">
    {children}
  </button>
);

const ActionButton = ({ onClick, children }: { onClick: () => void; children: React.ReactNode }) => (
  <button onClick={onClick} className="rounded-[10px] bg-[var(--red)] px-4 py-2 text-sm font-medium text-white">
    {children}
  </button>
);
