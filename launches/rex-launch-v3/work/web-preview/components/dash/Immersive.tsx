"use client";

import { TrackToggle, type useTranscriptions } from "@livekit/components-react";
import { Track } from "livekit-client";
import { Clock, Minimize2, MonitorUp, PhoneOff, Sparkles } from "lucide-react";
import { useEffect, useRef, useState, type CSSProperties, type ReactNode } from "react";
import { createPortal } from "react-dom";
import Image from "next/image";

import { MascotStage } from "@/components/dash/Mascot";
import { openApprovals } from "@/components/dash/Panels";
import { RichText } from "@/components/dash/RichText";
import type { ActionEvent, MascotState } from "@/lib/dashboard";

// A slow particle field around the mascot; Rex's voice level speeds it up and brightens it.
function ParticleField({ level, animate }: { level: number; animate: boolean }) {
  const canvas = useRef<HTMLCanvasElement>(null);
  const levelRef = useRef(level);
  levelRef.current = level;

  useEffect(() => {
    const el = canvas.current;
    const ctx = el?.getContext("2d");
    if (!el || !ctx) return;
    const parts = Array.from({ length: 150 }, () => ({
      a: Math.random() * Math.PI * 2,
      r: 0.12 + Math.random() * 0.9, // fraction of the half-diagonal
      s: 0.0006 + Math.random() * 0.0016, // radians per frame
      z: 0.3 + Math.random() * 0.7, // depth: size and brightness
    }));
    let raf = 0;
    let w = 0;
    let h = 0;
    const resize = () => {
      const dpr = Math.min(devicePixelRatio || 1, 2);
      w = el.clientWidth;
      h = el.clientHeight;
      el.width = w * dpr;
      el.height = h * dpr;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    };
    const draw = () => {
      const boost = 1 + Math.min(levelRef.current, 1) * 5;
      const cx = w / 2;
      const cy = h * 0.44;
      const R = Math.hypot(w, h) / 2;
      ctx.clearRect(0, 0, w, h);
      for (const p of parts) {
        if (animate) {
          p.a += p.s * boost;
          p.r += 0.00035 * boost * p.z;
          if (p.r > 1) p.r = 0.12;
        }
        const x = cx + Math.cos(p.a) * p.r * R;
        const y = cy + Math.sin(p.a) * p.r * R * 0.62;
        const alpha = (0.15 + p.z * 0.45) * (1 - p.r * 0.6) * (0.7 + Math.min(levelRef.current, 1) * 0.6);
        ctx.fillStyle = `rgba(255, ${80 + Math.round(p.z * 60)}, ${90 + Math.round(p.z * 40)}, ${alpha.toFixed(3)})`;
        ctx.beginPath();
        ctx.arc(x, y, 0.6 + p.z * 1.6, 0, Math.PI * 2);
        ctx.fill();
      }
      if (animate) raf = requestAnimationFrame(draw);
    };
    resize();
    draw();
    const onResize = () => { resize(); if (!animate) draw(); };
    addEventListener("resize", onResize);
    return () => {
      cancelAnimationFrame(raf);
      removeEventListener("resize", onResize);
    };
  }, [animate]);

  return <canvas ref={canvas} className="absolute inset-0 size-full" aria-hidden />;
}

