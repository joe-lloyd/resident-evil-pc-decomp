// Draft floor plans for her map screen, drawn from the plan and the scenes:
// one per area of maps.ts, laid out by the plan's map positions, each room
// shaped by its floor, with corridors and door marks from the plan's links,
// in RE1's map colours. A first look to judge, not the final art.
//
//   node tools/rebecca/plan/map-draft.ts <outdir>
//
// Writes <area>.png (RE1's 128x128 map, shown at 3x) in two states: map
// owned but nothing visited, and the first rooms visited with hers marked.
import { existsSync, mkdirSync, readFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { writePng, type Image } from '../../harness/image.ts';
import { day } from './day.ts';
import { AREAS } from './maps.ts';

const here = path.dirname(fileURLToPath(import.meta.url));
const SIZE = 128;
const SHOW = 3;
type RGB = readonly [number, number, number];
const BACK: RGB = [0, 0, 0];
const VISITED: RGB = [24, 140, 24];
const EDGE: RGB = [150, 210, 90];
const OWNED: RGB = [16, 56, 16];
const OWNED_EDGE: RGB = [60, 110, 50];
const DOOR: RGB = [240, 190, 40];
const HERE: RGB = [230, 60, 70];

/** A room's floor in metres, from its scene, or a guess for the original save room. */
function floor(id: string): [number, number] {
  const p = day.places.find((x) => x.id === id)!;
  const file = path.join(here, '..', 'day', p.room ?? p.id, 'renders', 'room.json');
  if (!existsSync(file)) return [6, 4];
  const b = (JSON.parse(readFileSync(file, 'utf8')) as { bounds: { x0: number; z0: number; x1: number; z1: number } }).bounds;
  return [(b.x1 - b.x0) / 1700, (b.z1 - b.z0) / 1700];
}

interface Box {
  x0: number;
  y0: number;
  x1: number;
  y1: number;
}

function layout(places: readonly string[]): Map<string, Box> {
  const at = new Map(places.map((id) => [id, day.places.find((p) => p.id === id)!.at] as const));
  const xs = [...at.values()].map((a) => a[0]);
  const ys = [...at.values()].map((a) => a[1]);
  const [minX, maxX, minY, maxY] = [Math.min(...xs), Math.max(...xs), Math.min(...ys), Math.max(...ys)];
  // Grid steps of the plan's map: 2.2 across, 1.4 down.
  const unit = Math.min((SIZE - 16) / (maxX - minX + 2.2), (SIZE - 16) / (maxY - minY + 1.4));
  const cellW = 2.2 * unit - 3;
  const cellH = 1.4 * unit - 3;
  const sizes = places.map((id) => floor(id));
  const biggest = Math.max(...sizes.map(([w, h]) => Math.max(w, h)));
  const ox = (SIZE - (maxX - minX) * unit) / 2;
  const oy = (SIZE - (maxY - minY) * unit) / 2;
  const out = new Map<string, Box>();
  places.forEach((id, i) => {
    const [w, h] = sizes[i]!;
    // Bigger rooms draw bigger, but every room fits its cell and stays big enough to see.
    const fit = Math.min(cellW / w, cellH / h) * Math.max(0.55, Math.sqrt(Math.max(w, h) / biggest));
    const bw = Math.max(6, w * fit);
    const bh = Math.max(5, h * fit);
    const [ax, ay] = at.get(id)!;
    const cx = ox + (ax - minX) * unit;
    const cy = oy + (ay - minY) * unit;
    out.set(id, { x0: Math.round(cx - bw / 2), y0: Math.round(cy - bh / 2), x1: Math.round(cx + bw / 2), y1: Math.round(cy + bh / 2) });
  });
  return out;
}

function draw(places: readonly string[], visited: ReadonlySet<string>, current: string | undefined): Image {
  const rgb = new Uint8Array(SIZE * SIZE * 3);
  const put = (x: number, y: number, c: RGB) => {
    if (x < 0 || y < 0 || x >= SIZE || y >= SIZE) return;
    rgb.set(c, (y * SIZE + x) * 3);
  };
  const rect = (b: Box, fill: RGB, edge: RGB) => {
    for (let y = b.y0; y <= b.y1; y++) for (let x = b.x0; x <= b.x1; x++) put(x, y, x === b.x0 || x === b.x1 || y === b.y0 || y === b.y1 ? edge : fill);
  };
  rgb.fill(BACK[0]);
  const boxes = layout(places);
  const inArea = new Set(places);
  const centre = (b: Box) => [(b.x0 + b.x1) / 2, (b.y0 + b.y1) / 2] as const;
  // Where a line from a room's centre toward (tx, ty) leaves its edge.
  const exit = (b: Box, tx: number, ty: number): [number, number] => {
    const [cx, cy] = centre(b);
    const dx = tx - cx;
    const dy = ty - cy;
    const t = Math.min(dx ? (dx > 0 ? b.x1 - cx : b.x0 - cx) / dx : Infinity, dy ? (dy > 0 ? b.y1 - cy : b.y0 - cy) / dy : Infinity);
    return [Math.round(cx + dx * t), Math.round(cy + dy * t)];
  };
  const doors: [number, number][] = [];
  for (const l of day.links) {
    const a = boxes.get(l.from);
    const b = boxes.get(l.to);
    if (a && b) {
      const [ax, ay] = centre(a);
      const [bx, by] = centre(b);
      const pa = exit(a, bx, by);
      const pb = exit(b, ax, ay);
      const seen = visited.has(l.from) || visited.has(l.to);
      const steps = Math.max(Math.abs(pb[0] - pa[0]), Math.abs(pb[1] - pa[1]), 1);
      for (let i = 0; i <= steps; i++) {
        const x = Math.round(pa[0] + ((pb[0] - pa[0]) * i) / steps);
        const y = Math.round(pa[1] + ((pb[1] - pa[1]) * i) / steps);
        put(x, y, seen ? EDGE : OWNED_EDGE);
      }
      doors.push(pa, pb);
    } else if (a || b) {
      // A way off this map: a door mark on the edge facing the other area.
      const [box, other] = a ? [a, l.to] : [b!, l.from];
      const o = day.places.find((p) => p.id === other)!.at;
      const me = day.places.find((p) => p.id === (a ? l.from : l.to))!.at;
      const [cx, cy] = centre(box);
      doors.push(exit(box, cx + (o[0] - me[0]) * 100, cy + (o[1] - me[1]) * 100));
    }
  }
  for (const id of places) {
    const b = boxes.get(id)!;
    const lit = visited.has(id);
    rect(b, id === current ? HERE : lit ? VISITED : OWNED, lit ? EDGE : OWNED_EDGE);
  }
  for (const [x, y] of doors) for (let dy = -1; dy <= 1; dy++) for (let dx = -1; dx <= 1; dx++) put(x + dx, y + dy, DOOR);
  void inArea;
  // Shown at 3x with hard pixels, as the game zooms its maps.
  const big = new Uint8Array(SIZE * SHOW * SIZE * SHOW * 3);
  for (let y = 0; y < SIZE * SHOW; y++) {
    for (let x = 0; x < SIZE * SHOW; x++) {
      const s = (Math.floor(y / SHOW) * SIZE + Math.floor(x / SHOW)) * 3;
      big.set(rgb.subarray(s, s + 3), (y * SIZE * SHOW + x) * 3);
    }
  }
  return { width: SIZE * SHOW, height: SIZE * SHOW, rgb: big };
}

const out = process.argv[2];
if (!out) throw new Error('usage: map-draft.ts <outdir>');
mkdirSync(out, { recursive: true });
for (const a of AREAS) {
  writePng(path.join(out, `${a.id}-owned.png`), draw(a.places, new Set(), undefined));
  // The first half of the area visited, in the plan's order, and her in the last of them.
  const seen = a.places.slice(0, Math.max(1, Math.ceil(a.places.length / 2)));
  writePng(path.join(out, `${a.id}-visited.png`), draw(a.places, new Set(seen), seen.at(-1)));
}
console.log(`${AREAS.length} areas drawn to ${out}`);
