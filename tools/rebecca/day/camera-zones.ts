// The camera switch zones of a room, drawn the way RE1 draws its own: a few
// convex quads per camera with straight borders, and a gap between the
// trigger into a camera and the trigger back out of it, so a step back and
// forth at a border never flips between two cameras.
//
// RE1's 154 rooms have 2 trigger quads per camera and a gap of 123 to 399
// units between the two triggers of a border (half of them in that range).
// The rectangles floors.ts used to give the switch table had 43 per camera
// and no gap.
//
// How: every cell of the floor gets the cameras that show her well there
// (floors.ts badness). Each camera's area is a site with a linear score,
// fitted so the best-scoring site's camera shows her, with GAP to spare at
// every border. The borders between sites are then straight lines, and each
// site's area, pulled back GAP / 2 from them, is a convex polygon: the
// trigger quads. Once triggered, a camera holds until she is GAP / 2 past
// the border, inside the next camera's trigger.
import { existsSync, readFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { autoFloors, badness, floorCells, readDepth, type FloorScene, type Rect } from './floors.ts';
import { dayRooms } from './rooms.ts';

export type Point = readonly [number, number];
/** Corners clockwise seen from above with Z up, as the engine's test reads them (Room.cpp is_entity_in_switch_zone). */
export type Quad = readonly [Point, Point, Point, Point];

/** Dead band between the triggers either side of a border, in game units. */
export const GAP = 400;
const CELL = 425;
/** Triggers reach past the floor's edge, so the edge is covered whatever the walls. */
const OVERHANG = 3000;
/** A camera shows her well enough at badness up to this (floors.ts: 0 is centred, whole and in plain view; 1.5 is a screen corner). */
const GOOD = 1.2;
/** Or, where no camera is that good, within this of the best one. */
const SLACK = 0.4;
/** A camera's area apart from its main one needs this many cells to be a site of its own. */
const MIN_SITE = 6;
/** An area is cut into compact pieces of about this many cells, at most MAX_PIECES, to start the fit from. */
const PIECE_CELLS = 220;
const MAX_PIECES = 4;

/** The middles of k compact pieces of a set of points: k-means from points spread farthest apart. */
function pieces(pts: [number, number][], k: number): [number, number][] {
  const mids: [number, number][] = [pts[0]!];
  while (mids.length < k) {
    let far = pts[0]!;
    let farD = -1;
    for (const p of pts) {
      const d = Math.min(...mids.map((m) => (m[0] - p[0]) ** 2 + (m[1] - p[1]) ** 2));
      if (d > farD) [far, farD] = [p, d];
    }
    mids.push(far);
  }
  for (let round = 0; round < 12; round++) {
    const sum = mids.map(() => [0, 0, 0]);
    for (const p of pts) {
      let best = 0;
      mids.forEach((m, i) => {
        if ((m[0] - p[0]) ** 2 + (m[1] - p[1]) ** 2 < (mids[best]![0] - p[0]) ** 2 + (mids[best]![1] - p[1]) ** 2) best = i;
      });
      sum[best]![0] += p[0]; sum[best]![1] += p[1]; sum[best]![2]++;
    }
    sum.forEach((s, i) => { if (s[2]) mids[i] = [s[0]! / s[2], s[1]! / s[2]]; });
  }
  return mids;
}

/** Areas added where she is still lost, at most, and the share of the floor that may stay lost. */
const MAX_ADDED = 8;
const ENOUGH = 0.015;
/** A piece goes if the fit without it loses her on at most this much more of the floor. */
const PRUNE_COST = 0.002;

/** The largest group of cells that touch, corners included. */
function biggestCluster<T extends { x: number; z: number }>(cells: T[]): T[] {
  const key = (x: number, z: number) => `${Math.round(x / CELL)},${Math.round(z / CELL)}`;
  const byKey = new Map(cells.map((c) => [key(c.x, c.z), c]));
  const seen = new Set<T>();
  let best: T[] = [];
  for (const start of cells) {
    if (seen.has(start)) continue;
    const group: T[] = [];
    const stack = [start];
    seen.add(start);
    while (stack.length) {
      const c = stack.pop()!;
      group.push(c);
      for (let di = -1; di <= 1; di++) {
        for (let dj = -1; dj <= 1; dj++) {
          const n = byKey.get(key(c.x + di * CELL, c.z + dj * CELL));
          if (n && !seen.has(n)) {
            seen.add(n);
            stack.push(n);
          }
        }
      }
    }
    if (group.length > best.length) best = group;
  }
  return best;
}

interface Cell {
  x: number;
  z: number;
  /** Cameras that show her well here. */
  ok: boolean[];
  best: number;
}

interface Site {
  camera: number;
  /** Score a*u + b*v + d over u = (x - cx) / s, v = (z - cz) / s. */
  w: [number, number, number];
}

export interface RoomZones {
  /** Trigger quads per camera: standing in one cuts to that camera. */
  zones: Quad[][];
  /** Whether camera `cam` can be the one on screen with her at (x, z): its trigger, or the gap round it. */
  holds: (cam: number, x: number, z: number) => boolean;
  /** Cells where the camera she can end up with does not show her well, with the camera. */
  misses: { x: number; z: number; camera: number }[];
  cells: number;
}

export function cellsOf(scene: FloorScene, depths: readonly (Float32Array | undefined)[], prefer?: readonly (Rect | readonly Rect[])[]): { cells: Cell[]; cols: number; rows: number; at: (Cell | undefined)[] } {
  const { bounds } = scene;
  const cols = Math.ceil((bounds.x1 - bounds.x0) / CELL);
  const rows = Math.ceil((bounds.z1 - bounds.z0) / CELL);
  const cells: Cell[] = [];
  const at: (Cell | undefined)[] = new Array(cols * rows);
  // floors.ts's choice, smoothed so a lone cell does not make an area of its own.
  const smooth = floorCells(scene, depths, CELL);
  for (let j = 0; j < rows; j++) {
    for (let i = 0; i < cols; i++) {
      const x = bounds.x0 + (i + 0.5) * CELL;
      const z = bounds.z0 + (j + 0.5) * CELL;
      if (scene.walls.some((w) => x >= w.x0 && x < w.x1 && z >= w.z0 && z < w.z1)) continue;
      const bad = scene.cameras.map((_, c) => badness(scene, c, x, z, depths[c]));
      // A hand-drawn floor (rooms.ts cameraFloor) names the camera; badness only widens the choice.
      const given = prefer?.findIndex((f) => [f].flat().some((r) => x >= r.x0 && x < r.x1 && z >= r.z0 && z < r.z1)) ?? -1;
      const best = given >= 0 ? given : smooth.cam[j * cols + i]! >= 0 ? smooth.cam[j * cols + i]! : bad.indexOf(Math.min(...bad));
      const limit = Math.max(GOOD, Math.min(...bad) + SLACK);
      const cell = { x, z, ok: bad.map((b, c) => c === best || b <= limit), best };
      cells.push(cell);
      at[j * cols + i] = cell;
    }
  }
  return { cells, cols, rows, at };
}

/** One site per camera's largest area of cells it is best for, and one for each other area of MIN_SITE cells or more. */
function sitesOf(scene: FloorScene, grid: ReturnType<typeof cellsOf>, norm: (x: number, z: number) => [number, number]): Site[] {
  const { cols, rows, at } = grid;
  const seen = new Set<Cell>();
  const areas: { camera: number; cells: Cell[] }[] = [];
  for (let k = 0; k < at.length; k++) {
    const start = at[k];
    if (!start || seen.has(start)) continue;
    const area: Cell[] = [];
    const stack = [k];
    seen.add(start);
    while (stack.length) {
      const n = stack.pop()!;
      area.push(at[n]!);
      const i = n % cols;
      const j = Math.floor(n / cols);
      for (const [a, b] of [[i - 1, j], [i + 1, j], [i, j - 1], [i, j + 1]] as const) {
        if (a < 0 || b < 0 || a >= cols || b >= rows) continue;
        const c = at[b * cols + a];
        if (!c || seen.has(c) || c.best !== start.best) continue;
        seen.add(c);
        stack.push(b * cols + a);
      }
    }
    areas.push({ camera: start.best, cells: area });
  }
  areas.sort((a, b) => b.cells.length - a.cells.length);
  const sites: Site[] = [];
  const has = new Set<number>();
  for (const area of areas) {
    if (has.has(area.camera) && area.cells.length < MIN_SITE) continue;
    has.add(area.camera);
    // Start from the Voronoi split of compact pieces of the area: score 2 m.p - |m|^2.
    for (const [mu, mv] of pieces(area.cells.map((c) => norm(c.x, c.z)), Math.min(MAX_PIECES, Math.ceil(area.cells.length / PIECE_CELLS)))) {
      sites.push({ camera: area.camera, w: [2 * mu, 2 * mv, -(mu * mu + mv * mv)] });
    }
  }
  return sites;
}

const score = (s: Site, u: number, v: number) => s.w[0] * u + s.w[1] * v + s.w[2];
/** Signed distance in normalised units from the k|j border, positive on k's side. */
function side(k: Site, j: Site, u: number, v: number): number {
  const g = Math.hypot(k.w[0] - j.w[0], k.w[1] - j.w[1]) || 1e-9;
  return (score(k, u, v) - score(j, u, v)) / g;
}

/** Whether camera `cam`'s site k holds at (u, v): no other camera's site is `gap` past its border with k. */
const holds = (sites: Site[], k: Site, u: number, v: number, gap: number) => sites.every((j) => j.camera === k.camera || side(k, j, u, v) >= -gap);

function clip(poly: Point[], a: number, b: number, c: number): Point[] {
  // Keep a*x + b*z >= c.
  const out: Point[] = [];
  for (let i = 0; i < poly.length; i++) {
    const p = poly[i]!;
    const q = poly[(i + 1) % poly.length]!;
    const fp = a * p[0] + b * p[1] - c;
    const fq = a * q[0] + b * q[1] - c;
    if (fp >= 0) out.push(p);
    if ((fp >= 0) !== (fq >= 0)) {
      const t = fp / (fp - fq);
      out.push([p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t]);
    }
  }
  return out;
}

const area = (poly: readonly Point[]) => {
  let a = 0;
  for (let i = 0; i < poly.length; i++) {
    const p = poly[i]!;
    const q = poly[(i + 1) % poly.length]!;
    a += p[0] * q[1] - q[0] * p[1];
  }
  return Math.abs(a) / 2;
};

function hull(pts: readonly Point[]): Point[] {
  const p = [...pts].sort((a, b) => a[0] - b[0] || a[1] - b[1]);
  const turn = (o: Point, a: Point, b: Point) => (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0]);
  const half = (list: Point[]) => {
    const out: Point[] = [];
    for (const q of list) {
      while (out.length >= 2 && turn(out[out.length - 2]!, out[out.length - 1]!, q) <= 0) out.pop();
      out.push(q);
    }
    return out.slice(0, -1);
  };
  return [...half(p), ...half(p.reverse())];
}

