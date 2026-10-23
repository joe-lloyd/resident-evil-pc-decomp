// Each room's outline on her map, traced from its floor. A building keeps
// its straight walls: its floor (the bounds less the gaps and the big
// furniture) is its outline. Outdoors, and in the mine's rock, the outline is
// where she can walk (her collision, day/walkable.ts) and the doors she
// leaves by, then smoothed the way a hand-drawn map is:
//
//   1. close it: grow it 1 m and shrink it back, which fills the gaps a tree
//      or a crate leaves and rounds the inside corners;
//   2. fill the small holes left inside it; a big one is a building that
//      stands in the clearing, and stays, its door on its edge;
//   3. grow it again by a wobbling margin, 0.3 to 1.2 m, so its edges wander.
//
// Every step only adds floor, so the outline holds everywhere she can stand.
// Distances are exact (a Euclidean distance transform), so the result is
// round, not stepped. Grids are in the room's own metres, CELL to a cell.
import { CELL as WALK_CELL } from '../day/walkable.ts';
import { HOLE_M2, isHole, UNITS, type Rect, type RoomFloor } from './floors.ts';

/** Metres to a cell. */
export const CELL = 0.25;
/** Rooms underground: rough rock, drawn like outdoors. */
export const CAVES: ReadonlySet<string> = new Set(['tunnel', 'junction', 'gallery', 'crawl']);
/** Room past its floor that the grid keeps, in metres, for the margin to grow into. */
const PAD = 2.5;
const CLOSE = 1.0;
const GROW = 0.3;
const WOBBLE = 0.9;

/** A grid of cells over a room, in the room's own metres. */
export interface Outline {
  readonly x0: number;
  readonly y0: number;
  readonly cols: number;
  readonly rows: number;
  /** 1 where the room is. */
  readonly cells: Uint8Array;
}

export const organic = (f: RoomFloor) => !f.inside || CAVES.has(f.place);

/** Whether a room point, in metres, is in the outline. */
export function inOutline(o: Outline, x: number, y: number): boolean {
  const i = Math.floor((x - o.x0) / CELL);
  const j = Math.floor((y - o.y0) / CELL);
  return i >= 0 && j >= 0 && i < o.cols && j < o.rows && o.cells[j * o.cols + i] === 1;
}

const inRect = (x: number, z: number, r: Rect) => x >= r.x0 && x < r.x1 && z >= r.z0 && z < r.z1;

/** A building's floor at a room point (game units): in the bounds, out of the gaps and the big furniture. */
export function buildingFloor(f: RoomFloor, x: number, z: number): boolean {
  if (!inRect(x, z, f.bounds) || f.voids.some((v) => inRect(x, z, v))) return false;
  return !f.solids.some((s) => isHole(s) && (s.round ? Math.hypot((x - (s.x0 + s.x1) / 2) / ((s.x1 - s.x0) / 2), (z - (s.z0 + s.z1) / 2) / ((s.z1 - s.z0) / 2)) <= 1 : inRect(x, z, s)));
}

/** An empty grid over a room's bounds and PAD round them. */
function gridOver(f: RoomFloor): Outline {
  const b = f.bounds;
  const x0 = Math.floor(b.x0 / UNITS / CELL) * CELL - PAD;
  const y0 = Math.floor(b.z0 / UNITS / CELL) * CELL - PAD;
  const cols = Math.ceil((b.x1 / UNITS + PAD - x0) / CELL);
  const rows = Math.ceil((b.z1 / UNITS + PAD - y0) / CELL);
  return { x0, y0, cols, rows, cells: new Uint8Array(cols * rows) };
}

/** The spacing of her collision grid, in game units (day/walkable.ts): 10 cm. */
export const STEP = WALK_CELL;

/** Whether a room point (game units) is floor: a building's, or outdoors where she can stand and the doors she walks out through. */
export function isFloor(f: RoomFloor, x: number, z: number): boolean {
  return organic(f) ? f.stand(x, z) || f.doors.some((d) => inRect(x, z, d.zone)) : buildingFloor(f, x, z);
}

