"use client";

import { useEffect, useId, useRef, useState } from "react";
import type { MascotState } from "@/lib/dashboard";
import { EXPRESSIONS } from "@/lib/bloub/expressions";
import type { BotFrame } from "@/lib/bloub/engine";
import { STATES, STATE_BY_ID } from "@/lib/bloub/states";
import { createMascot, cursorLook, frozenTime, mascotPose, type MascotAnimation, type MascotExpression } from "@/lib/mascot";

export function MascotFace({ state = "idle", level = 0, size = 200, animate = true, className = "", animation, expression, cycle = false }: {
  state?: MascotState; level?: number; size?: number; animate?: boolean; className?: string;
  animation?: MascotAnimation; expression?: MascotExpression; cycle?: boolean;
}) {
  const uid = useId().replace(/:/g, "");
  const svg = useRef<SVGSVGElement>(null);
  const [engine] = useState(() => createMascot(state, animation, expression));
  const clock = useRef(0);
  const volume = useRef(level);
  volume.current = level;
  const liveState = useRef(state);
  liveState.current = state;
  const pose = mascotPose(state, animation, expression);
  const [frame, setFrame] = useState(() => engine.sample(frozenTime(pose.animation)));

  useEffect(() => {
    engine.setExpression(EXPRESSIONS.find((e) => e.id === pose.expression)!, clock.current);
    engine.setState(pose.animation, clock.current);
    if (!animate) setFrame(createMascot(state, animation, expression).sample(frozenTime(pose.animation)));
    else if (cycle) engine.setState("idle", clock.current);
  }, [engine, pose.animation, pose.expression, animate, state, animation, expression, cycle]);

  useEffect(() => {
    if (!animate) return;
    let pointer: { x: number; y: number } | null = null;
    let raf = 0, last = 0, index = 0;
    let until = clock.current + (STATE_BY_ID.get(engine.state)!.duration);
    const move = (event: PointerEvent) => {
      if (event.pointerType !== "touch") pointer = { x: event.clientX, y: event.clientY };
    };
    const leave = () => { pointer = null; };
    const tick = (ms: number) => {
      const dt = last ? Math.min((ms - last) / 1000, 0.064) : 0;
      last = ms;
      clock.current += dt;
      if (cycle && clock.current >= until) {
        index = (index + 1) % STATES.length;
        engine.setState(STATES[index].id, clock.current);
        until = clock.current + STATES[index].duration;
      }
      const box = svg.current?.getBoundingClientRect();
      const tracking = size > 40 && STATE_BY_ID.get(engine.state)!.baseFace;
      engine.setLook(tracking && pointer && box ? cursorLook(pointer.x, pointer.y, box, { width: innerWidth, height: innerHeight }) : null, clock.current);
      const next = engine.sample(clock.current);
      // Voice opens the eyes, leaving the body and the frame's projection intact.
      const audio = Math.max(0, Math.min(1, volume.current));
      if (audio && (liveState.current === "speaking" || liveState.current === "listening")) {
        next.eyes = next.eyes.map((eye) => ({ ...eye, matrix: `${eye.matrix} scale(1 ${1 + audio * 0.18})` }));
      }
      setFrame(next);
      raf = requestAnimationFrame(tick);
    };
    if (size > 40) {
      window.addEventListener("pointermove", move);
      document.addEventListener("pointerleave", leave);
    }
    raf = requestAnimationFrame(tick);
    return () => {
      cancelAnimationFrame(raf);
      window.removeEventListener("pointermove", move);
      document.removeEventListener("pointerleave", leave);
    };
  }, [engine, animate, size, cycle]);

  const dots = (items: BotFrame["dots"]) => items.map((dot, i) => {
    const fill = dot.color ?? (dot.depth === undefined ? "var(--red)" : `color-mix(in srgb, var(--red) ${dot.depth * 100}%, #161c21)`);
    return dot.d ? <path key={i} d={dot.d} transform={`translate(${dot.x} ${dot.y}) rotate(${dot.rot ?? 0}) scale(100)`} fill={fill} opacity={dot.opacity} /> : <circle key={i} cx={dot.x} cy={dot.y} r={dot.r} fill={fill} opacity={dot.opacity} />;
  });
  const arcs = (front: boolean) => frame.arcs.map((arc) => <path key={arc.id} d={front ? arc.front : arc.back} stroke={`url(#${uid}-${arc.id})`} strokeWidth={arc.width} opacity={arc.opacity} />);
  return (
    <svg ref={svg} viewBox="-158 -158 316 316" width={size} height={size} className={className} role="img" aria-label={`Rex mascot, ${state}`} data-animation={engine.state} data-expression={pose.expression}>
      <defs>
        <clipPath id={`${uid}-body`}><path d={frame.bodyPath} /></clipPath>
        <mask id={`${uid}-notch`} maskUnits="userSpaceOnUse" x="-158" y="-158" width="316" height="316"><path d={frame.bodyPath} fill="white" />{frame.notch && <circle cx={frame.notch.x} cy={frame.notch.y} r={frame.notch.r} fill="black" />}</mask>
        {frame.arcs.map((arc) => <linearGradient key={arc.id} id={`${uid}-${arc.id}`} gradientUnits="userSpaceOnUse" x1={arc.grad.x1} y1={arc.grad.y1} x2={arc.grad.x2} y2={arc.grad.y2}>{arc.grad.stops.map((color, i) => <stop key={i} offset={i / (arc.grad.stops.length - 1)} stopColor={color} />)}</linearGradient>)}
      </defs>
      <g fill="none" strokeLinecap="round">{arcs(false)}</g>
      {frame.dotsBehind && dots(frame.dots)}
      <g opacity={frame.bodyAlpha} mask={`url(#${uid}-notch)`}>
        <path d={frame.bodyPath} fill="var(--red, #ff4055)" />
        <g clipPath={`url(#${uid}-body)`}>{frame.eyes.map((eye, i) => <path key={i} data-eye="" d={eye.d} transform={eye.matrix} opacity={eye.alpha} fill="white" />)}</g>
      </g>
      {!frame.dotsBehind && dots(frame.dots)}
      {frame.notif && <circle cx={frame.notif.x} cy={frame.notif.y} r={frame.notif.r} fill="white" />}
      <g fill="none" strokeLinecap="round">{arcs(true)}</g>
    </svg>
  );
}

export function MascotStage({ state, level = 0, micLevel = 0, animate = true, className = "max-w-[370px]", animation, expression, cycle }: {
  state: MascotState; level?: number; micLevel?: number; animate?: boolean; className?: string;
  animation?: MascotAnimation; expression?: MascotExpression; cycle?: boolean;
}) {
  return <div className={`relative mx-auto aspect-square w-full ${className}`} data-state={state}><MascotFace state={state} level={state === "listening" ? micLevel : level} size={400} animate={animate} className="size-full" animation={animation} expression={expression} cycle={cycle} /></div>;
}
