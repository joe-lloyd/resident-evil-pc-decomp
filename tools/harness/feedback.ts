// Playthrough notes: pull from the lab, make a review page, or restore a mark.
// Node 24, built-ins only. See docs/FEEDBACK.md.
import { existsSync, mkdirSync, readFileSync, readdirSync, writeFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { take, restore, type Checkpoint } from './checkpoint.ts';
import { parseReply, roomLabel, type GameState } from './state.ts';
import { encodePng } from './image.ts';
import { loadShapes, type Shape } from './room-map.ts';
import { slugAt } from './world.ts';

const kinds = ['clipping', 'drawn-over', 'item', 'enemy', 'text', 'other'] as const;
type Kind = typeof kinds[number];
interface Point { agoMs: number; stage: number; room: number; cam: number; x: number; y: number; z: number; angle: number }
export interface Feedback {
  kind: Kind;
  text: string;
  time: string;
  mode: string;
  build: { version: string; compiled: string };
  state: GameState;
  path: Point[];
}

function record(v: unknown): v is Record<string, unknown> {
  return typeof v === 'object' && v !== null && !Array.isArray(v);
}
function number(o: Record<string, unknown>, key: string): number {
  const n = o[key];
  if (typeof n !== 'number' || !Number.isSafeInteger(n)) throw new Error(`feedback: invalid ${key}`);
  return n;
}
function text(o: Record<string, unknown>, key: string): string {
  const v = o[key];
  if (typeof v !== 'string') throw new Error(`feedback: invalid ${key}`);
  return v;
}
function isKind(k: unknown): k is Kind { return kinds.some((kind) => kind === k); }

/** Accept an entry folder or its note.json. The state uses the test-link parser. */
export function readFeedback(entry: string): Feedback {
  const file = entry.endsWith('.json') ? entry : path.join(entry, 'note.json');
  const o: unknown = JSON.parse(readFileSync(file, 'utf8'));
  if (!record(o) || o.version !== 1 || !isKind(o.kind) || !record(o.build) || !Array.isArray(o.path)) {
    throw new Error('feedback: expected a version 1 note');
  }
  const reply = parseReply(JSON.stringify(o.state));
  if (reply.t !== 'state') throw new Error('feedback: expected a state');
  for (const bank of [1, 2, 3, 7]) {
    const bytes = reply.state.banks[bank];
    if (!bytes?.length || bytes.length % 4) throw new Error(`feedback: missing checkpoint bank ${bank}`);
  }
  return {
    kind: o.kind, text: text(o, 'text'), time: text(o, 'time'), mode: text(o, 'mode'),
    build: { version: text(o.build, 'version'), compiled: text(o.build, 'compiled') },
    state: reply.state,
    path: o.path.map((p: unknown) => {
      if (!record(p)) throw new Error('feedback: invalid path point');
      return { agoMs: number(p, 'agoMs'), stage: number(p, 'stage'), room: number(p, 'room'), cam: number(p, 'cam'),
        x: number(p, 'x'), y: number(p, 'y'), z: number(p, 'z'), angle: number(p, 'angle') };
    }),
  };
}

/** Same four banks, slot order, weapon and spot as a playthrough checkpoint. */
export function feedbackCheckpoint(note: Feedback): Checkpoint { return take(note.state, []); }

/** Map the engine's character ids, including Rebecca at 3, to DevBoot names. */
export function feedbackBoot(note: Feedback): string {
  let character: string;
  switch (note.state.player.id & 3) {
    case 0: character = 'chris'; break;
    case 1: character = 'jill'; break;
    case 3: character = 'rebecca'; break;
    default: throw new Error('feedback: unsupported character');
  }
  if (!['OG', 'DC', 'SATURN', 'DS', 'REB'].includes(note.mode)) throw new Error('feedback: unsupported mode');
  return `--mode ${note.mode} --boot ${character}`;
}

function screenshot(entry: string): string {
  const png = path.join(entry, 'shot.png');
  if (existsSync(png)) return readFileSync(png).toString('base64');
  const raw = readFileSync(path.join(entry, 'shot.rgba'));
  const end = raw.indexOf(10);
  const m = /^RE1CAP ([0-9]+) ([0-9]+)$/.exec(raw.subarray(0, end).toString('ascii'));
  if (!m) throw new Error(`bad capture header in ${entry}`);
  const width = Number(m[1]), height = Number(m[2]);
  if (width < 1 || height < 1 || width * height > 16_777_216 || raw.length !== end + 1 + width * height * 4) {
    throw new Error(`bad capture dimensions in ${entry}`);
  }
  const rgb = new Uint8Array(width * height * 3);
  for (let i = 0; i < width * height; i++) rgb.set(raw.subarray(end + 1 + i * 4, end + 4 + i * 4), i * 3);
  const encoded = encodePng({ width, height, rgb });
  writeFileSync(png, encoded);
  return Buffer.from(encoded).toString('base64');
}

const escape = (s: string) => s.replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]!));