/** A camera's pieces, side by side, merged wherever two make one convex polygon. */
function mergeConvex(list: Point[][]): Point[][] {
  const out = [...list];
  for (let merged = true; merged; ) {
    merged = false;
    for (let i = 0; i < out.length && !merged; i++) {
      for (let j = i + 1; j < out.length && !merged; j++) {
        const h = hull([...out[i]!, ...out[j]!]);
        if (area(h) <= (area(out[i]!) + area(out[j]!)) * 1.002 + 1) {
          out.splice(j, 1);
          out[i] = h;
          merged = true;
        }
      }
    }
  }
  return out;
}

/** A convex polygon as quads fanned from its first corner, clockwise with Z up; a last triangle repeats its far corner. */
export function quadsOf(poly: readonly Point[]): Quad[] {
  let pts = poly.map(([x, z]) => [Math.round(x), Math.round(z)] as Point);
  pts = pts.filter((p, i) => {
    const q = pts[(i + 1) % pts.length]!;
    return p[0] !== q[0] || p[1] !== q[1];
  });
  // Corners on a straight line between their neighbours, which clipping leaves, only cost quads.
  pts = pts.filter((p, i) => {
    const a = pts[(i + pts.length - 1) % pts.length]!;
    const b = pts[(i + 1) % pts.length]!;
    const cross = (p[0] - a[0]) * (b[1] - a[1]) - (p[1] - a[1]) * (b[0] - a[0]);
    return Math.abs(cross) > Math.hypot(b[0] - a[0], b[1] - a[1]) * 2;
  });
  if (pts.length < 3) return [];
  let area = 0;
  for (let i = 0; i < pts.length; i++) {
    const p = pts[i]!;
    const q = pts[(i + 1) % pts.length]!;
    area += p[0] * q[1] - q[0] * p[1];
  }
  if (Math.abs(area) < 2) return [];
  if (area > 0) pts.reverse();
  const quads: Quad[] = [];
  for (let i = 1; i + 1 < pts.length; i += 2) {
    const c = pts[i + 2] ?? pts[i + 1]!;
    quads.push([pts[0]!, pts[i]!, pts[i + 1]!, c]);
  }
  return quads;
}