/**
 * The room's floor on its grid. A building's cell is floor by its middle;
 * outdoors a cell is floor if any spot of her 10 cm collision grid in it
 * is, so a narrow way between two rocks is not lost between cells.
 */
export function floorCells(f: RoomFloor): Outline {
  const g = gridOver(f);
  if (!organic(f)) {
    for (let j = 0; j < g.rows; j++)
      for (let i = 0; i < g.cols; i++) g.cells[j * g.cols + i] = isFloor(f, (g.x0 + (i + 0.5) * CELL) * UNITS, (g.y0 + (j + 0.5) * CELL) * UNITS) ? 1 : 0;
    return g;
  }
  const b = f.bounds;
  for (let z = b.z0; z <= b.z1; z += STEP)
    for (let x = b.x0; x <= b.x1; x += STEP) {
      if (!isFloor(f, x, z)) continue;
      const i = Math.floor((x / UNITS - g.x0) / CELL);
      const j = Math.floor((z / UNITS - g.y0) / CELL);
      g.cells[j * g.cols + i] = 1;
    }
  return g;
}

/** 1D squared distance transform (Felzenszwalb and Huttenlocher), in place over `f`. */
function edt1(f: Float64Array, n: number, d: Float64Array, v: Int32Array, z: Float64Array): void {
  let k = 0;
  v[0] = 0;
  z[0] = -Infinity;
  z[1] = Infinity;
  for (let q = 1; q < n; q++) {
    if (f[q] === Infinity) continue;
    if (f[v[k]!] === Infinity) {
      v[k] = q;
      continue;
    }
    let s = (f[q]! + q * q - (f[v[k]!]! + v[k]! * v[k]!)) / (2 * q - 2 * v[k]!);
    while (s <= z[k]!) {
      k--;
      s = (f[q]! + q * q - (f[v[k]!]! + v[k]! * v[k]!)) / (2 * q - 2 * v[k]!);
    }
    k++;
    v[k] = q;
    z[k] = s;
    z[k + 1] = Infinity;
  }
  k = 0;
  for (let q = 0; q < n; q++) {
    while (z[k + 1]! < q) k++;
    const p = v[k]!;
    d[q] = f[p] === Infinity ? Infinity : (q - p) * (q - p) + f[p]!;
  }
}

/** Each cell's distance, in metres, to the nearest cell where `on` is 1. */
export function distanceTo(on: Uint8Array, cols: number, rows: number): Float64Array {
  const n = Math.max(cols, rows);
  const f = new Float64Array(n);
  const d = new Float64Array(n);
  const v = new Int32Array(n);
  const z = new Float64Array(n + 1);
  const out = new Float64Array(cols * rows);
  for (let k = 0; k < out.length; k++) out[k] = on[k] ? 0 : Infinity;
  for (let i = 0; i < cols; i++) {
    for (let j = 0; j < rows; j++) f[j] = out[j * cols + i]!;
    edt1(f, rows, d, v, z);
    for (let j = 0; j < rows; j++) out[j * cols + i] = d[j]!;
  }
  for (let j = 0; j < rows; j++) {
    for (let i = 0; i < cols; i++) f[i] = out[j * cols + i]!;
    edt1(f, cols, d, v, z);
    for (let i = 0; i < cols; i++) out[j * cols + i] = Math.sqrt(d[i]!) * CELL;
  }
  return out;
}

/** The cells within `r(i, j)` metres of `on`. */
function grow(on: Uint8Array, cols: number, rows: number, r: (i: number, j: number) => number): Uint8Array {
  const d = distanceTo(on, cols, rows);
  const out = new Uint8Array(on.length);
  for (let j = 0; j < rows; j++) for (let i = 0; i < cols; i++) out[j * cols + i] = d[j * cols + i]! <= r(i, j) ? 1 : 0;
  return out;
}

const invert = (a: Uint8Array) => a.map((v) => 1 - v);

