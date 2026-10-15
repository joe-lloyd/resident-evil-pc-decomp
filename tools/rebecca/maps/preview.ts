// Draw every map of her day as the map screen would show it, to look at
// before building: for each area, the map owned with nothing visited, and
// owned with half its rooms visited and her in the last of them.
//
//   node tools/rebecca/maps/preview.ts <outdir>
//
// Writes <area>-owned.png, <area>-visited.png and index.html, and prints any
// rooms the layout could not keep apart.
import { mkdirSync, writeFileSync } from 'node:fs';
import path from 'node:path';
import { writePng } from '../../harness/image.ts';
import { AREAS } from '../plan/maps.ts';
import { areaTim, drawArea, preview } from './draw.ts';
import { browserPreview, overview } from './overview.ts';
import { STAGES } from '../plan/maps.ts';

const out = process.argv[2];
if (!out) throw new Error('usage: preview.ts <outdir>');
mkdirSync(out, { recursive: true });
const rows: string[] = [];
for (const a of AREAS) {
  const d = drawArea(a.id);
  const t = areaTim(a.id);
  const n = a.places.length;
  const seen = new Set(Array.from({ length: Math.ceil(n / 2) }, (_, k) => k));
  writePng(path.join(out, `${a.id}-owned.png`), preview(t, n, { owned: true, visited: new Set() }));
  writePng(path.join(out, `${a.id}-visited.png`), preview(t, n, { owned: true, visited: seen, here: seen.size - 1 }));
  writePng(path.join(out, `${a.id}-unowned.png`), preview(t, n, { owned: false, visited: seen, here: seen.size - 1 }));
  if (d.plan.overlaps.length) console.log(`${a.id}: ${d.plan.overlaps.join('; ')}`);
  rows.push(`<h2>${a.name} <small>${n} rooms, ${d.scale.toFixed(1)} px/m</small></h2><p>${['owned', 'visited', 'unowned'].map((s) => `<img src="${a.id}-${s}.png">`).join(' ')}</p>`);
}
const o = overview();
const shots: string[] = [];
STAGES.forEach((st, upTo) => {
  const area = AREAS.findIndex((a) => a.id === st.areas[0]);
  writePng(path.join(out, `overview-${upTo}.png`), browserPreview(o, upTo, upTo, area));
  shots.push(`<img src="overview-${upTo}.png" title="${st.name}">`);
});
rows.unshift(`<h2>The overview, stage by stage</h2><p>${shots.join(' ')}</p>`);
writeFileSync(
  path.join(out, 'index.html'),
  `<!doctype html><meta charset="utf-8"><title>Her maps</title><style>body{background:#111;color:#ddd;font:15px system-ui}img{image-rendering:pixelated;margin-right:8px}</style>${rows.join('\n')}`,
);
console.log(`${AREAS.length} maps drawn to ${out}`);
