import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { createRequire } from 'node:module';
const require = createRequire(new URL('../../../apps/web/package.json', import.meta.url));
const ts = require('typescript');
const root = path.resolve(import.meta.dirname, '../../../apps/web');
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

const { createMascot, EXPRESSIONS_LIST } = load(path.join(root, 'lib/mascot.ts'));
const output = import.meta.dirname;
const entries = EXPRESSIONS_LIST.map(([id, name]) => {
 const frame = createMascot('idle', 'idle', id).sample(1);
 assert.equal(frame.eyes.length, 2);
 assert.doesNotMatch(JSON.stringify(frame), /NaN|Infinity/);
 const eyes = frame.eyes.map(eye => `<path d="${eye.d}" transform="${eye.matrix}" opacity="${eye.alpha}" fill="#fff"/>`).join('');
 const body = `<path d="${frame.bodyPath}" fill="#FF4055"/>${eyes}`;
 const svg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="-128 -128 256 256" role="img"><title>Rex / ${name}</title>${body}</svg>`;
 fs.writeFileSync(path.join(output, `${id}.svg`), svg);
 return {id,name,body};
});
assert.equal(new Set(entries.map(x=>x.body)).size, 16);
const labels = {neutre:'Neutral',attentif:'Listening',surpris:'Surprised',excite:'Excited',heureux:'Happy',hilare:'Laughing',colere:'Focused / fierce',triste:'Sad',effraye:'Startled',mefiant:'Skeptical',confus:'Confused',curieux:'Curious',fier:'Proud',timide:'Shy',blase:'Unimpressed',somnolent:'Sleepy'};
function sheet(items, name) {
 const height=240+Math.ceil(items.length/4)*252;
 const cards=items.map((e,i)=>{
  const x=48+(i%4)*288,y=188+Math.floor(i/4)*252;
  return `<rect x="${x}" y="${y}" width="268" height="232" rx="24" fill="#161619" stroke="#29292e"/><g transform="translate(${x+134} ${y+102}) scale(.83)">${e.body}</g><text x="${x+134}" y="${y+209}" text-anchor="middle" fill="#c7c7ce" font-size="17" font-family="Arial,sans-serif">${labels[e.id]}</text>`;
 }).join('');
 fs.writeFileSync(path.join(output,`${name}.svg`),`<svg xmlns="http://www.w3.org/2000/svg" width="1232" height="${height}" viewBox="0 0 1232 ${height}"><rect width="1232" height="${height}" fill="#0c0c0e"/><text x="48" y="76" fill="#fff" font-family="Arial,sans-serif" font-size="43" font-weight="700">Rex. One mascot, more personality.</text><text x="48" y="119" fill="#95959f" font-family="Arial,sans-serif" font-size="20">Your current mascot as the logo. Same red body. Expression through the eyes.</text>${cards}</svg>`);
}
sheet(entries,'expressions');
