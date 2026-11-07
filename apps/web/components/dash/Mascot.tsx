"use client";

import { useEffect, useId, useState } from "react";

import type { MascotState } from "@/lib/dashboard";

// Rex's face: a soft red rounded square with heavy-lidded, slightly sarcastic eyes. Pure SVG, so it stays
// crisp from 32px (brand mark) to 300px (centre stage). Each state sets lids, brows, pupils, mouth and tilt.
type Face = {
  lid: number; // 0 = eyes wide open, 1 = closed
  lidTilt: number; // degrees; positive droops the outer corners
  brow: number; // px offset (negative = raised)
  browTilt: number;
  look: [number, number]; // pupil offset
  mouth: "flat" | "smile" | "grin" | "o" | "wavy" | "frown" | "open";
  tilt: number; // whole-body rotation
};

const FACES: Record<MascotState, Face> = {
  idle: { lid: 0.44, lidTilt: -9, brow: 0, browTilt: -7, look: [0, 3], mouth: "flat", tilt: 0 },
  listening: { lid: 0.18, lidTilt: 2, brow: -4, browTilt: 0, look: [0, 0], mouth: "flat", tilt: 0 },
  thinking: { lid: 0.32, lidTilt: -4, brow: -5, browTilt: -10, look: [5, -5], mouth: "wavy", tilt: -3 },
  speaking: { lid: 0.3, lidTilt: -5, brow: -2, browTilt: -3, look: [0, 1], mouth: "open", tilt: 0 },
  happy: { lid: 0.3, lidTilt: -6, brow: -4, browTilt: -4, look: [0, 0], mouth: "grin", tilt: 2 },
  confused: { lid: 0.24, lidTilt: 10, brow: -3, browTilt: 18, look: [-4, -2], mouth: "wavy", tilt: -5 },
  surprised: { lid: 0, lidTilt: 0, brow: -9, browTilt: 0, look: [0, 0], mouth: "o", tilt: 0 },
  error: { lid: 0.36, lidTilt: -12, brow: 2, browTilt: -16, look: [0, 3], mouth: "frown", tilt: -2 },
  sleeping: { lid: 1, lidTilt: 0, brow: 3, browTilt: 4, look: [0, 4], mouth: "flat", tilt: 4 },
  success: { lid: 0.2, lidTilt: -4, brow: -5, browTilt: -2, look: [0, -1], mouth: "smile", tilt: 0 },
};

const MOUTHS: Record<Face["mouth"], string> = {
  flat: "M88 146 Q100 149 112 145",
  smile: "M84 142 Q100 156 116 142",
  grin: "M82 140 Q100 160 118 140 Q100 150 82 140 Z",
  o: "M100 140 m-6 0 a6 7 0 1 0 12 0 a6 7 0 1 0 -12 0",
  wavy: "M86 147 Q93 141 100 147 T114 145",
  frown: "M86 150 Q100 140 114 150",
  open: "",
};

function useBlink(enabled: boolean) {
  const [shut, setShut] = useState(false);
  useEffect(() => {
    if (!enabled) return;
    let t: ReturnType<typeof setTimeout>;
    const loop = () => {
      t = setTimeout(
        () => {
          setShut(true);
          t = setTimeout(() => {
            setShut(false);
            loop();
          }, 130);
        },
        2600 + Math.random() * 3400,
      );
    };
    loop();
    return () => clearTimeout(t);
  }, [enabled]);
  return shut;
}

function useGlance(enabled: boolean) {
  const [g, setG] = useState<[number, number]>([0, 0]);
  useEffect(() => {
    if (!enabled) return;
    const id = setInterval(() => setG([Math.round((Math.random() - 0.5) * 8), Math.round((Math.random() - 0.5) * 3)]), 3200);
    return () => clearInterval(id);
  }, [enabled]);
  return enabled ? g : ([0, 0] as [number, number]);
}

function Eye({ cx, cy, side, face, shut, glance, ids }: {
  cx: number;
  cy: number;
  side: -1 | 1;
  face: Face;
  shut: boolean;
  glance: [number, number];
  ids: { body: string; clip: string };
}) {
  const rx = 25;
  const ry = 19;
  const lid = shut ? 1 : face.lid;
  const lidY = cy - ry + lid * ry * 2;
  const [lx, ly] = [face.look[0] + glance[0], face.look[1] + glance[1]];
  const clip = `${ids.clip}-${side}`;
  return (
    <g>
      <clipPath id={clip}>
        <ellipse cx={cx} cy={cy} rx={rx} ry={ry} />
      </clipPath>
      <ellipse cx={cx} cy={cy} rx={rx} ry={ry} fill="#fff" />
      <g clipPath={`url(#${clip})`}>
        <g className="mascot-ease" style={{ transform: `translate(${lx}px, ${ly + 3}px)` }}>
          <circle cx={cx} cy={cy} r={11.5} fill="#141414" />
          <circle cx={cx + 4} cy={cy - 4} r={3.4} fill="#fff" />
        </g>
        {/* the lid: body-coloured, tilted for attitude, with a dark lash line */}
        <g
          className="mascot-ease"
          style={{ transform: `rotate(${side * face.lidTilt}deg)`, transformOrigin: `${cx}px ${cy}px` }}
        >
          <rect x={cx - 34} y={cy - 40} width={68} height={lidY - (cy - 40)} fill={`url(#${ids.body})`} className="mascot-ease" />
          <line x1={cx - 34} x2={cx + 34} y1={lidY} y2={lidY} stroke="#2a0a0d" strokeWidth={4} strokeLinecap="round" />
        </g>
      </g>
      <ellipse cx={cx} cy={cy} rx={rx} ry={ry} fill="none" stroke="#2a0a0d" strokeWidth={3.5} />
    </g>
  );
}