/**
 * Fill the small holes `on` encloses: those under `most` square metres. A
 * bigger one is a building standing in the clearing, its door on the hole's
 * edge, and stays.
 */
function fillHoles(on: Uint8Array, cols: number, rows: number, most: number): Uint8Array {
  const out = new Uint8Array(on.length).fill(1);
  const stack: number[] = [];
  const push = (i: number, j: number) => {
    if (i < 0 || j < 0 || i >= cols || j >= rows) return;
    const k = j * cols + i;
    if (on[k] || !out[k]) return;
    out[k] = 0;
    stack.push(k);
  };
  for (let i = 0; i < cols; i++) push(i, 0), push(i, rows - 1);
  for (let j = 0; j < rows; j++) push(0, j), push(cols - 1, j);
  while (stack.length) {
    const k = stack.pop()!;
    const i = k % cols;
    const j = (k - i) / cols;
    push(i - 1, j), push(i + 1, j), push(i, j - 1), push(i, j + 1);
  }
  // Each hole, by flood: kept open when it is big.
  const seen = new Uint8Array(on.length);
  for (let start = 0; start < on.length; start++) {
    if (on[start] || !out[start] || seen[start]) continue;
    const hole = [start];
    seen[start] = 1;
    for (let n = 0; n < hole.length; n++) {
      const k = hole[n]!;
      const i = k % cols;
      for (const m of [i > 0 ? k - 1 : -1, i < cols - 1 ? k + 1 : -1, k - cols, k + cols]) {
        if (m < 0 || m >= on.length || on[m] || seen[m]) continue;
        seen[m] = 1;
        hole.push(m);
      }
    }
    if (hole.length * CELL * CELL >= most) for (const k of hole) out[k] = 0;
  }
  return out;
}

/** A small number from a string, the same each run. */
export function seedOf(s: string): number {
  let h = 2166136261;
  for (let i = 0; i < s.length; i++) h = Math.imul(h ^ s.charCodeAt(i), 16777619);
  return (h >>> 0) / 4294967296;
}

/** Smooth noise over the plane, 0 to 1, waves 3 to 7 m long, the same for the same key. */
export function noise(key: string): (x: number, y: number) => number {
  const waves = [0, 1, 2, 3].map((k) => {
    const a = seedOf(`${key}/${k}/a`) * 2 * Math.PI;
    const len = 3 + 4 * seedOf(`${key}/${k}/l`);
    return { dx: Math.cos(a) * ((2 * Math.PI) / len), dy: Math.sin(a) * ((2 * Math.PI) / len), p: seedOf(`${key}/${k}/p`) * 2 * Math.PI, w: 1 / (k + 1) };
  });
  const total = waves.reduce((s, w) => s + w.w, 0);
  return (x, y) => 0.5 + (0.5 * waves.reduce((s, w) => s + w.w * Math.sin(w.dx * x + w.dy * y + w.p), 0)) / total;
}

const cache = new Map<string, Outline>();

/** A room's outline on her map. */
export function outlineOf(f: RoomFloor): Outline {
  const hit = cache.get(f.place);
  if (hit) return hit;
  const g = floorCells(f);
  let out: Outline = g;
  if (organic(f)) {
    const { cols, rows } = g;
    const grown = grow(g.cells, cols, rows, () => CLOSE);
    const closed = invert(grow(invert(grown), cols, rows, () => CLOSE));
    // Closing never loses floor, but a cell's centre test can at the grid's edge: keep the floor.
    for (let k = 0; k < closed.length; k++) closed[k] = closed[k]! | g.cells[k]!;
    const filled = fillHoles(closed, cols, rows, HOLE_M2);
    const n = noise(f.place);
    const wobbled = grow(filled, cols, rows, (i, j) => GROW + WOBBLE * n(g.x0 + i * CELL, g.y0 + j * CELL));
    out = { ...g, cells: wobbled };
  }
  cache.set(f.place, out);
  return out;
}
