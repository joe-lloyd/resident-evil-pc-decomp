// Draws an act's plan as one web page: the puzzle dependency chart, how many
// things she has open as she plays, the map with its locks and shortcuts,
// the beat chart and the storyboard of the cameras built so far.
//
//   node tools/rebecca/plan/page.ts <out dir>
//
// The out dir gets index.html and the camera renders it shows. The page
// refuses to draw a plan that check() finds errors in.
import { copyFileSync, existsSync, mkdirSync, readdirSync, writeFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { act1 } from './act1.ts';
import { check, type Act, type Report, type Step, type StepKind } from './plan.ts';

const DAY = join(dirname(fileURLToPath(import.meta.url)), '..', 'day');

const esc = (s: string) => s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');

/** The dark categorical steps (dataviz reference palette), one per kind; each node also says its kind in words. */
const KIND: Record<StepKind, { colour: string; word: string }> = {
  find: { colour: '#3987e5', word: 'find' },
  do: { colour: '#d95926', word: 'do' },
  learn: { colour: '#199e70', word: 'learn' },
  shortcut: { colour: '#9085e9', word: 'shortcut' },
  goal: { colour: '#e66767', word: 'goal' },
};

function wrap(text: string, width: number): string[] {
  const lines: string[] = [];
  let line = '';
  for (const word of text.split(' ')) {
    if (line && (line + ' ' + word).length > width) {
      lines.push(line);
      line = word;
    } else line = line ? line + ' ' + word : word;
  }
  return line ? [...lines, line] : lines;
}

function chart(act: Act, report: Report): string {
  const W = 190;
  const H = 58;
  const COL = 232;
  const ROW = 74;
  const placeName = new Map(act.places.map((p) => [p.id, p.name]));
  const columns: Step[][] = [];
  for (const s of act.steps) (columns[report.depth.get(s.id)!] ??= []).push(s);
  // Order each column by where its needs sit, so the lines cross less.
  const row = new Map<string, number>();
  columns[0]!.forEach((s, i) => row.set(s.id, i));
  for (let pass = 0; pass < 3; pass++) {
    for (const col of columns.slice(1)) {
      const at = (s: Step) => s.needs.reduce((a, n) => a + (row.get(n) ?? 0), 0) / Math.max(1, s.needs.length);
      col.sort((a, b) => at(a) - at(b));
      col.forEach((s, i) => row.set(s.id, i));
    }
  }
  const tallest = Math.max(...columns.map((c) => c.length));
  const pos = new Map<string, { x: number; y: number }>();
  columns.forEach((col, d) =>
    col.forEach((s, i) => pos.set(s.id, { x: 16 + d * COL, y: 16 + (i + (tallest - col.length) / 2) * ROW })),
  );
  const width = 16 * 2 + (columns.length - 1) * COL + W;
  const height = 16 * 2 + (tallest - 1) * ROW + H;

  const edges = act.steps.flatMap((s) =>
    s.needs.map((n) => {
      const a = pos.get(n)!;
      const b = pos.get(s.id)!;
      const x1 = a.x + W;
      const y1 = a.y + H / 2;
      const x2 = b.x;
      const y2 = b.y + H / 2;
      const mid = (x1 + x2) / 2;
      return `<path class="edge" data-from="${n}" data-to="${s.id}" d="M${x1},${y1} C${mid},${y1} ${mid},${y2} ${x2},${y2}"/>`;
    }),
  );
  const nodes = act.steps.map((s) => {
    const p = pos.get(s.id)!;
    const k = KIND[s.kind];
    const lines = wrap(s.label, 27).slice(0, 2);
    const tip = `${s.label}\nAt: ${placeName.get(s.at)}\n${s.needs.length ? `Needs: ${s.needs.join(', ')}` : 'Open from the start'}\n${s.built === 'built' ? 'Built' : 'Planned'}${s.optional ? ', optional' : ''}`;
    return `<g class="node ${s.built}${s.optional ? ' optional' : ''}" data-id="${s.id}" data-needs="${s.needs.join(' ')}" transform="translate(${p.x},${p.y})">
  <title>${esc(tip)}</title>
  <rect class="box" width="${W}" height="${H}" rx="6"/>
  <rect width="5" height="${H - 12}" x="6" y="6" rx="2" fill="${k.colour}"/>
  <text x="18" y="15" class="meta">${esc(k.word)} · ${esc(placeName.get(s.at)!)}</text>
  ${lines.map((l, i) => `<text x="18" y="${32 + i * 15}" class="label">${esc(l)}</text>`).join('')}
</g>`;
  });
  return `<svg class="chart" viewBox="0 0 ${width} ${height}" width="${width}" height="${height}" role="img" aria-label="Puzzle dependency chart for ${esc(act.title)}">
${edges.join('\n')}
${nodes.join('\n')}
</svg>`;
}

function openStrip(act: Act, report: Report): string {
  const label = new Map(act.steps.map((s) => [s.id, s.label]));
  const BAR = 22;
  const UNIT = 18;
  const max = Math.max(...report.open);
  const h = max * UNIT;
  const left = 28;
  const bars = report.order.map((id, i) => {
    const n = report.open[i]!;
    const x = left + i * (BAR + 2);
    const bh = n * UNIT;
    return `<g class="bar"><title>${esc(`Step ${i + 1}: ${label.get(id)}\n${n} open to her before it`)}</title>
  <rect x="${x - 1}" y="0" width="${BAR + 2}" height="${h + 4}" fill="transparent"/>
  <path d="M${x},${h} V${h - bh + 4} Q${x},${h - bh} ${x + 4},${h - bh} H${x + BAR - 4} Q${x + BAR},${h - bh} ${x + BAR},${h - bh + 4} V${h} Z"/></g>`;
  });
  const ticks = Array.from({ length: max + 1 }, (_, v) =>
    `<line class="grid" x1="${left}" x2="${left + report.order.length * (BAR + 2)}" y1="${h - v * UNIT}" y2="${h - v * UNIT}"/><text class="axis" x="${left - 8}" y="${h - v * UNIT + 4}" text-anchor="end">${v}</text>`,
  );
  const w = left + report.order.length * (BAR + 2) + 4;
  return `<svg class="strip" viewBox="0 -8 ${w} ${h + 30}" width="${w}" height="${h + 30}" role="img" aria-label="Open steps before each step">
${ticks.join('\n')}
${bars.join('\n')}
<text class="axis" x="${left}" y="${h + 18}">step 1</text>
<text class="axis" x="${w - 4}" y="${h + 18}" text-anchor="end">step ${report.order.length}</text>
</svg>`;
}

function map(act: Act): string {
  const U = 100;
  const BW = 128;
  const BH = 42;
  const xs = act.places.map((p) => p.at[0]);
  const ys = act.places.map((p) => p.at[1]);
  const x0 = Math.min(...xs);
  const y0 = Math.min(...ys);
  const centre = new Map(act.places.map((p) => [p.id, { x: 24 + (p.at[0] - x0) * U + BW / 2, y: 24 + (p.at[1] - y0) * U + BH / 2 }]));
  const label = new Map(act.steps.map((s) => [s.id, s.label]));
  const links = act.links.map((l) => {
    const a = centre.get(l.from)!;
    const b = centre.get(l.to)!;
    // Two links between the same places (the ferry over, the bridge back) sit side by side.
    const twin = act.links.some((o) => o !== l && o.from === l.to && o.to === l.from) ? (l.shortcut ? 10 : -10) : 0;
    // Offset along the normal of the pair's sorted direction, so the twins part rather than cancel.
    const [p, q] = l.from < l.to ? [a, b] : [b, a];
    const dx = q.x - p.x;
    const dy = q.y - p.y;
    const len = Math.hypot(dx, dy) || 1;
    const ox = (-dy / len) * twin;
    const oy = (dx / len) * twin;
    const cls = l.shortcut ? 'link shortcut' : l.opens ? 'link locked' : 'link';
    const tip = `${l.kind}${l.opens ? `, opened by: ${label.get(l.opens)}` : ', open'}${l.shortcut ? ' (a shortcut, opened from this side)' : ''}`;
    const mx = (a.x + b.x) / 2 + ox;
    const my = (a.y + b.y) / 2 + oy;
    const tag = l.shortcut ? 'shortcut' : l.kind === 'ferry' ? 'ferry' : l.opens ? 'locked' : '';
    return `<g class="${cls}"><title>${esc(`${l.from} to ${l.to}: ${tip}`)}</title>
  <line x1="${a.x + ox}" y1="${a.y + oy}" x2="${b.x + ox}" y2="${b.y + oy}"/>
  ${tag ? `<text x="${mx + ox * 0.8}" y="${my - 5}" text-anchor="${ox > 0 ? 'start' : ox < 0 ? 'end' : 'middle'}" class="tag">${tag}</text>` : ''}</g>`;
  });
  const boxes = act.places.map((p) => {
    const c = centre.get(p.id)!;
    return `<g class="place ${p.built}"><title>${esc(`${p.name}\n${p.there}`)}</title>
  <rect x="${c.x - BW / 2}" y="${c.y - BH / 2}" width="${BW}" height="${BH}" rx="6"/>
  ${wrap(p.name, 20).map((l, i, all) => `<text x="${c.x}" y="${c.y + 4 + (i - (all.length - 1) / 2) * 14}" text-anchor="middle">${esc(l)}</text>`).join('')}</g>`;
  });
  const w = 48 + (Math.max(...xs) - x0) * U + BW;
  const h = 48 + (Math.max(...ys) - y0) * U + BH;
  return `<svg class="map" viewBox="0 0 ${w} ${h}" width="${w}" height="${h}" role="img" aria-label="Map of ${esc(act.title)}">
${links.join('\n')}
${boxes.join('\n')}
</svg>`;
}

function beats(act: Act): string {
  const rows = act.places.map(
    (p) => `<tr class="${p.built}"><td>${esc(p.name)}</td><td>${p.built}</td><td>${esc(p.there)}</td><td>${esc(p.moves)}</td><td>${esc(p.enemies)}</td><td>${esc(p.story)}</td></tr>`,
  );
  return `<table><thead><tr><th>Place</th><th>State</th><th>What is there</th><th>What moves</th><th>Enemies</th><th>What it tells</th></tr></thead><tbody>${rows.join('')}</tbody></table>`;
}

/** The built rooms' camera renders, copied next to the page. */
function storyboard(act: Act, out: string): string {
  return act.places
    .filter((p) => p.room)
    .map((p) => {
      const dir = join(DAY, p.room!, 'renders');
      const shots = existsSync(dir) ? readdirSync(dir).filter((f) => /^cam\d+\.png$/.test(f)).sort() : [];
      const imgs = shots.map((f) => {
        const name = `${p.room}-${f}`;
        copyFileSync(join(dir, f), join(out, name));
        return `<figure><img src="${name}" width="320" height="240" alt="${esc(`${p.name}, camera ${f.slice(3, -4)}`)}" loading="lazy"><figcaption>camera ${f.slice(3, -4)}</figcaption></figure>`;
      });
      return `<section class="board"><h3>${esc(p.name)}</h3><div class="shots">${imgs.join('') || '<p>No renders yet.</p>'}</div></section>`;
    })
    .join('\n');
}

function page(act: Act, report: Report, out: string): string {
  const steps = act.steps.length;
  const built = act.steps.filter((s) => s.built === 'built').length;
  const widest = Math.max(...report.open);
  return `<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Rebecca's day: planning ${esc(act.title)}</title>
<style>
:root { color-scheme: dark; --bg: #1a1a19; --panel: #232321; --text: #ffffff; --soft: #c3c2b7; --muted: #8d8c84; --line: #4a4945; }
body { margin: 0; background: var(--bg); color: var(--text); font: 15px/1.5 system-ui, sans-serif; }
main { max-width: 1180px; margin: 0 auto; padding: 32px 24px 64px; }
h1 { font-size: 28px; margin: 0 0 4px; } h2 { font-size: 20px; margin: 40px 0 8px; } h3 { font-size: 16px; margin: 20px 0 8px; }
p, li { color: var(--soft); max-width: 78ch; } a { color: #86b6ef; }
.scroll { overflow-x: auto; background: var(--panel); border-radius: 8px; padding: 12px; }
.edge { fill: none; stroke: var(--line); stroke-width: 1.5; }
.edge.lit { stroke: #ffffff; stroke-width: 2; }
.node .box { fill: #2c2c2a; stroke: #6b6a64; stroke-width: 1; }
.node.planned .box { fill: var(--bg); stroke-dasharray: 4 3; }
.node.optional .box { stroke: var(--muted); }
.node.lit .box { stroke: #ffffff; stroke-width: 2; }
.node.dim { opacity: 0.35; }
.node .label { fill: var(--text); font-size: 12.5px; }
.node .meta { fill: var(--muted); font-size: 10.5px; }
.node { cursor: pointer; }
.key { display: flex; flex-wrap: wrap; gap: 6px 18px; margin: 8px 0 12px; color: var(--soft); font-size: 13px; }
.key span::before { content: ''; display: inline-block; width: 5px; height: 14px; border-radius: 2px; margin-right: 6px; vertical-align: -2px; background: var(--c); }
.strip path { fill: #3987e5; } .strip .bar:hover path { fill: #86b6ef; }
.grid { stroke: #33332f; } .axis { fill: var(--muted); font-size: 11px; }
.map .link line { stroke: #8d8c84; stroke-width: 2; }
.map .link.locked line { stroke: #d95926; stroke-dasharray: 6 4; }
.map .link.shortcut line { stroke: #9085e9; stroke-dasharray: 2 4; stroke-width: 3; }
.map .tag { fill: var(--soft); font-size: 10.5px; paint-order: stroke; stroke: var(--panel); stroke-width: 4px; }
.map .place rect { fill: #2c2c2a; stroke: #c3c2b7; }
.map .place.planned rect { fill: var(--bg); stroke: #6b6a64; stroke-dasharray: 4 3; }
.map .place text { fill: var(--text); font-size: 12px; }
table { border-collapse: collapse; width: 100%; font-size: 13px; }
th, td { text-align: left; vertical-align: top; padding: 6px 8px; border-bottom: 1px solid #33332f; }
th { color: var(--muted); font-weight: 600; } td { color: var(--soft); } td:first-child { color: var(--text); white-space: nowrap; }
tr.planned td:first-child { color: var(--soft); font-style: italic; }
.shots { display: flex; flex-wrap: wrap; gap: 10px; }
figure { margin: 0; } figure img { display: block; border-radius: 4px; image-rendering: pixelated; }
figcaption { color: var(--muted); font-size: 12px; margin-top: 2px; }
.methods dt { color: var(--text); font-weight: 600; margin-top: 14px; } .methods dd { margin: 2px 0 0; color: var(--soft); max-width: 78ch; }
</style></head>
<body><main>
<h1>Planning ${esc(act.title)}</h1>
<p>${steps} steps over ${act.places.length} places. ${built} of the steps are built. At its widest she has ${widest} things she could do next.</p>

<h2>How games like this get planned</h2>
<dl class="methods">
<dt>Puzzle dependency chart</dt>
<dd>Every find, action and clue is a box, and each one points at what it needs first. Ron Gilbert drew these for Maniac Mansion and Monkey Island (<a href="https://grumpygamer.com/puzzle_dependency_charts">his write-up</a>). The chart's shape tells you how the game plays. A long thin chart is a corridor. A wide one gives the player several jobs at once, and the points where lines meet are the bottlenecks. This is the tool for branching.</dd>
<dt>Lock and key map</dt>
<dd>The places as boxes and the ways between them as lines, each lock marked with what opens it. It shows the loops and the shortcuts, which the chart can't. Mark Brown's <a href="https://zeldauniverse.net/2017/01/26/explore-zelda-dungeon-design-in-mark-browns-youtube-series-boss-keys/">Boss Keys</a> videos draw Zelda dungeons this way.</dd>
<dt>Beat chart</dt>
<dd>One row per place: what is there, what attacks, what it tells. Read down the column, you can see the pacing, such as three quiet rooms in a row or two fights back to back. Scott Rogers lays one out in <a href="https://oreilly.com/library/view/level-up-the/9781118877197">Level Up!</a> as part of the design document.</dd>
<dt>Storyboard</dt>
<dd>For a fixed-camera game the storyboard is the set of camera shots. A planned room gets cheap block-out shots first, which is what the preview render does, before it is dressed and lit.</dd>
</dl>
<p>All four come from one file, <code>tools/rebecca/plan/act1.ts</code>. A script checks that file before it draws anything. It confirms every step can be reached, that each step's needs really get her to its place, and that every find is used somewhere.</p>

<h2>Puzzle dependency chart</h2>
<p>Read left to right. Each box needs the boxes whose lines come into it. Solid boxes are built and dashed ones are planned. Click a box to light up everything it needs; click it again to clear.</p>
<div class="key">${Object.values(KIND).map((k) => `<span style="--c:${k.colour}">${k.word}</span>`).join('')}</div>
<div class="scroll">${chart(act, report)}</div>

<h2>How many things she can do at once</h2>
<p>Played one step at a time, each bar is how many steps were open to her at that point. A run of ones is a corridor. The middle of the act should be wide, and the end narrows to the ferry.</p>
<div class="scroll">${openStrip(act, report)}</div>

<h2>Map</h2>
<p>Grey lines are open. Orange dashes are locked until a step opens them. Purple dots are shortcuts, opened from the far side. Hover a line for what opens it.</p>
<div class="scroll">${map(act)}</div>

<h2>Beat chart</h2>
${beats(act)}

<h2>Storyboard of the built rooms</h2>
${storyboard(act, out)}
</main>
<script>
const svg = document.querySelector('svg.chart');
const needs = new Map([...svg.querySelectorAll('.node')].map((n) => [n.dataset.id, n.dataset.needs ? n.dataset.needs.split(' ') : []]));
let lit = null;
svg.addEventListener('click', (e) => {
  const node = e.target.closest('.node');
  const id = node && node.dataset.id !== lit ? node.dataset.id : null;
  lit = id;
  const chain = new Set();
  const walk = (s) => { if (chain.has(s)) return; chain.add(s); needs.get(s).forEach(walk); };
  if (id) walk(id);
  svg.querySelectorAll('.node').forEach((n) => {
    n.classList.toggle('lit', !!id && chain.has(n.dataset.id));
    n.classList.toggle('dim', !!id && !chain.has(n.dataset.id));
  });
  svg.querySelectorAll('.edge').forEach((p) => p.classList.toggle('lit', !!id && chain.has(p.dataset.to) && chain.has(p.dataset.from)));
});
</script>
</body></html>
`;
}

const out = process.argv[2];
if (!out) {
  console.error('usage: node tools/rebecca/plan/page.ts <out dir>');
  process.exit(2);
}
const report = check(act1);
for (const w of report.warnings) console.warn(`warning: ${w}`);
if (report.errors.length) {
  for (const e of report.errors) console.error(`error: ${e}`);
  process.exit(1);
}
mkdirSync(out, { recursive: true });
writeFileSync(join(out, 'index.html'), page(act1, report, out));
console.log(`${join(out, 'index.html')}: ${act1.steps.length} steps, open choices ${report.open.join(' ')}`);