function plot(note: Feedback, dirs: string[]): string {
  const s = note.state;
  let shapes: Shape[] = [], unavailable = '';
  try { shapes = loadShapes(dirs, s.stage, s.room, s.player.cf); }
  catch (err) { unavailable = `Collision unavailable: ${err instanceof Error ? err.message : String(err)}`; }
  const trail = note.path.filter((p) => p.stage === s.stage && p.room === s.room && p.agoMs >= 0 && p.agoMs <= 10000);
  const points = [s.player, ...trail, ...s.enemies];
  const xs = [...points.map((p) => p.x), ...shapes.flatMap((b) => [b.xMin, b.xMax])];
  const zs = [...points.map((p) => p.z), ...shapes.flatMap((b) => [b.zMin, b.zMax])];
  const x = Math.min(...xs) - 300, z = Math.min(...zs) - 300;
  const w = Math.max(...xs) - x + 300, h = Math.max(...zs) - z + 300;
  const collision = shapes.map((b) => b.kind === 'box'
    ? `<rect class="collision" x="${b.xMin}" y="${b.zMin}" width="${b.xMax - b.xMin}" height="${b.zMax - b.zMin}"/>`
    : `<circle class="collision" cx="${(b.xMin + b.xMax) / 2}" cy="${(b.zMin + b.zMax) / 2}" r="${(b.xMax - b.xMin) / 2}"/>`).join('');
  return `<svg viewBox="${x} ${z} ${w} ${h}" role="img" aria-label="Room collision and last ten seconds of movement">
${collision}<polyline class="trail" points="${trail.map((p) => `${p.x},${p.z}`).join(' ')}"/>
${s.enemies.map((e) => `<circle class="enemy" cx="${e.x}" cy="${e.z}" r="90"><title>type ${e.type}, health ${e.hp}</title></circle>`).join('')}
<circle class="player" cx="${s.player.x}" cy="${s.player.z}" r="90"/></svg>
<p class="muted">${unavailable ? escape(unavailable) : 'Grey: collision. Gold: path. Green: Rebecca. Red: enemies.'}</p>`;
}

