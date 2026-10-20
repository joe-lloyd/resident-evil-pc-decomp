// A page of every kit room as the game shows it: each camera's background
// through the look filter (look.ts), and each state a puzzle leaves it in,
// in the plan's order. For judging the look across the whole day at once.
//
//   node tools/rebecca/day/look-page.ts <outdir>
import { existsSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { readPng, writePng } from '../../harness/image.ts';
import { look } from './look.ts';
import { dayRooms } from './rooms.ts';
import { day } from '../plan/day.ts';

const here = path.dirname(fileURLToPath(import.meta.url));
const out = process.argv[2];
if (!out) throw new Error('usage: look-page.ts <outdir>');
mkdirSync(path.join(out, 'img'), { recursive: true });

const esc = (t: string) => t.replace(/&/g, '&amp;').replace(/</g, '&lt;');
const placeName = new Map(day.places.map((p) => [p.room ?? p.id, p.name]));
const sections: string[] = [];
let pictures = 0;
for (const r of dayRooms) {
  const renders = path.join(here, r.slug, 'renders');
  const json = path.join(renders, 'room.json');
  if (!existsSync(json)) continue;
  const rec: { cameras: unknown[]; notes?: string[]; states?: { name: string }[] } = JSON.parse(readFileSync(json, 'utf8'));
  const figs: string[] = [];
  rec.cameras.forEach((_, i) => {
    const note = rec.notes?.[i];
    for (const suffix of ['', ...(rec.states ?? []).map((s) => `.s-${s.name}`)]) {
      const src = path.join(renders, `cam${i}${suffix}.png`);
      if (!existsSync(src)) continue;
      const name = `${r.slug}-cam${i}${suffix}.png`;
      writePng(path.join(out, 'img', name), look(readPng(src)));
      pictures++;
      const caption = suffix ? `camera ${i}, after ${suffix.slice(3)}` : `camera ${i}${note ? `: ${note}` : ''}`;
      figs.push(`<figure><img src="img/${name}" width="320" height="240" loading="lazy" alt=""><figcaption>${esc(caption)}</figcaption></figure>`);
    }
  });
  sections.push(`<section id="${r.slug}"><h2>${esc(placeName.get(r.slug) ?? r.slug)} <small>${r.slug}, ${'hour' in r ? r.hour : 'custom light'}${'inside' in r && r.inside ? ', inside' : ''}</small></h2><div class="grid">${figs.join('')}</div></section>`);
}

const html = `<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>Rebecca's day: every room with the look</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<script src="/research/rebecca-day/nav.js" defer></script>
<style>
:root{--bg:#121110;--fg:#ddd6c8;--dim:#8b8478;--line:#2a2724}
body{background:var(--bg);color:var(--fg);font:15px/1.45 system-ui,sans-serif;max-width:1400px;margin:2em auto;padding:0 1em}
h1{font-size:1.5em}h2{font-size:1.1em;border-top:1px solid var(--line);padding-top:1em;margin-top:2em}h2 small{color:var(--dim);font-weight:normal}
.grid{display:flex;flex-wrap:wrap;gap:12px}figure{margin:0;width:320px}
img{image-rendering:pixelated;display:block;background:#000}figcaption{color:var(--dim);font-size:.85em;margin-top:.3em}
p{max-width:70ch}
</style></head><body>
<h1>Rebecca's day: every room with the look</h1>
<p>Each camera's background as the game shows it: rendered with the kit's worn, bitty surfaces, ragged trees and interior fill, then through the build's look filter (tone and the game's colour, no grain). Rooms a puzzle changes show that state too. ${sections.length} rooms, ${pictures} pictures, in the plan's order.</p>
${sections.join('\n')}
</body></html>
`;
writeFileSync(path.join(out, 'index.html'), html);
console.log(`${sections.length} rooms, ${pictures} pictures into ${out}`);
