"use client";

import { useEffect, useRef } from "react";
import * as THREE from "three";

// Rex's face: one camera-facing plane with a polar shader (idea from JARVIS's reactor,
// own look). Props are read every frame through a ref, so React re-renders are cheap.
// state: LiveKit agent state; level: agent audio volume 0..1.

const fragment = /* glsl */ `
  uniform float uTime, uLevel, uSpeed, uSat, uHue;
  uniform vec3 uColor;
  varying vec2 vUv;

  float hash(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
  float noise(vec2 p) {
    vec2 i = floor(p), f = fract(p), u = f * f * (3.0 - 2.0 * f);
    return mix(mix(hash(i), hash(i + vec2(1, 0)), u.x), mix(hash(i + vec2(0, 1)), hash(i + vec2(1, 1)), u.x), u.y);
  }
  float fbm(vec2 p) { float v = 0.0, a = 0.5; for (int i = 0; i < 5; i++) { v += a * noise(p); p *= 2.03; a *= 0.5; } return v; }

  void main() {
    vec2 p = vUv * 2.0 - 1.0;
    float r = length(p), a = atan(p.y, p.x);
    vec2 ring = vec2(cos(a), sin(a));               // seam-free angular sample
    float t = uTime * uSpeed;

    // Body: radius wobbles with noise, swells with voice level.
    float R = 0.55 + (fbm(ring * 2.5 + t * 0.3) - 0.5) * (0.10 + uLevel * 0.25) + uLevel * 0.08;
    float body = smoothstep(R, R - 0.06, r);

    // Inside: slow swirling plasma, brighter toward the centre.
    vec2 q = p * 2.2;
    float swirl = fbm(q + vec2(fbm(q + t * 0.4), fbm(q - t * 0.35)) * 1.6);
    float core = body * (0.45 + 0.75 * swirl) * (1.15 - r);

    // Rim + outer glow; speaking adds a ripple travelling outward.
    float rim = exp(-pow((r - R) / 0.025, 2.0));
    float glow = exp(-max(r - R, 0.0) * 7.0) * (1.0 - body) * (0.35 + uLevel);
    float ripple = uLevel * exp(-pow((r - R - fract(t * 0.6) * 0.35) / 0.02, 2.0)) * (1.0 - fract(t * 0.6));

    vec3 base = uColor;
    vec3 hot = mix(base, vec3(1.0, 0.93, 0.82), 0.65);
    vec3 tint = mix(base, vec3(0.86, 0.32, 0.78), uHue);   // thinking leans magenta
    vec3 col = tint * (core + glow) + hot * (rim * 0.9 + ripple) + hot * core * swirl * 0.5;

    float gray = dot(col, vec3(0.299, 0.587, 0.114));
    col = mix(vec3(gray), col, uSat);
    float alpha = clamp(core + glow + rim + ripple, 0.0, 1.0);
    // Un-premultiply so faint areas keep their hue instead of going muddy against the page.
    gl_FragColor = vec4(clamp(col / max(alpha, 0.001), 0.0, 1.0), alpha);
  }
`;

const vertex = /* glsl */ `
  varying vec2 vUv;
  void main() { vUv = uv; gl_Position = vec4(position.xy, 0.0, 1.0); }
`;

// Target uniforms per agent state; the loop eases toward them.
const LOOK: Record<string, { speed: number; sat: number; hue: number }> = {
  listening: { speed: 0.6, sat: 1, hue: 0 },
  thinking: { speed: 2.2, sat: 1, hue: 0.6 },
  speaking: { speed: 1.2, sat: 1, hue: 0 },
};
const IDLE = { speed: 0.25, sat: 0.25, hue: 0 };

export function RexOrb({ state = "idle", level = 0, size = 220 }: { state?: string; level?: number; size?: number }) {
  const host = useRef<HTMLDivElement>(null);
  const live = useRef({ state, level });
  live.current = { state, level };

  useEffect(() => {
    const el = host.current!;
    let renderer: THREE.WebGLRenderer;
    try {
      renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });
    } catch {
      el.classList.add("orb", "orb-idle"); // no WebGL: fall back to the CSS orb
      return;
    }
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.setSize(size, size);
    el.appendChild(renderer.domElement);

    const accent = getComputedStyle(document.documentElement).getPropertyValue("--accent").trim() || "#e8772e";
    const u = {
      uTime: { value: 0 },
      uLevel: { value: 0 },
      uSpeed: { value: IDLE.speed },
      uSat: { value: IDLE.sat },
      uHue: { value: 0 },
      uColor: { value: new THREE.Color(accent) },
    };
    const scene = new THREE.Scene();
    const mat = new THREE.ShaderMaterial({ uniforms: u, vertexShader: vertex, fragmentShader: fragment, transparent: true });
    const mesh = new THREE.Mesh(new THREE.PlaneGeometry(2, 2), mat);
    scene.add(mesh);
    const camera = new THREE.Camera();

    const still = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const clock = new THREE.Clock();
    let raf = 0;
    const tick = () => {
      const dt = Math.min(clock.getDelta(), 0.1);
      const { state: s, level: lv } = live.current;
      const want = LOOK[s] ?? IDLE;
      const k = 1 - Math.exp(-dt * 6); // frame-rate independent easing
      u.uSpeed.value += (want.speed * (still ? 0.15 : 1) - u.uSpeed.value) * k;
      u.uSat.value += (want.sat - u.uSat.value) * k;
      u.uHue.value += (want.hue - u.uHue.value) * k;
      u.uLevel.value += (Math.min(lv * 2.5, 1) * (still ? 0.3 : 1) - u.uLevel.value) * (1 - Math.exp(-dt * 14));
      u.uTime.value += dt;
      renderer.render(scene, camera);
      raf = requestAnimationFrame(tick);
    };
    tick();

    return () => {
      cancelAnimationFrame(raf);
      mesh.geometry.dispose();
      mat.dispose();
      renderer.dispose();
      renderer.domElement.remove();
    };
  }, [size]);

  return <div ref={host} style={{ width: size, height: size }} aria-hidden />;
}