/** The engine's own test of a point against a zone quad (Room.cpp is_entity_in_switch_zone), for the checks. */
export function inQuad(q: Quad, x: number, z: number): boolean {
  const [p0, p1, p2, p3] = q;
  const dx = x - p0[0];
  const dz = z - p0[1];
  if ((p1[0] - p0[0]) * dz > (p1[1] - p0[1]) * dx) return false;
  if ((p3[0] - p0[0]) * dz < (p3[1] - p0[1]) * dx) return false;
  const dx2 = x - p2[0];
  const dz2 = z - p2[1];
  if ((p1[0] - p2[0]) * dz2 < (p1[1] - p2[1]) * dx2) return false;
  if ((p3[0] - p2[0]) * dz2 > (p3[1] - p2[1]) * dx2) return false;
  return true;
}

/**
 * The room's trigger quads. `prefer` is a hand-drawn camera floor
 * (rooms.ts cameraFloor), which picks the camera where several would do.
 */
export function roomZones(scene: FloorScene, depths: readonly (Float32Array | undefined)[], prefer?: readonly (Rect | readonly Rect[])[]): RoomZones {
  const { bounds } = scene;
  const cx = (bounds.x0 + bounds.x1) / 2;
  const cz = (bounds.z0 + bounds.z1) / 2;
  const s = Math.max(bounds.x1 - bounds.x0, bounds.z1 - bounds.z0) / 2 || 1;
  const norm = (x: number, z: number): [number, number] => [(x - cx) / s, (z - cz) / s];
  const grid = cellsOf(scene, depths, prefer);
  const sites = sitesOf(scene, grid, norm);
  const gap = GAP / s;

  // Fit: a perceptron that wants each cell's top site to be a camera that
  // shows her, GAP / 2 clear of the border with every site that does not.
  const cells = grid.cells.map((c) => ({ ...c, uv: norm(c.x, c.z) }));
  const missed = () => {
    // Each site's borders with the other cameras' sites, as unit-normal lines: side() without the work.
    const lines = sites.map((k) =>
      sites.filter((j) => j.camera !== k.camera).map((j) => {
        const g = Math.hypot(k.w[0] - j.w[0], k.w[1] - j.w[1]) || 1e-9;
        return [(k.w[0] - j.w[0]) / g, (k.w[1] - j.w[1]) / g, (k.w[2] - j.w[2]) / g] as const;
      }),
    );
    return cells.filter((c) => sites.some((k, i) => !c.ok[k.camera] && lines[i]!.every((l) => l[0] * c.uv[0] + l[1] * c.uv[1] + l[2] >= -gap / 2)));
  };
  const fit = () => {
    let bestW = sites.map((k) => [...k.w] as Site['w']);
    let bestMiss = missed().length;
    for (let epoch = 0; epoch < 150 && bestMiss > 0; epoch++) {
      const rate = 0.05 / (1 + epoch / 20);
      for (const c of cells) {
        const [u, v] = c.uv;
        let t: Site | undefined;
        for (const k of sites) if (c.ok[k.camera] && (!t || score(k, u, v) > score(t, u, v))) t = k;
        if (!t) continue;
        for (const k of sites) {
          if (c.ok[k.camera] || side(t, k, u, v) >= gap) continue;
          t.w[0] += rate * u; t.w[1] += rate * v; t.w[2] += rate;
          k.w[0] -= rate * u; k.w[1] -= rate * v; k.w[2] -= rate;
        }
      }
      const miss = missed().length;
      if (miss < bestMiss) [bestMiss, bestW] = [miss, sites.map((k) => [...k.w] as Site['w'])];
    }
    sites.forEach((k, i) => (k.w = bestW[i]!));
  };
  fit();
  // One straight-edged area a camera can be too few: where she is still
  // lost, give the camera that shows that spot best an area of its own there,
  // and fit again. Each one is a quad or two more; one that does not help
  // is taken back out.
  let kept = { sites: sites.map((k) => ({ camera: k.camera, w: [...k.w] as Site['w'] })), lost: missed().length };
  for (let added = 0; added < MAX_ADDED && kept.lost > cells.length * ENOUGH; added++) {
    const cluster = biggestCluster(missed());
    const votes = new Map<number, number>();
    for (const c of cluster) votes.set(c.best, (votes.get(c.best) ?? 0) + 1);
    const camera = [...votes].sort((a, b) => b[1] - a[1])[0]![0];
    const u = cluster.reduce((a, c) => a + c.uv[0], 0) / cluster.length;
    const v = cluster.reduce((a, c) => a + c.uv[1], 0) / cluster.length;
    const top = sites.reduce((a, k) => (score(k, u, v) > score(a, u, v) ? k : a));
    // Start as the site that wins there, but ahead of it beyond a line that
    // cuts the spot off from the rest of that site's floor.
    const rest = cells.filter((c) => score(top, c.uv[0], c.uv[1]) >= Math.max(...sites.map((k) => score(k, c.uv[0], c.uv[1]))) && !cluster.includes(c));
    const ru = rest.length ? rest.reduce((a, c) => a + c.uv[0], 0) / rest.length : u - 1;
    const rv = rest.length ? rest.reduce((a, c) => a + c.uv[1], 0) / rest.length : v;
    const nl = Math.hypot(u - ru, v - rv) || 1;
    const [nu, nv] = [(u - ru) / nl, (v - rv) / nl];
    const edge = Math.min(...cluster.map((c) => nu * c.uv[0] + nv * c.uv[1]));
    sites.push({ camera, w: [top.w[0] + nu, top.w[1] + nv, top.w[2] - edge] });
    fit();
    const lost = missed().length;
    if (lost < kept.lost) kept = { sites: sites.map((k) => ({ camera: k.camera, w: [...k.w] as Site['w'] })), lost };
    else sites.splice(0, sites.length, ...kept.sites.map((k) => ({ camera: k.camera, w: [...k.w] as Site['w'] })));
  }

  // Fewer pieces, fewer quads: drop each piece the fit does as well without.
  const snapshot = () => sites.map((k) => ({ camera: k.camera, w: [...k.w] as Site['w'] }));
  for (let i = sites.length - 1; i >= 0; i--) {
    const k = sites[i]!;
    if (sites.filter((j) => j.camera === k.camera).length < 2) continue;
    sites.splice(i, 1);
    fit();
    const lost = missed().length;
    if (lost <= kept.lost + cells.length * PRUNE_COST) kept = { sites: snapshot(), lost: Math.min(lost, kept.lost) };
    else sites.splice(0, sites.length, ...kept.sites.map((j) => ({ camera: j.camera, w: [...j.w] as Site['w'] })));
  }

  // Each site's trigger: the floor's box, pulled back GAP / 2 from every border with another camera.
  const box: Point[] = [
    [Math.max(0, bounds.x0 - OVERHANG), Math.max(0, bounds.z0 - OVERHANG)],
    [Math.max(0, bounds.x0 - OVERHANG), bounds.z1 + OVERHANG],
    [bounds.x1 + OVERHANG, bounds.z1 + OVERHANG],
    [bounds.x1 + OVERHANG, Math.max(0, bounds.z0 - OVERHANG)],
  ];
  const polys: Point[][][] = scene.cameras.map(() => []);
  for (const k of sites) {
    let poly = box;
    for (const j of sites) {
      if (j === k) continue;
      // side(k, j) >= gap / 2 in game units, or >= 0 against the camera's own other sites: a*x + b*z >= c.
      const da = k.w[0] - j.w[0];
      const db = k.w[1] - j.w[1];
      const dd = k.w[2] - j.w[2];
      const g = Math.hypot(da, db) || 1e-9;
      poly = clip(poly, da / s, db / s, (da * cx + db * cz) / s - dd + (j.camera === k.camera ? 0 : (g * gap) / 2));
      if (poly.length < 3) break;
    }
    if (poly.length >= 3) polys[k.camera]!.push(poly);
  }
  const zones: Quad[][] = polys.map((list) => mergeConvex(list).flatMap(quadsOf));

  // What she gets: from any camera, the ones she can still be on at a cell
  // are those whose trigger she last crossed and has not left the hold of.
  const misses: RoomZones['misses'] = [];
  for (const c of cells) {
    for (const k of sites) {
      if (!c.ok[k.camera] && holds(sites, k, c.uv[0], c.uv[1], gap / 2)) {
        misses.push({ x: c.x, z: c.z, camera: k.camera });
        break;
      }
    }
  }
  const holdsAt = (cam: number, x: number, z: number) => {
    const [u, v] = norm(x, z);
    return sites.some((k) => k.camera === cam && holds(sites, k, u, v, gap / 2));
  };
  return { zones, holds: holdsAt, misses, cells: cells.length };
}