export function MascotFace({
  state = "idle",
  level = 0,
  size = 200,
  animate = true,
  className = "",
}: {
  state?: MascotState;
  level?: number; // 0-1 voice level, opens the mouth while speaking
  size?: number;
  animate?: boolean;
  className?: string;
}) {
  const uid = useId().replace(/:/g, "");
  const ids = { body: `b${uid}`, shade: `s${uid}`, clip: `c${uid}`, hl: `h${uid}` };
  const face = FACES[state];
  const shut = useBlink(animate && state !== "sleeping");
  const glance = useGlance(animate && state === "idle");
  const open = Math.min(1, level * 2.2);

  return (
    <svg
      viewBox="0 0 200 200"
      width={size}
      height={size}
      className={`${animate ? "mascot-float" : ""} ${className}`}
      role="img"
      aria-label={`Rex mascot, ${state}`}
    >
      <defs>
        <linearGradient id={ids.body} x1="0.2" y1="0" x2="0.8" y2="1">
          <stop offset="0" stopColor="#ff6b62" />
          <stop offset="0.55" stopColor="#f2303a" />
          <stop offset="1" stopColor="#b8172a" />
        </linearGradient>
        <radialGradient id={ids.hl} cx="0.32" cy="0.22" r="0.5">
          <stop offset="0" stopColor="#fff" stopOpacity="0.38" />
          <stop offset="1" stopColor="#fff" stopOpacity="0" />
        </radialGradient>
        <radialGradient id={ids.shade} cx="0.5" cy="1.05" r="0.7">
          <stop offset="0" stopColor="#5a0610" stopOpacity="0.55" />
          <stop offset="1" stopColor="#5a0610" stopOpacity="0" />
        </radialGradient>
      </defs>
      <g className="mascot-ease" style={{ transform: `rotate(${face.tilt}deg)`, transformOrigin: "100px 110px" }}>
        {/* slightly asymmetric squircle body */}
        <path
          d="M100 42 C150 40 182 48 184 98 C186 146 164 164 102 165 C38 166 14 150 16 102 C18 54 46 44 100 42 Z"
          fill={`url(#${ids.body})`}
        />
        <path
          d="M100 42 C150 40 182 48 184 98 C186 146 164 164 102 165 C38 166 14 150 16 102 C18 54 46 44 100 42 Z"
          fill={`url(#${ids.shade})`}
        />
        <ellipse cx="74" cy="70" rx="40" ry="15" fill={`url(#${ids.hl})`} />

        {/* brows */}
        {[-1, 1].map((side) => (
          <path
            key={side}
            d={side < 0 ? "M52 80 Q66 75 80 78" : "M120 77 Q134 74 148 79"}
            stroke="#2a0a0d"
            strokeWidth={4.5}
            strokeLinecap="round"
            fill="none"
            className="mascot-ease"
            style={{
              transform: `translateY(${face.brow}px) rotate(${side * face.browTilt}deg)`,
              transformOrigin: side < 0 ? "66px 78px" : "134px 77px",
            }}
          />
        ))}

        <Eye cx={67} cy={110} side={-1} face={face} shut={shut} glance={glance} ids={ids} />
        <Eye cx={133} cy={109} side={1} face={face} shut={shut} glance={glance} ids={ids} />

        {face.mouth === "open" ? (
          <ellipse cx={100} cy={146} rx={9 + open * 3} ry={2 + open * 8} fill="#3a0a10" className="mascot-ease" />
        ) : (
          <path
            d={MOUTHS[face.mouth]}
            stroke="#3a0a10"
            strokeWidth={3.5}
            strokeLinecap="round"
            fill={face.mouth === "grin" || face.mouth === "o" ? "#3a0a10" : "none"}
          />
        )}

        {state === "sleeping" && (
          <text x="150" y="44" fill="#ffd0d4" fontSize="16" fontWeight="700">
            z
          </text>
        )}
      </g>
    </svg>
  );
}

