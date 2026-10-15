// Check the Strudel sketches without a browser: evaluate each with Strudel's
// own engine, query the first eight cycles, and fail if one doesn't parse,
// plays nothing, or uses a sound that isn't CC0 (VCSL) or a built-in synth.
// Strudel isn't a dependency of this repository, so install it in a scratch
// folder first. 1.2.5 is the last release that loads in Node; 1.2.6 imports a
// browser-only bundle.
//
//   (cd /tmp/strudel && pnpm add --ignore-scripts @strudel/core@1.2.5 @strudel/mini@1.2.5 @strudel/tonal@1.2.5 @strudel/transpiler@1.2.5)
//   node tools/rebecca/music/check.ts /tmp/strudel tools/rebecca/music/sketches/*.js
import { readFileSync } from 'node:fs';
import { createRequire } from 'node:module';
import path from 'node:path';
import { pathToFileURL } from 'node:url';

const [dir, ...files] = process.argv.slice(2);
if (!dir || files.length === 0) {
  console.error('usage: node check.ts <folder with @strudel installed> <sketch.js>...');
  process.exit(2);
}
const from = createRequire(path.join(path.resolve(dir), 'package.json'));
const load = (name: string) => import(pathToFileURL(from.resolve(name)).href);
const [core, mini, tonal, { transpiler }] = await Promise.all(['@strudel/core', '@strudel/mini', '@strudel/tonal', '@strudel/transpiler'].map(load));
await core.evalScope(core, mini, tonal);

const SYNTHS = new Set(['sawtooth', 'sine', 'square', 'triangle', 'brown', 'pink', 'white']);
let sampleMap = '';
let cpm = 0;
Object.assign(globalThis, {
  samples: (url: string) => { sampleMap = url; },
  setcpm: (x: number) => { cpm = x; },
});

let failed = false;
for (const file of files) {
  sampleMap = '';
  cpm = 0;
  const problems: string[] = [];
  try {
    const { pattern } = await core.evaluate(readFileSync(file, 'utf8'), transpiler);
    if (!sampleMap.includes('/vcsl.json')) problems.push('loads no pinned VCSL sample map');
    const known = sampleMap ? new Set(Object.keys((await (await fetch(sampleMap)).json()) as object)) : new Set<string>();
    const haps: { value: { s?: string } }[] = pattern.queryArc(0, 8);
    if (haps.length === 0) problems.push('plays nothing in eight cycles');
    const sounds = [...new Set(haps.map((h) => h.value.s ?? '(none)'))];
    for (const s of sounds) if (!SYNTHS.has(s) && !known.has(s)) problems.push(`sound ${s} is not CC0 or a synth`);
    console.log(`${problems.length ? 'FAIL' : 'ok  '} ${file}: ${haps.length} events in ${((8 * 60) / cpm).toFixed(0)} s, ${sounds.join(', ')}`);
  } catch (e) {
    problems.push(`does not evaluate: ${(e as Error).message}`);
  }
  for (const p of problems) console.log(`     ${p}`);
  failed ||= problems.length > 0;
}
process.exit(failed ? 1 : 0);
