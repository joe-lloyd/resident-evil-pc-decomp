// Draws the day's plan as one web page: for each act its puzzle dependency
// chart, its lock and key map and its beat chart, then how many things she
// has open across the whole day, and the storyboard of the cameras built so
// far.
//
//   node tools/rebecca/plan/page.ts <out dir>
//
// The out dir gets index.html and the camera renders it shows. The page
// refuses to draw a plan that check() finds errors in.
import { copyFileSync, existsSync, mkdirSync, readdirSync, writeFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { day, MANSION } from './day.ts';
import { check, type ActInfo, type Place, type Plan, type Report, type Step, type StepKind } from './plan.ts';

const DAY = join(dirname(fileURLToPath(import.meta.url)), '..', 'day');

const esc = (s: string) => s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');

/** The dark categorical steps (dataviz reference palette), one per kind; each node also says its kind in words. */
const KIND: Record<StepKind, { colour: string; word: string }> = {
  find: { colour: '#3987e5', word: 'find' },
  do: { colour: '#d95926', word: 'do' },
  learn: { colour: '#199e70', word: 'learn' },
  shortcut: { colour: '#9085e9', word: 'shortcut' },
  milestone: { colour: '#c98500', word: 'act ends' },
  goal: { colour: '#e66767', word: 'the end' },
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

/** One act's steps, with the steps they need from earlier acts as faint boxes on the left. */
function chart(plan: Plan, act: ActInfo): string {
  const W = 190;
  const H = 58;
  const COL = 232;
  const ROW = 74;
  const byId = new Map(plan.steps.map((s) => [s.id, s]));
  const placeName = new Map(plan.places.map((p) => [p.id, p.name]));
  const own = plan.steps.filter((s) => s.act === act.n);
  const mine = new Set(own.map((s) => s.id));
  const ghosts = [...new Set(own.flatMap((s) => s.needs.filter((n) => !mine.has(n))))].map((id) => byId.get(id)!);
  const depth = new Map<string, number>(ghosts.map((g) => [g.id, 0]));
  const d = (s: Step): number => {
    if (!depth.has(s.id)) depth.set(s.id, s.needs.reduce((m, n) => Math.max(m, d(byId.get(n)!) + 1), ghosts.length ? 1 : 0));
    return depth.get(s.id)!;
  };
  own.forEach(d);
  const columns: Step[][] = [];
  for (const s of [...ghosts, ...own]) (columns[depth.get(s.id)!] ??= []).push(s);
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
  columns.forEach((col, c) =>
    col.forEach((s, i) => pos.set(s.id, { x: 16 + c * COL, y: 16 + (i + (tallest - col.length) / 2) * ROW })),
  );
  const width = 16 * 2 + (columns.length - 1) * COL + W;
  const height = 16 * 2 + (tallest - 1) * ROW + H;

  const edges = own.flatMap((s) =>
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
  const nodes = [...ghosts, ...own].map((s) => {
    const p = pos.get(s.id)!;
    const k = KIND[s.kind];
    const ghost = !mine.has(s.id);
    const lines = wrap(s.label, 27).slice(0, 2);
    const meta = ghost ? `from act ${s.act}` : `${k.word} · ${placeName.get(s.at)}`;
    const tip = `${s.label}\nAt: ${placeName.get(s.at)}\n${s.needs.length ? `Needs: ${s.needs.join(', ')}` : 'Open from the start'}\n${s.built === 'built' ? 'Built' : 'Planned'}${s.optional ? ', optional' : ''}`;
    const cls = ghost ? 'ghost' : `${s.built}${s.optional ? ' optional' : ''}`;
    return `<g class="node ${cls}" data-id="${s.id}" data-needs="${ghost ? '' : s.needs.join(' ')}" transform="translate(${p.x},${p.y})">
  <title>${esc(tip)}</title>
  <rect class="box" width="${W}" height="${H}" rx="6"/>
  <rect width="5" height="${H - 12}" x="6" y="6" rx="2" fill="${k.colour}"/>
  <text x="18" y="15" class="meta">${esc(meta)}</text>
  ${lines.map((l, i) => `<text x="18" y="${32 + i * 15}" class="label">${esc(l)}</text>`).join('')}
</g>`;
  });
  return `<svg class="chart" viewBox="0 0 ${width} ${height}" width="${width}" height="${height}" role="img" aria-label="Puzzle dependency chart for act ${act.n}">
${edges.join('\n')}
${nodes.join('\n')}
</svg>`;
}

/** One act's places, with the places they join to in other acts drawn faint. */
function map(plan: Plan, act: ActInfo): string {
  const U = 100;
  const BW = 128;
  const BH = 42;
  const label = new Map(plan.steps.map((s) => [s.id, s.label]));
  const own = new Set(plan.places.filter((p) => p.act === act.n).map((p) => p.id));
  const links = plan.links.filter((l) => own.has(l.from) || own.has(l.to));
  const shown = plan.places.filter((p) => own.has(p.id) || links.some((l) => l.from === p.id || l.to === p.id));
  const x0 = Math.min(...shown.map((p) => p.at[0]));
  const y0 = Math.min(...shown.map((p) => p.at[1]));
  const centre = new Map(shown.map((p) => [p.id, { x: 24 + (p.at[0] - x0) * U + BW / 2, y: 24 + (p.at[1] - y0) * U + BH / 2 }]));
  const lines = links.map((l) => {
    const a = centre.get(l.from)!;
    const b = centre.get(l.to)!;
    // Two links between the same places sit side by side, parted along the
    // normal of the pair's sorted direction so they don't cancel.
    const twin = plan.links.some((o) => o !== l && o.from === l.to && o.to === l.from) ? (l.shortcut ? 10 : -10) : 0;
    const [p, q] = l.from < l.to ? [a, b] : [b, a];
    const len = Math.hypot(q.x - p.x, q.y - p.y) || 1;
    const ox = (-(q.y - p.y) / len) * twin;
    const oy = ((q.x - p.x) / len) * twin;
    const cls = l.shortcut ? 'link shortcut' : l.opens ? 'link locked' : 'link';
    const tip = `${l.kind}${l.opens ? `, opened by: ${label.get(l.opens)}` : ', open'}${l.shortcut ? ' (a shortcut, opened from this side)' : ''}`;
    const tag = l.shortcut ? 'shortcut' : l.kind === 'ride' || l.kind === 'lift' ? l.kind : l.opens ? 'locked' : '';
    const mx = (a.x + b.x) / 2 + ox * 0.8;
    const my = (a.y + b.y) / 2 + oy;
    return `<g class="${cls}"><title>${esc(`${l.from} to ${l.to}: ${tip}`)}</title>
  <line x1="${a.x + ox}" y1="${a.y + oy}" x2="${b.x + ox}" y2="${b.y + oy}"/>
  ${tag ? `<text x="${mx}" y="${my - 5}" text-anchor="${ox > 0 ? 'start' : ox < 0 ? 'end' : 'middle'}" class="tag">${tag}</text>` : ''}</g>`;
  });
  const boxes = shown.map((p) => {
    const c = centre.get(p.id)!;
    const cls = own.has(p.id) ? p.built : 'ghost';
    return `<g class="place ${cls}"><title>${esc(`${p.name}${own.has(p.id) ? '' : ` (act ${p.act})`}\n${p.there}\n${p.cameras} cameras`)}</title>
  <rect x="${c.x - BW / 2}" y="${c.y - BH / 2}" width="${BW}" height="${BH}" rx="6"/>
  ${wrap(p.name, 20).map((l, i, all) => `<text x="${c.x}" y="${c.y + 4 + (i - (all.length - 1) / 2) * 14}" text-anchor="middle">${esc(l)}</text>`).join('')}</g>`;
  });
  const w = 48 + (Math.max(...shown.map((p) => p.at[0])) - x0) * U + BW;
  const h = 48 + (Math.max(...shown.map((p) => p.at[1])) - y0) * U + BH;
  return `<svg class="map" viewBox="0 0 ${w} ${h}" width="${w}" height="${h}" role="img" aria-label="Map of act ${act.n}">
${lines.join('\n')}
${boxes.join('\n')}
</svg>`;
}

function beats(places: readonly Place[]): string {
  const state = (p: Place) => (p.existing ? `existing (${p.existing})` : p.built);
  const rows = places.map(
    (p) => `<tr class="${p.built}"><td>${esc(p.name)}</td><td>${esc(state(p))}</td><td class="n">${p.cameras}</td><td>${esc(p.there)}</td><td>${esc(p.moves)}</td><td>${esc(p.enemies)}</td><td>${esc(p.story)}</td></tr>`,
  );
  return `<table><thead><tr><th>Place</th><th>State</th><th class="n">Cameras</th><th>What is there</th><th>What moves</th><th>Enemies</th><th>What it tells</th></tr></thead><tbody>${rows.join('')}</tbody></table>`;
}

/** Bars of how many steps were open before each step, with the acts marked. */
function openStrip(plan: Plan, report: Report): string {
  const byId = new Map(plan.steps.map((s) => [s.id, s]));
  const BAR = 14;
  const GAP = 2;
  const UNIT = 14;
  const max = Math.max(...report.open);
  const h = max * UNIT;
  const left = 28;
  const x = (i: number) => left + i * (BAR + GAP);
  const bars = report.order.map((id, i) => {
    const n = report.open[i]!;
    const bh = n * UNIT;
    return `<g class="bar"><title>${esc(`Step ${i + 1}, act ${byId.get(id)!.act}: ${byId.get(id)!.label}\n${n} open to her before it`)}</title>
  <rect x="${x(i) - 1}" y="0" width="${BAR + GAP}" height="${h + 4}" fill="transparent"/>
  <path d="M${x(i)},${h} V${h - bh + 3} Q${x(i)},${h - bh} ${x(i) + 3},${h - bh} H${x(i) + BAR - 3} Q${x(i) + BAR},${h - bh} ${x(i) + BAR},${h - bh + 3} V${h} Z"/></g>`;
  });
  const marks = report.order.flatMap((id, i) => {
    const act = byId.get(id)!.act;
    if (i > 0 && byId.get(report.order[i - 1]!)!.act === act) return [];
    return [`<line class="act" x1="${x(i) - 1}" x2="${x(i) - 1}" y1="-8" y2="${h}"/><text class="axis" x="${x(i) + 2}" y="-12">act ${act}</text>`];
  });
  const ticks = Array.from({ length: max + 1 }, (_, v) => v).filter((v) => v % 2 === 0).map(
    (v) => `<line class="grid" x1="${left}" x2="${x(report.order.length)}" y1="${h - v * UNIT}" y2="${h - v * UNIT}"/><text class="axis" x="${left - 8}" y="${h - v * UNIT + 4}" text-anchor="end">${v}</text>`,
  );
  const w = x(report.order.length) + 4;
  return `<svg class="strip" viewBox="0 -26 ${w} ${h + 48}" width="${w}" height="${h + 48}" role="img" aria-label="Open steps before each step of the day">
${ticks.join('\n')}
${marks.join('\n')}
${bars.join('\n')}
<text class="axis" x="${left}" y="${h + 16}">first step</text>
<text class="axis" x="${w - 4}" y="${h + 16}" text-anchor="end">step ${report.order.length}</text>
</svg>`;
}

/** The built rooms' camera renders, copied next to the page. */
function storyboard(plan: Plan, out: string): string {
  return plan.places
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

const sum = (xs: readonly number[]) => xs.reduce((a, b) => a + b, 0);

function overview(plan: Plan, report: Report): string {
  const byId = new Map(plan.steps.map((s) => [s.id, s]));
  const rows = plan.acts.map((a) => {
    const places = plan.places.filter((p) => p.act === a.n);
    const builtRooms = places.filter((p) => p.built === 'built').length;
    const widest = Math.max(0, ...report.order.map((id, i) => (byId.get(id)!.act === a.n ? report.open[i]! : 0)));
    return `<tr><td><a href="#act${a.n}">Act ${a.n}: ${esc(a.title)}</a></td><td>${esc(a.time)}</td><td class="n">${places.length}</td><td class="n">${builtRooms}</td><td class="n">${sum(places.map((p) => p.cameras))}</td><td class="n">${plan.steps.filter((s) => s.act === a.n).length}</td><td class="n">${widest}</td></tr>`;
  });
  const total = `<tr class="total"><td>The day</td><td></td><td class="n">${plan.places.length}</td><td class="n">${plan.places.filter((p) => p.built === 'built').length}</td><td class="n">${sum(plan.places.map((p) => p.cameras))}</td><td class="n">${plan.steps.length}</td><td class="n">${Math.max(...report.open)}</td></tr>`;
  const mansion = `<tr class="mansion"><td>The mansion, for scale</td><td></td><td class="n">${MANSION.rooms}</td><td></td><td class="n">${MANSION.cameras}</td><td></td><td></td></tr>`;
  return `<table class="overview"><thead><tr><th>Act</th><th>Time</th><th class="n">Rooms</th><th class="n">Built</th><th class="n">Cameras</th><th class="n">Steps</th><th class="n">Most open at once</th></tr></thead><tbody>${rows.join('')}${total}${mansion}</tbody></table>`;
}

function page(plan: Plan, report: Report, out: string): string {
  const cameras = sum(plan.places.map((p) => p.cameras));
  const builtCameras = sum(plan.places.filter((p) => p.built === 'built').map((p) => p.cameras));
  const acts = plan.acts.map((a) => {
    const places = plan.places.filter((p) => p.act === a.n);
    return `<section id="act${a.n}">
<h2>Act ${a.n}: ${esc(a.title)} <span class="time">${esc(a.time)}</span></h2>
<p>${esc(a.summary)}</p>
<h3>Puzzle dependency chart</h3>
<div class="scroll">${chart(plan, a)}</div>
<h3>Map</h3>
<div class="scroll">${map(plan, a)}</div>
<h3>Beat chart</h3>
${beats(places)}
</section>`;
  });
  return `<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Planning Rebecca's day</title>
<style>
:root { color-scheme: dark; --bg: #1a1a19; --panel: #232321; --text: #ffffff; --soft: #c3c2b7; --muted: #8d8c84; --line: #4a4945; }
body { margin: 0; background: var(--bg); color: var(--text); font: 15px/1.5 system-ui, sans-serif; }
main { max-width: 1180px; margin: 0 auto; padding: 32px 24px 64px; }
h1 { font-size: 28px; margin: 0 0 4px; } h2 { font-size: 22px; margin: 56px 0 8px; } h3 { font-size: 16px; margin: 24px 0 8px; }
h2 .time { color: var(--muted); font-size: 15px; font-weight: 400; margin-left: 8px; }
p, li { color: var(--soft); max-width: 78ch; } a { color: #86b6ef; }
.scroll { overflow-x: auto; background: var(--panel); border-radius: 8px; padding: 12px; }
.edge { fill: none; stroke: var(--line); stroke-width: 1.5; }
.edge.lit { stroke: #ffffff; stroke-width: 2; }
.node .box { fill: #2c2c2a; stroke: #6b6a64; stroke-width: 1; }
.node.planned .box { fill: var(--bg); stroke-dasharray: 4 3; }
.node.optional .box { stroke: var(--muted); }
.node.ghost { opacity: 0.45; }
.node.lit .box { stroke: #ffffff; stroke-width: 2; }
.node.dim { opacity: 0.3; }
.node .label { fill: var(--text); font-size: 12.5px; }
.node .meta { fill: var(--muted); font-size: 10.5px; }
.node { cursor: pointer; }
.key { display: flex; flex-wrap: wrap; gap: 6px 18px; margin: 8px 0 12px; color: var(--soft); font-size: 13px; }
.key span::before { content: ''; display: inline-block; width: 5px; height: 14px; border-radius: 2px; margin-right: 6px; vertical-align: -2px; background: var(--c); }
.strip path { fill: #3987e5; } .strip .bar:hover path { fill: #86b6ef; }
.strip .act { stroke: var(--muted); stroke-dasharray: 2 3; }
.grid { stroke: #33332f; } .axis { fill: var(--muted); font-size: 11px; }
.map .link line { stroke: #8d8c84; stroke-width: 2; }
.map .link.locked line { stroke: #d95926; stroke-dasharray: 6 4; }
.map .link.shortcut line { stroke: #9085e9; stroke-dasharray: 2 4; stroke-width: 3; }
.map .tag { fill: var(--soft); font-size: 10.5px; paint-order: stroke; stroke: var(--panel); stroke-width: 4px; }
.map .place rect { fill: #2c2c2a; stroke: #c3c2b7; }
.map .place.planned rect { fill: var(--bg); stroke: #6b6a64; stroke-dasharray: 4 3; }
.map .place.ghost { opacity: 0.6; }
.map .place text { fill: var(--text); font-size: 12px; }
table { border-collapse: collapse; width: 100%; font-size: 13px; }
th, td { text-align: left; vertical-align: top; padding: 6px 8px; border-bottom: 1px solid #33332f; }
th { color: var(--muted); font-weight: 600; } td { color: var(--soft); } td:first-child { color: var(--text); white-space: nowrap; }
.n { text-align: right; font-variant-numeric: tabular-nums; }
tr.planned td:first-child { color: var(--soft); font-style: italic; }
.overview tr.total td { color: var(--text); font-weight: 600; border-top: 1px solid var(--line); }
.overview tr.mansion td { color: var(--muted); }
.shots { display: flex; flex-wrap: wrap; gap: 10px; }
figure { margin: 0; } figure img { display: block; border-radius: 4px; image-rendering: pixelated; }
figcaption { color: var(--muted); font-size: 12px; margin-top: 2px; }
.methods dt { color: var(--text); font-weight: 600; margin-top: 14px; } .methods dd { margin: 2px 0 0; color: var(--soft); max-width: 78ch; }
</style></head>
<body><main>
<h1>Planning Rebecca's day</h1>
<p>${plan.places.length} rooms, the same as the mansion's ${MANSION.rooms}. About ${cameras} camera angles; the mansion has ${MANSION.cameras}. Built so far: ${plan.places.filter((p) => p.built === 'built').length} rooms and ${builtCameras} cameras. The station yard is the hub for most of the game. From it she goes out in three directions for what the gondola needs, and the gondola takes her down the mountain to the mansion.</p>
${overview(plan, report)}

<h2>How to read this</h2>
<dl class="methods">
<dt>Puzzle dependency chart</dt>
<dd>Every find, action and clue is a box, and lines come in from the boxes it needs first. Read it left to right. Ron Gilbert drew these for Maniac Mansion and Monkey Island (<a href="https://grumpygamer.com/puzzle_dependency_charts">his write-up</a>). A long thin chart is a corridor, and a wide one gives her several jobs at once. Solid boxes are built and dashed ones are planned. Faint boxes on the left come from an earlier act. Click a box to light up everything it needs, and click it again to clear.</dd>
<dt>Lock and key map</dt>
<dd>The rooms and the ways between them. Grey lines are open, orange dashes are locked until a step opens them, and purple dots are shortcuts, opened from the far side. Faint rooms belong to another act. Hover a line to see what opens it. Mark Brown's <a href="https://zeldauniverse.net/2017/01/26/explore-zelda-dungeon-design-in-mark-browns-youtube-series-boss-keys/">Boss Keys</a> videos draw Zelda dungeons this way.</dd>
<dt>Beat chart</dt>
<dd>One row per room: what is there, what moves, what attacks and what it tells. Read down a column to see the pacing. Scott Rogers lays one out in <a href="https://oreilly.com/library/view/level-up-the/9781118877197">Level Up!</a>.</dd>
<dt>Storyboard</dt>
<dd>For a fixed-camera game the storyboard is the set of camera shots. The built rooms' shots are at the bottom. A planned room gets quick preview renders first, before it is dressed and lit.</dd>
</dl>
<div class="key">${Object.values(KIND).map((k) => `<span style="--c:${k.colour}">${k.word}</span>`).join('')}</div>
<p>Everything here comes from <code>tools/rebecca/plan/day.ts</code>. A script checks that file before drawing it. It confirms every step can be reached, that each step's needs really get her to its room, and that every find is used somewhere.</p>

<h2>How many things she can do at once</h2>
<p>Played one step at a time, each bar is how many steps were open to her at that point. A run of ones is a corridor. Act 2 should be wide and the ending can narrow.</p>
<div class="scroll">${openStrip(plan, report)}</div>

${acts.join('\n')}

<h2>Storyboard of the built rooms</h2>
${storyboard(plan, out)}
</main>
<script>
for (const svg of document.querySelectorAll('svg.chart')) {
  const needs = new Map([...svg.querySelectorAll('.node')].map((n) => [n.dataset.id, n.dataset.needs ? n.dataset.needs.split(' ') : []]));
  let lit = null;
  svg.addEventListener('click', (e) => {
    const node = e.target.closest('.node');
    const id = node && node.dataset.id !== lit ? node.dataset.id : null;
    lit = id;
    const chain = new Set();
    const walk = (s) => { if (chain.has(s)) return; chain.add(s); (needs.get(s) || []).forEach(walk); };
    if (id) walk(id);
    svg.querySelectorAll('.node').forEach((n) => {
      n.classList.toggle('lit', !!id && chain.has(n.dataset.id));
      n.classList.toggle('dim', !!id && !chain.has(n.dataset.id));
    });
    svg.querySelectorAll('.edge').forEach((p) => p.classList.toggle('lit', !!id && chain.has(p.dataset.to) && chain.has(p.dataset.from)));
  });
}
</script>
</body></html>
`;
}

const out = process.argv[2];
if (!out) {
  console.error('usage: node tools/rebecca/plan/page.ts <out dir>');
  process.exit(2);
}
const report = check(day);
for (const w of report.warnings) console.warn(`warning: ${w}`);
if (report.errors.length) {
  for (const e of report.errors) console.error(`error: ${e}`);
  process.exit(1);
}
mkdirSync(out, { recursive: true });
writeFileSync(join(out, 'index.html'), page(day, report, out));
console.log(`${join(out, 'index.html')}: ${day.places.length} rooms, ${day.steps.length} steps, open choices ${report.open.join(' ')}`);
