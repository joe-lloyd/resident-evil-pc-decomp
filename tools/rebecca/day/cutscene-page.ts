// A page of the cutscenes as tests/cutscenes.ts saw them in the game: each
// scene's pictures in order, each line's picture captioned with the line.
//
//   node tools/rebecca/day/cutscene-page.ts <pictures dir> <outdir>
//
// <pictures dir> is the test's --out folder, which holds <scene id>/*.png.
import { copyFileSync, existsSync, mkdirSync, readdirSync, readFileSync, writeFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { CUT_FLAGS, CUTSCENES } from './cutscenes.ts';
import { CUTSCENES as ROWS } from '../plan/todo.ts';

const here = path.dirname(fileURLToPath(import.meta.url));
const [pictures, out] = process.argv.slice(2);
if (!pictures || !out) throw new Error('usage: cutscene-page.ts <pictures dir> <outdir>');
mkdirSync(path.join(out, 'img'), { recursive: true });

const esc = (t: string) => t.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/"/g, '&quot;');
const title = new Map(ROWS);

/** A room's messages as plain text, by index: page and line breaks become spaces, \o an opening quote. */
function messages(room: string): Map<number, string> {
  const file = room === 'save' ? path.join(here, '..', 'rooms', 'ROOM1000.msg.txt') : path.join(here, room, 'room.msg.txt');
  const text = new Map<number, string>();
  for (const l of readFileSync(file, 'utf8').split('\n')) {
    const m = /^(\d+): (.*)$/.exec(l);
    if (m) text.set(Number(m[1]), m[2]!.replace(/\\p\{0\}|\\n/g, ' ').replace(/\\s\{\d+\}/g, '').replace(/\\o/g, '"').trim());
  }
  return text;
}

function caption(name: string, lines: Map<number, string>): string {
  const what = /-\d\d-(.*)\.png$/.exec(name)?.[1] ?? name;
  if (what === 'before') return 'Before it starts.';
  if (what === 'after') return 'After: the bars gone, her controls back.';
  const cam = /^cam(\d+)$/.exec(what);
  if (cam) return `Camera ${cam[1]}.`;
  const line = /^line(\d+)$/.exec(what);
  if (line) return lines.get(Number(line[1]) - 128) ?? `Message ${line[1]}.`;
  return what;
}

const sections: string[] = [];
let count = 0;
for (const c of CUTSCENES) {
  const dir = path.join(pictures, c.id);
  if (!existsSync(dir)) continue;
  const lines = messages(c.room);
  const figs = readdirSync(dir)
    .filter((f) => f.endsWith('.png'))
    .sort()
    .map((f) => {
      copyFileSync(path.join(dir, f), path.join(out, 'img', f));
      count++;
      const text = caption(f, lines);
      return `<figure><img src="img/${f}" width="640" height="480" loading="lazy" alt="${esc(text)}"><figcaption>${esc(text)}</figcaption></figure>`;
    });
  sections.push(`<h2>${esc(title.get(c.id) ?? c.id)}</h2><p class="id">${c.id}, in ${c.room}, FG_COMMON ${CUT_FLAGS.get(c.id)}</p><div class="grid">${figs.join('')}</div>`);
}

writeFileSync(
  path.join(out, 'index.html'),
  `<!doctype html>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Rebecca's day: cutscenes</title>
<style>
body{background:#121110;color:#ddd6c8;font:15px/1.5 system-ui,sans-serif;max-width:1340px;margin:2em auto;padding:0 1em}
h1{font-weight:600}h2{margin:1.6em 0 .2em;font-size:1.15em}p{max-width:48em}.id{color:#8b8478;margin:0 0 .6em}
.grid{display:flex;flex-wrap:wrap;gap:1em}figure{margin:0;max-width:420px}img{width:100%;height:auto;image-rendering:pixelated;background:#000}
figcaption{color:#8b8478;font-size:.9em}
</style>
<h1>Rebecca's day: cutscenes</h1>
<p>Each scene as tools/harness/tests/cutscenes.ts played it in the game: a picture at each camera cut and each line, then one after it ends, with her controls back. docs/REBECCA_CUTSCENES.md says how a scene is made.</p>
${sections.join('\n')}
`,
);
console.log(`${sections.length} scenes, ${count} pictures in ${out}`);