// Centre stage: the face inside a diagnostic HUD, standing on a holographic platform.
export function MascotStage({
  state,
  level = 0,
  micLevel = 0,
  animate = true,
}: {
  state: MascotState;
  level?: number;
  micLevel?: number;
  animate?: boolean;
}) {
  const warn = state === "error";
  const ticks = Array.from({ length: 72 }, (_, i) => i * 5);
  const pulse = state === "listening" ? 1 + Math.min(micLevel, 1) * 0.05 : 1;
  return (
    <div className="relative mx-auto aspect-square w-full max-w-[400px]" data-state={state}>
      {/* HUD */}
      <svg viewBox="0 0 400 400" className="absolute inset-0 size-full" aria-hidden>
        <defs>
          <radialGradient id="hud-glow" cx="0.5" cy="0.48" r="0.5">
            <stop offset="0" stopColor="var(--red)" stopOpacity="0.22" />
            <stop offset="0.6" stopColor="var(--red)" stopOpacity="0.05" />
            <stop offset="1" stopColor="var(--red)" stopOpacity="0" />
          </radialGradient>
        </defs>
        <circle cx="200" cy="190" r="190" fill="url(#hud-glow)" />
        {/* corner brackets */}
        {[
          "M24 40 V24 H40",
          "M360 24 H376 V40",
          "M24 360 V376 H40",
          "M376 360 V376 H360",
        ].map((d) => (
          <path key={d} d={d} stroke="var(--text-2)" strokeOpacity="0.5" strokeWidth="1.5" fill="none" />
        ))}
        {/* crosshair stubs */}
        <g stroke="var(--red)" strokeOpacity="0.55" strokeWidth="1.5">
          <line x1="14" x2="38" y1="190" y2="190" />
          <line x1="362" x2="386" y1="190" y2="190" />
        </g>
        {/* outer tick ring (responds to the mic while listening) */}
        <g
          className={animate ? "hud-spin-slow" : ""}
          style={{ transformOrigin: "200px 190px", transform: `scale(${pulse})`, transition: "transform 120ms" }}
        >
          {ticks.map((a) => (
            <line
              key={a}
              x1="200"
              x2="200"
              y1={a % 30 === 0 ? 22 : 26}
              y2="32"
              stroke={a % 30 === 0 ? "var(--red)" : "var(--text-2)"}
              strokeOpacity={a % 30 === 0 ? 0.7 : 0.22}
              strokeWidth="1.2"
              transform={`rotate(${a} 200 190)`}
            />
          ))}
        </g>
        <circle cx="200" cy="190" r="150" fill="none" stroke="var(--text-2)" strokeOpacity="0.12" />
        {/* lit arc segments */}
        <g
          className={animate ? (state === "thinking" ? "hud-spin-fast" : "hud-spin-mid") : ""}
          style={{ transformOrigin: "200px 190px" }}
        >
          <circle
            cx="200"
            cy="190"
            r="150"
            fill="none"
            stroke={warn ? "var(--warn)" : "var(--red)"}
            strokeWidth="4"
            strokeLinecap="round"
            strokeDasharray="38 120 14 160 60 550"
            opacity={state === "success" ? 1 : 0.85}
          />
        </g>
        <circle cx="200" cy="190" r="128" fill="none" stroke="var(--red)" strokeOpacity="0.18" strokeDasharray="2 6" />
        <path d="M150 20 A170 170 0 0 1 250 20" stroke="var(--red)" strokeWidth="5" fill="none" strokeLinecap="round" opacity="0.9" />
      </svg>

      {/* platform */}
      <svg viewBox="0 0 400 120" className="absolute bottom-[2%] left-1/2 w-[64%] -translate-x-1/2" aria-hidden>
        <defs>
          <linearGradient id="beam" x1="0" y1="1" x2="0" y2="0">
            <stop offset="0" stopColor="var(--red)" stopOpacity="0.35" />
            <stop offset="1" stopColor="var(--red)" stopOpacity="0" />
          </linearGradient>
          <linearGradient id="deck" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0" stopColor="#2a1418" />
            <stop offset="1" stopColor="#0d0b0e" />
          </linearGradient>
        </defs>
        <path d="M110 70 L150 0 H250 L290 70 Z" fill="url(#beam)" />
        <ellipse cx="200" cy="92" rx="190" ry="26" fill="url(#deck)" stroke="var(--red)" strokeOpacity="0.35" />
        <ellipse cx="200" cy="80" rx="150" ry="20" fill="#120c0f" stroke="var(--red)" strokeOpacity="0.55" />
        <ellipse cx="200" cy="72" rx="96" ry="12" fill="none" stroke="var(--red-hi)" strokeWidth="2" opacity="0.9" />
        <ellipse cx="200" cy="72" rx="60" ry="6" fill="var(--red)" opacity="0.35" />
      </svg>

      <div className="absolute left-1/2 top-[46%] w-[56%] -translate-x-1/2 -translate-y-1/2">
        <MascotFace state={state} level={level} size={400} animate={animate} className="size-full drop-shadow-[0_18px_30px_rgba(255,40,60,0.35)]" />
      </div>
    </div>
  );
}
