import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';
import { test } from 'node:test';
import ts from 'typescript';
import React from 'react';
import { renderToStaticMarkup } from 'react-dom/server';

// Use the installed TypeScript compiler instead of adding a test runner.
const root = fileURLToPath(new URL('../', import.meta.url));
const require = createRequire(import.meta.url);
const cache = new Map();
function load(filename) {
  if (cache.has(filename)) return cache.get(filename).exports;
  const compiledModule = { exports: {} };
  cache.set(filename, compiledModule);
  const compiled = ts.transpileModule(fs.readFileSync(filename, 'utf8'), {
    compilerOptions: { jsx: ts.JsxEmit.ReactJSX, module: ts.ModuleKind.CommonJS },
  }).outputText;
  const localRequire = (id) => {
    if (!id.startsWith('.') && !id.startsWith('@/')) return require(id);
    const target = id.startsWith('@/') ? path.join(root, id.slice(2)) : path.resolve(path.dirname(filename), id);
    const file = ['.ts', '.tsx'].map(ext => target + ext).find(fs.existsSync);
    return load(file);
  };
  new Function('require', 'module', 'exports', compiled)(localRequire, compiledModule, compiledModule.exports);
  return compiledModule.exports;
}
const { BotEngine } = load(path.join(root, 'lib/bloub/engine.ts'));
const { STATES } = load(path.join(root, 'lib/bloub/states.ts'));
const { EXPRESSIONS } = load(path.join(root, 'lib/bloub/expressions.ts'));
const { createMascot, mascotPose, cursorLook, ANIMATIONS, EXPRESSIONS_LIST } = load(path.join(root, 'lib/mascot.ts'));
const { MascotFace } = load(path.join(root, 'components/dash/Mascot.tsx'));
const liveStates = ['idle', 'listening', 'thinking', 'speaking', 'happy', 'confused', 'surprised', 'error', 'sleeping', 'success'];

function finite(frame) {
  assert.ok(frame.bodyPath.length > 10);
  assert.doesNotMatch(JSON.stringify(frame), /NaN|Infinity|null/);
  for (const eye of frame.eyes) assert.ok(eye.alpha >= 0 && eye.alpha <= 1);
}

test('all 15 animations produce finite deterministic frames, including transitions', () => {
  assert.equal(ANIMATIONS.length, 15);
  for (const animation of ANIMATIONS) {
    const engine = createMascot('idle', animation);
    for (let t = 0; t < 4; t += 0.1) {
      const frame = engine.sample(t);
      // Null notification/notch are valid, so inspect geometry separately.
      assert.doesNotMatch(JSON.stringify(frame), /NaN|Infinity/);
      assert.deepEqual(engine.sample(t), frame);
    }
    engine.setState('idle', 4);
    assert.doesNotMatch(JSON.stringify(engine.sample(4.15)), /NaN|Infinity/);
  }
});

test('all 16 expressions render distinct pairs of projected eyes on the capsule', () => {
  assert.equal(EXPRESSIONS_LIST.length, 16);
  const pairs = new Set();
  for (const expression of EXPRESSIONS) {
    const frame = createMascot('idle', 'idle', expression.id).sample(0);
    assert.equal(frame.eyes.length, 2);
    finite({ ...frame, notif: undefined, notch: undefined });
    pairs.add(JSON.stringify(frame.eyes));
  }
  assert.equal(pairs.size, 16);
});

test('live states retain accessible labels and map to valid animations/expressions', () => {
  for (const state of liveStates) {
    const pose = mascotPose(state);
    assert.ok(STATES.some(s => s.id === pose.animation));
    assert.ok(EXPRESSIONS.some(e => e.id === pose.expression));
    const svg = renderToStaticMarkup(React.createElement(MascotFace, { state, animate: false }));
    assert.ok(svg.includes(`aria-label="Rex mascot, ${state}"`));
    assert.doesNotMatch(svg, /NaN|Infinity/);
  }
});

test('cursor tracking clamps targets and rejects hidden or invalid bounds', () => {
  const box = { left: 100, top: 100, width: 200, height: 200 };
  const viewport = { width: 1000, height: 800 };
  assert.equal(cursorLook(200, 200, { ...box, width: 0 }, viewport), null);
  assert.equal(cursorLook(NaN, 200, box, viewport), null);
  assert.equal(cursorLook(10000, -10000, box, viewport).yaw, 16);
  assert.equal(cursorLook(10000, -10000, box, viewport).pitch, 23);
  const engine = new BotEngine();
  engine.setLook(cursorLook(900, 300, box, viewport), 0);
  const before = engine.sample(0.1);
  engine.setLook({ yaw: NaN, pitch: 0, mix: 1, spin: 0, wander: 0 }, 0.1);
  assert.deepEqual(engine.sample(0.1), before);
});

test('interrupting a state morph continues from the visible composite pose', () => {
  const engine = createMascot('idle');
  engine.setState('wide', 1);
  const before = engine.sample(1.1);
  engine.setState('idle', 1.1);
  const after = engine.sample(1.1);
  assert.equal(after.bodyPath, before.bodyPath);
  assert.deepEqual(after.eyes, before.eyes);
});


test('multiple mascot instances keep their masks and gradients independent', () => {
  const svg = renderToStaticMarkup(React.createElement('div', null,
    React.createElement(MascotFace, { animation: 'orbit', animate: false }),
    React.createElement(MascotFace, { animation: 'orbit', animate: false })));
  const ids = [...svg.matchAll(/ id="([^"]+)"/g)].map(m => m[1]);
  assert.equal(ids.length, new Set(ids).size);
});