export function Immersive({
  identity,
  mascot,
  level,
  micLevel,
  status,
  language,
  connected,
  events,
  deciding,
  onDecide,
  onExit,
  onEnd,
  bar,
  animate,
  transcriptions,
}: {
  transcriptions: ReturnType<typeof useTranscriptions>;
  identity: string;
  mascot: MascotState;
  level: number;
  micLevel: number;
  status: string;
  language: string | null;
  connected: boolean;
  events: ActionEvent[];
  deciding: string | null;
  onDecide: (actionId: string, d: "approve" | "deny") => void;
  onExit: () => void;
  onEnd: () => void;
  bar: ReactNode;
  animate: boolean;
}) {
  const scene = useRef<HTMLDivElement>(null);
  const exit = useRef(onExit);
  exit.current = onExit;
  useEffect(() => {
    const previousFocus = document.activeElement as HTMLElement | null;
    const overflow = document.body.style.overflow;
    const dashboard = document.querySelector<HTMLElement>(".dashboard-shell");
    const wasInert = dashboard?.inert ?? false;
    document.body.style.overflow = "hidden";
    if (dashboard) dashboard.inert = true;
    const controls = () => Array.from(scene.current?.querySelectorAll<HTMLElement>('button:not(:disabled), textarea, input, a[href], [tabindex="0"]') ?? []).filter((el) => el.getClientRects().length > 0);
    controls()[0]?.focus();
    const keydown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        event.preventDefault();
        exit.current();
      }
      if (event.key !== "Tab") return;
      const items = controls();
      const first = items[0], last = items[items.length - 1];
      if (event.shiftKey && (document.activeElement === first || !scene.current?.contains(document.activeElement))) {
        event.preventDefault(); last?.focus();
      } else if (!event.shiftKey && (document.activeElement === last || !scene.current?.contains(document.activeElement))) {
        event.preventDefault(); first?.focus();
      }
    };
    document.addEventListener("keydown", keydown);
    return () => {
      document.removeEventListener("keydown", keydown);
      document.body.style.overflow = overflow;
      if (dashboard) dashboard.inert = wasInert;
      previousFocus?.focus();
    };
  }, []);
  const [now, setNow] = useState(() => Date.now());
  useEffect(() => {
    const id = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(id);
  }, []);

  // Depth: the mouse tilts the mascot one way and drifts the particles the other (CSS vars, no re-render).
  useEffect(() => {
    const el = scene.current;
    if (!el) return;
    if (!animate) {
      el.style.setProperty("--mx", "0");
      el.style.setProperty("--my", "0");
      return;
    }
    const move = (e: PointerEvent) => {
      if (e.pointerType === "touch") return;
      el.style.setProperty("--mx", ((e.clientX / innerWidth) * 2 - 1).toFixed(3));
      el.style.setProperty("--my", ((e.clientY / innerHeight) * 2 - 1).toFixed(3));
    };
    addEventListener("pointermove", move);
    return () => removeEventListener("pointermove", move);
  }, [animate]);

  const lastRex = [...transcriptions].reverse().find((t) => t.participantInfo.identity !== identity);
  const lastMe = [...transcriptions].reverse().find((t) => t.participantInfo.identity === identity);
  const energy = connected && animate ? Math.max(0, Math.min(1, mascot === "listening" ? micLevel : level)) : 0;
  const presence = !connected ? "Your space to think out loud" : mascot === "listening" ? "Listening to you" : mascot === "thinking" ? "Working on it" : mascot === "speaking" ? "Rex is speaking" : status;
  const open = openApprovals(events);
  const toasts = events.filter((e) => open.has(e.id) || now - new Date(e.ts).getTime() < 9000).slice(0, 3);

  return createPortal(
    <div
      ref={scene}
      className="immersive-scene fixed inset-0 z-50 bg-[radial-gradient(ellipse_at_50%_40%,#2a0d14_0%,#0d0a0d_55%,#060607_100%)] [--mx:0] [--my:0]"
      data-mode={connected ? mascot : "offline"}
      data-motion={animate}
      style={{ "--voice-energy": energy } as CSSProperties}
      role="dialog"
      aria-modal="true"
      aria-label="Immersive call with Rex"
    >
      <div className="absolute inset-0 transition-transform duration-300 ease-out [transform:translate(calc(var(--mx)*-14px),calc(var(--my)*-10px))]">
        <ParticleField level={energy} animate={animate} />
      </div>
      <div className="immersive-horizon pointer-events-none absolute inset-0" aria-hidden />

      {/* top: status and controls */}
      <header className="immersive-header relative z-10 flex items-center justify-between gap-3 px-4 py-4 sm:px-8">
        <span className="flex min-w-0 flex-wrap items-center gap-2 sm:gap-3">
          <Image src="/rex-logo.svg" alt="Rex logo" width={40} height={40} className="shrink-0" />
          <span className="flex flex-col gap-0.5">
            <span className="text-lg font-semibold tracking-[0.4em]">REX</span>
            <span className="text-[10px] tracking-wide text-[var(--text-2)]">Focus mode</span>
          </span>
          <span className="flex items-center gap-2 rounded-full border border-[var(--line)] bg-black/30 px-3 py-1 text-xs text-[var(--text-2)] backdrop-blur" aria-live="polite">
            <span className={`size-1.5 rounded-full ${connected ? "live-dot bg-[var(--red)]" : "bg-[var(--faint)]"}`} aria-hidden />
            {status}
            {language && <span className="text-[var(--red-hi)]">· {language}</span>}
          </span>
        </span>
        <span className="flex shrink-0 items-center gap-2">
          {connected && (
            <TrackToggle
              source={Track.Source.ScreenShare}
              captureOptions={{ audio: false }}
              showIcon={false}
              className="grid size-10 place-items-center rounded-full border border-[var(--line)] bg-black/30 text-[var(--text-2)] backdrop-blur hover:text-[var(--text)] data-[lk-enabled=true]:border-[var(--line-active)] data-[lk-enabled=true]:text-[var(--red-hi)]"
              aria-label="Share screen with Rex"
            >
              <MonitorUp className="size-4" />
            </TrackToggle>
          )}
          <button onClick={onExit} aria-label="Leave immersive view (Esc)" title="Leave immersive view (Esc)" className="flex h-10 items-center gap-2 rounded-full border border-[var(--line)] bg-white/[0.03] px-3 text-[var(--text-2)] backdrop-blur hover:border-[var(--line-active)] hover:text-[var(--text)]">
            <Minimize2 className="size-4" />
            <span className="hidden text-xs sm:inline">Back to workspace</span>
            <kbd className="hidden rounded border border-white/10 px-1 text-[10px] lg:inline">Esc</kbd>
          </button>
          {connected && (
            <button onClick={onEnd} aria-label="End call" className="grid size-10 place-items-center rounded-full bg-[var(--red)] text-white hover:bg-[var(--red-hi)]">
              <PhoneOff className="size-4" />
            </button>
          )}
        </span>
      </header>

      {/* the mascot, tilting with the mouse */}
      <div className="immersive-mascot relative flex min-h-0 items-center justify-center">
        <div className="immersive-atmosphere pointer-events-none absolute" aria-hidden>
          <div className="immersive-aura" />
          <div className="immersive-orbit immersive-orbit-one" />
          <div className="immersive-orbit immersive-orbit-two" />
          <div className="immersive-ground" />
        </div>
        <div className="immersive-avatar transition-transform duration-300 ease-out [transform:perspective(900px)_rotateY(calc(var(--mx)*4deg))_rotateX(calc(var(--my)*-3deg))]">
          <MascotStage state={mascot} level={level} micLevel={micLevel} animate={animate} className="max-w-none" />
        </div>
        <div className="immersive-presence absolute bottom-2 flex flex-col items-center gap-3">
          <div className="immersive-signal flex h-6 items-center gap-1" aria-hidden>
            {[0.45, 0.75, 1, 0.6, 0.9, 0.65, 0.4].map((weight, i) => <span key={i} className="w-[3px] rounded-full bg-[var(--red-hi)]" style={{ height: 3 + energy * weight * 21, opacity: connected ? 0.8 : 0.3 }} />)}
          </div>
          <p className="text-xs tracking-wide text-[var(--text-2)]" aria-live="polite">{presence}</p>
        </div>
      </div>

      {/* actions as toasts */}
      <ol className="immersive-actions relative z-10 mx-auto flex max-h-[25dvh] w-full max-w-3xl flex-col gap-2 overflow-y-auto px-4" aria-label="Rex's actions">
        {toasts.map((e) => (
          <li key={e.id} className="rise rounded-[14px] border border-[var(--line)] bg-black/45 p-3 text-sm backdrop-blur-md">
            <p className="flex items-center gap-2">
              {open.has(e.id) ? <Clock className="size-4 shrink-0 text-[var(--warn)]" /> : <Sparkles className="size-4 shrink-0 text-[var(--red-hi)]" />}
              <span className="min-w-0 flex-1">{e.summary}</span>
            </p>
            {open.has(e.id) && (
              <div className="mt-2 flex gap-2">
                <button onClick={() => onDecide(e.trace_id as string, "approve")} disabled={deciding === e.trace_id} className="rounded-lg bg-[var(--red)] px-3 py-1 text-xs font-medium text-white disabled:opacity-50">
                  Approve
                </button>
                <button onClick={() => onDecide(e.trace_id as string, "deny")} disabled={deciding === e.trace_id} className="rounded-lg border border-[var(--line)] px-3 py-1 text-xs text-[var(--text-2)]">
                  Deny
                </button>
              </div>
            )}
          </li>
        ))}
      </ol>

      {/* captions and the command bar */}
      <div className="immersive-footer relative z-10 flex min-w-0 flex-col items-center gap-3 bg-gradient-to-t from-black/70 to-transparent px-4 pb-6 pt-3">
        <div className="immersive-captions flex w-full max-w-3xl flex-col items-center gap-2 text-center" aria-live="polite">
          {lastMe && (
            <p key={`me-${lastMe.streamInfo.id}`} className="rise line-clamp-1 text-sm text-[var(--text-2)]">
              You: {lastMe.text}
            </p>
          )}
          {lastRex ? (
            <div key={`rex-${lastRex.streamInfo.id}`} className="rise max-h-[18dvh] overflow-y-auto text-lg leading-relaxed text-[var(--text)] [text-shadow:0_2px_18px_rgba(0,0,0,0.8)] sm:text-xl">
              <RichText text={lastRex.text} />
            </div>
          ) : (
            <div className="space-y-2">
              <p className="text-xl font-medium tracking-tight text-[var(--text)] sm:text-2xl">{connected ? "Whenever you're ready." : "What's on your mind?"}</p>
              <p className="text-sm text-[var(--text-2)]">{connected ? "Talk naturally, or type a thought below." : "Tap the mic to talk, or type below."}</p>
            </div>
          )}
        </div>
        <div className="immersive-dock flex w-full max-w-[600px] justify-center">{bar}</div>
        <p className="immersive-shortcuts hidden items-center gap-4 text-[11px] text-[var(--text-2)] sm:flex" aria-hidden>
          <span><kbd>Enter</kbd> to send</span><span><kbd>⌘ / Ctrl K</kbd> to type</span><span><kbd>Esc</kbd> to leave</span>
        </p>
      </div>
    </div>, document.body
  );
}