// node tools/rebecca/day/camera-zones.ts [slug ...]: every room's zones, quads per camera and where they lose her.
if (process.argv[1] === fileURLToPath(import.meta.url)) {
  const want = process.argv.slice(2);
  let quads = 0;
  let cams = 0;
  for (const spec of dayRooms.filter((r) => !want.length || want.includes(r.slug))) {
    const renders = path.join(path.dirname(fileURLToPath(import.meta.url)), spec.slug, 'renders');
    const json = JSON.parse(readFileSync(path.join(renders, 'room.json'), 'utf8')) as FloorScene & { voids?: Rect[] };
    const scene: FloorScene = { ...json, walls: [...json.walls, ...(json.voids ?? [])] };
    const depths = scene.cameras.map((_, i) => {
      const f = path.join(renders, `cam${i}.depth.png`);
      return existsSync(f) ? readDepth(f) : undefined;
    });
    const z = roomZones(scene, depths, spec.cameraFloor === 'auto' ? undefined : spec.cameraFloor);
    quads += z.zones.flat().length;
    cams += z.zones.length;
    const pct = ((100 * z.misses.length) / Math.max(1, z.cells)).toFixed(1);
    // The old switch table: the rectangles' own camera, wherever she is, from either side.
    const floors = spec.cameraFloor === 'auto' ? autoFloors(scene, depths) : spec.cameraFloor;
    const { cells } = cellsOf(scene, depths, spec.cameraFloor === 'auto' ? undefined : spec.cameraFloor);
    const owner = (x: number, z: number) => floors.findIndex((f) => [f].flat().some((r) => x >= r.x0 && x < r.x1 && z >= r.z0 && z < r.z1));
    const old = cells.filter((c) => { const o = owner(c.x, c.z); return o >= 0 && !c.ok[o]; }).length;
    const rects = floors.map((f) => [f].flat().length);
    console.log(`${spec.slug.padEnd(14)} quads ${z.zones.map((q) => q.length).join('/').padEnd(14)} rects ${rects.join('/').padEnd(18)} shown badly: ${pct}% (rects ${((100 * old) / Math.max(1, cells.length)).toFixed(1)}%)`);
  }
  console.log(`${(quads / Math.max(1, cams)).toFixed(1)} quads per camera`);
}
