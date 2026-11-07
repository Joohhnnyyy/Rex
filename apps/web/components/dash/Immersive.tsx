"use client";

import { TrackToggle, type useTranscriptions } from "@livekit/components-react";
import { Track } from "livekit-client";
import { Clock, Minimize2, MonitorUp, PhoneOff, Sparkles } from "lucide-react";
import { useEffect, useRef, useState, type ReactNode } from "react";

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
    addEventListener("resize", resize);
    return () => {
      cancelAnimationFrame(raf);
      removeEventListener("resize", resize);
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
  const [now, setNow] = useState(() => Date.now());
  useEffect(() => {
    const id = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(id);
  }, []);

  // Depth: the mouse tilts the mascot one way and drifts the particles the other (CSS vars, no re-render).
  useEffect(() => {
    const el = scene.current;
    if (!el || !animate) return;
    const move = (e: PointerEvent) => {
      el.style.setProperty("--mx", ((e.clientX / innerWidth) * 2 - 1).toFixed(3));
      el.style.setProperty("--my", ((e.clientY / innerHeight) * 2 - 1).toFixed(3));
    };
    addEventListener("pointermove", move);
    return () => removeEventListener("pointermove", move);
  }, [animate]);

  const lastRex = [...transcriptions].reverse().find((t) => t.participantInfo.identity !== identity);
  const lastMe = [...transcriptions].reverse().find((t) => t.participantInfo.identity === identity);
  const open = openApprovals(events);
  const toasts = events.filter((e) => open.has(e.id) || now - new Date(e.ts).getTime() < 9000).slice(0, 3);

  return (
    <div
      ref={scene}
      className="fixed inset-0 z-40 overflow-hidden bg-[radial-gradient(ellipse_at_50%_40%,#2a0d14_0%,#0d0a0d_55%,#060607_100%)] [--mx:0] [--my:0]"
      role="region"
      aria-label="Immersive call with Rex"
    >
      <div className="absolute inset-0 transition-transform duration-300 ease-out [transform:translate(calc(var(--mx)*-14px),calc(var(--my)*-10px))]">
        <ParticleField level={level} animate={animate} />
      </div>
      {/* faint grid floor for depth */}
      <div className="pointer-events-none absolute inset-x-0 bottom-0 h-[38%] [background:linear-gradient(transparent,rgba(255,64,85,0.1)),repeating-linear-gradient(90deg,rgba(255,64,85,0.12)_0_1px,transparent_1px_64px)] [mask-image:linear-gradient(transparent,black)] [transform:perspective(600px)_rotateX(58deg)] [transform-origin:bottom]" />

      {/* top: status and controls */}
      <header className="relative z-10 flex items-center justify-between px-5 py-4 sm:px-8">
        <span className="flex items-center gap-3">
          <span className="text-lg font-semibold tracking-[0.4em]">REX</span>
          <span className="flex items-center gap-2 rounded-full border border-[var(--line)] bg-black/30 px-3 py-1 text-xs text-[var(--text-2)] backdrop-blur" aria-live="polite">
            <span className={`size-1.5 rounded-full ${connected ? "live-dot bg-[var(--red)]" : "bg-[var(--faint)]"}`} aria-hidden />
            {status}
            {language && <span className="text-[var(--red-hi)]">· {language}</span>}
          </span>
        </span>
        <span className="flex items-center gap-2">
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
          <button onClick={onExit} aria-label="Leave immersive view (Esc)" title="Leave immersive view (Esc)" className="grid size-10 place-items-center rounded-full border border-[var(--line)] bg-black/30 text-[var(--text-2)] backdrop-blur hover:text-[var(--text)]">
            <Minimize2 className="size-4" />
          </button>
          {connected && (
            <button onClick={onEnd} aria-label="End call" className="grid size-10 place-items-center rounded-full bg-[var(--red)] text-white hover:bg-[var(--red-hi)]">
              <PhoneOff className="size-4" />
            </button>
          )}
        </span>
      </header>

      {/* the mascot, tilting with the mouse */}
      <div className="absolute inset-x-0 top-[9%] flex justify-center sm:top-[4%]">
        <div className="w-[min(92vw,68vh,640px)] transition-transform duration-300 ease-out [transform:perspective(900px)_rotateY(calc(var(--mx)*7deg))_rotateX(calc(var(--my)*-5deg))_translate(calc(var(--mx)*10px),calc(var(--my)*6px))]">
          <MascotStage state={mascot} level={level} micLevel={micLevel} animate={animate} className="max-w-none" />
        </div>
      </div>

      {/* actions as toasts */}
      <ol className="absolute right-4 top-20 z-10 flex w-[min(340px,calc(100vw-2rem))] flex-col gap-2 sm:right-8" aria-label="Rex's actions">
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
      <div className="absolute inset-x-0 bottom-0 z-10 flex flex-col items-center gap-3 bg-gradient-to-t from-black/70 via-black/30 to-transparent px-4 pb-6 pt-16">
        <div className="flex min-h-[4.5rem] w-full max-w-3xl flex-col items-center gap-1.5 text-center" aria-live="polite">
          {lastMe && (
            <p key={`me-${lastMe.streamInfo.id}`} className="rise line-clamp-1 text-sm text-[var(--text-2)]">
              You: {lastMe.text}
            </p>
          )}
          {lastRex ? (
            <div key={`rex-${lastRex.streamInfo.id}`} className="rise max-h-[22vh] overflow-y-auto text-lg leading-relaxed text-[var(--text)] [text-shadow:0_2px_18px_rgba(0,0,0,0.8)] sm:text-xl">
              <RichText text={lastRex.text} />
            </div>
          ) : (
            <p className="text-lg text-[var(--text-2)]">{connected ? "Say something, or type below." : "Press the mic or type to talk to Rex."}</p>
          )}
        </div>
        {bar}
      </div>
    </div>
  );
}

