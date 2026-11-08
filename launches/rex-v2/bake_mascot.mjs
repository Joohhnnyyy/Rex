// Bake Rex's live mascot for the video with the dashboard's own engine (apps/web/lib/bloub), so expression changes
// morph, the eyes blink and wander, and Rex reacts on the spoken words exactly as in the product.
// Reads plan.json scenes with a "rex" block and timeline.json word times; writes rexanim.json (30 fps frames).
// Run after vo.py (needs word times): node launches/rex-v2/bake_mascot.mjs
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { createRequire } from 'node:module';

const HERE = import.meta.dirname;
const root = path.resolve(HERE, '../../apps/web');
const require = createRequire(path.join(root, 'package.json'));
const ts = require('typescript');
const cache = new Map();
function load(filename) {   // same tiny TS loader as design/logo/mascot-expressions-2026-11-08/export.mjs
  if (cache.has(filename)) return cache.get(filename).exports;
  const mod = { exports: {} };
  cache.set(filename, mod);
  const js = ts.transpileModule(fs.readFileSync(filename, 'utf8'), {
    compilerOptions: { jsx: ts.JsxEmit.ReactJSX, module: ts.ModuleKind.CommonJS } }).outputText;
  const req = (id) => {
    if (!id.startsWith('.') && !id.startsWith('@/')) return require(id);
    const target = id.startsWith('@/') ? path.join(root, id.slice(2)) : path.resolve(path.dirname(filename), id);
    return load(['.ts', '.tsx'].map((e) => target + e).find(fs.existsSync));
  };
  new Function('require', 'module', 'exports', js)(req, mod, mod.exports);
  return mod.exports;
}
const { BotEngine } = load(path.join(root, 'lib/bloub/engine.ts'));
const { EXPRESSIONS } = load(path.join(root, 'lib/bloub/expressions.ts'));
const { CAPSULE } = load(path.join(root, 'lib/mascot.ts'));
const EXPR = Object.fromEntries(EXPRESSIONS.map((e) => [e.id, e]));

const plan = JSON.parse(fs.readFileSync(path.join(HERE, 'plan.json'), 'utf8'));
const tl = JSON.parse(fs.readFileSync(path.join(HERE, 'timeline.json'), 'utf8'));
const FPS = 30, SETTLE = 5;   // engine clock starts at SETTLE so the opening pose is already at rest
const norm = (s) => String(s).toLowerCase().replace(/[^a-z0-9]/g, '');
const r1 = (s) => s.replace(/-?\d+\.\d+/g, (n) => (+n).toFixed(1));

// gaze toward a point on screen, from the mascot's centre (same mapping as cursorLook in lib/mascot.ts)
function lookAt(rex, [tx, ty]) {
  const nx = Math.max(-1, Math.min(1, (tx - rex.x) / 0.5)), ny = Math.max(-1, Math.min(1, (ty - rex.y) / 0.5));
  return { yaw: nx * 16, pitch: 10 - ny * 13, mix: 1, spin: 0, wander: 0 };
}

const out = {};
plan.scenes.forEach((sc, i) => {
  const rex = sc.rex;
  if (!rex) return;
  const s = tl.scenes[i], dur = s.end - s.start;
  const words = (s.words || []).map((w) => ({ w: norm(w.w), t: w.s - s.start }));
  const when = (ev) => {
    if (ev.at != null) return ev.at;
    const hit = words.find((w) => w.w === norm(ev.word));
    assert.ok(hit, `scene ${i}: word "${ev.word}" not in the voiceover (${words.map((w) => w.w).join(' ')})`);
    return hit.t + (ev.offset ?? 0);
  };
  const events = rex.script.map((ev) => ({ ...ev, t: when(ev) })).sort((a, b) => a.t - b.t);
  const first = events.find((e) => e.expr);
  const bot = new BotEngine(100, 'idle', CAPSULE, EXPR[first ? first.expr : 'neutre']);
  let k = 0;
  const frames = [];
  for (let f = 0; f <= Math.ceil(dur * FPS); f++) {
    const t = f / FPS, now = SETTLE + t;
    while (k < events.length && events[k].t <= t + 1e-6) {
      const ev = events[k++], at = SETTLE + ev.t;
      if (ev.expr) { assert.ok(EXPR[ev.expr], `unknown expression ${ev.expr}`); bot.setExpression(EXPR[ev.expr], at); }
      if (ev.state) bot.setState(ev.state, at);
      if (ev.look !== undefined) bot.setLook(ev.look ? lookAt(rex, ev.look) : null, at, ev.lookMorph ?? 0.35);
    }
    const fr = bot.sample(now);
    assert.doesNotMatch(fr.bodyPath, /NaN/);
    frames.push([r1(fr.bodyPath), +fr.bodyAlpha.toFixed(2), fr.eyes.map((e) => [r1(e.d), r1(e.matrix), +(+e.alpha).toFixed(2)])]);
  }
  out[i] = { fps: FPS, frames };
  console.log(`scene ${i}: ${frames.length} frames, events at ${events.map((e) => e.t.toFixed(2)).join(' ')}`);
});
fs.writeFileSync(path.join(HERE, 'rexanim.json'), JSON.stringify(out));
console.log('rexanim.json', (fs.statSync(path.join(HERE, 'rexanim.json')).size / 1e6).toFixed(2), 'MB');