/** Write one self-contained page. Screenshots travel with it as data URLs. */
export function page(dir: string, out: string, dirs: string[]): void {
  const entries = existsSync(path.join(dir, 'note.json')) ? [dir] : readdirSync(dir).sort()
    .map((name) => path.join(dir, name)).filter((entry) => existsSync(path.join(entry, 'note.json')));
  const cards = entries.map((entry) => {
    const n = readFeedback(entry), s = n.state, p = s.player;
    const id = path.basename(entry), slug = n.mode === 'REB' ? slugAt(s.stage, s.room) : undefined;
    const after = path.join(entry, 'after.png');
    return `<article id="${escape(id)}"><h2>${escape(n.kind)} <small>${escape(id)}</small></h2>
<p class="note">${escape(n.text) || '<i>Quick mark</i>'}</p>
<p>${escape(slug ?? `ROOM${roomLabel(s)}`)} · Camera ${s.camera} · Stage ${s.stage + 1}, room ${s.room.toString(16).toUpperCase()}</p>
<div class="pictures"><figure><img alt="Captured frame" src="data:image/png;base64,${screenshot(entry)}"><figcaption>Before</figcaption></figure>
<figure data-after="${escape(id)}">${existsSync(after) ? `<img alt="After the fix" src="data:image/png;base64,${readFileSync(after).toString('base64')}">` : '<div class="after">After: awaiting proof</div>'}<figcaption>After</figcaption></figure></div>
<div class="details"><div>${plot(n, dirs)}</div><div><p>Position: ${p.x}, ${p.y}, ${p.z} · angle ${p.angle}<br>HP ${p.hp}/${p.maxHp} · weapon slot ${p.weapon}</p>
<p>Enemies: ${s.enemies.length ? s.enemies.map((e) => `type ${e.type} at ${e.x}, ${e.y}, ${e.z}, health ${e.hp}`).join('<br>') : 'none'}</p>
<p class="muted">${escape(n.time)} · ${escape(n.mode)} · build ${escape(n.build.version)} · ${escape(n.build.compiled)}</p></div></div></article>`;
  });
  mkdirSync(path.dirname(out), { recursive: true });
  writeFileSync(out, `<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Rebecca playthrough feedback</title>
<script src="/research/rebecca-day/nav.js" defer></script>
<style>body{background:#121110;color:#ddd6c8;font:15px/1.5 system-ui,sans-serif;max-width:1200px;margin:2em auto;padding:0 1em}h1{font-size:1.7em}h2{font-size:1.15em}small,.muted,figcaption{color:#aaa294}small{font-weight:400}article{border-top:1px solid #49443c;padding:1em 0 2em}.note{white-space:pre-wrap;font-size:1.1em}.pictures,.details{display:grid;grid-template-columns:1fr 1fr;gap:16px}figure{margin:0}figure img{width:100%;aspect-ratio:4/3;object-fit:contain;image-rendering:pixelated}.after{min-height:180px;aspect-ratio:4/3;display:grid;place-items:center;border:1px dashed #686157;color:#aaa294}.details{margin-top:1em}svg{width:100%;height:240px;background:#1c1b18}.collision{fill:#666157;stroke:#a49b8b;stroke-width:1;vector-effect:non-scaling-stroke}.trail{fill:none;stroke:#e7b65c;stroke-width:3;vector-effect:non-scaling-stroke}.player{fill:#90d0a2}.enemy{fill:#ef8175}@media(max-width:650px){.pictures,.details{grid-template-columns:1fr}}</style>
<h1>Playthrough feedback</h1><p>${entries.length} ${entries.length === 1 ? 'note' : 'notes'}. Put an after.png in an entry and rebuild this page once the fix is proven.</p>
${cards.join('\n')}</html>`);
}

async function main(): Promise<void> {
  const [cmd, dir, out] = process.argv.slice(2);
  if (cmd === 'page' && dir && out) {
    const dirs = process.env.RE1_FEEDBACK_ASSETS?.split(path.delimiter) ?? [process.env.RE1_OVERLAY ?? 'assets/REB', process.env.RE1_BASE ?? 'assets/USA'];
    page(dir, out.endsWith('.html') ? out : path.join(out, 'index.html'), dirs);
  } else if (cmd === 'pull' && dir) {
    const { pullFeedback } = await import('./lab.ts');
    pullFeedback(dir);
  } else if (cmd === 'restore' && dir) {
    const note = readFeedback(dir);
    // lab.ts reads its default at module load. Rebecca's playtest lives here.
    process.env.RE1_LAB_GAME_DIR ??= 'D:\\Games\\RE1-files';
    const { open } = await import('./lab.ts');
    const session = await open(Number(process.env.PORT ?? 7811), feedbackBoot(note));
    let restored = false;
    try {
      await restore(session.link, feedbackCheckpoint(note));
      await session.link.keyboard(true);
      restored = true;
    }
    finally { session.end(!restored); }
    process.stdout.write('Checkpoint restored. Game left running.\n');
  } else throw new Error('usage: feedback.ts pull <dir> | page <dir> <out.html> | restore <entry>');
}
if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) await main();
