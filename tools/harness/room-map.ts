// Path planning from a room's own collision data (the .blk boundaries at
// RDT+0x4C, docs/RDT_FILE_FORMAT.md): rasterise the blocking shapes, grown by
// the player's radius, into a grid and search it with A*. Shapes are boxes
// stored max corner first, or circles whose radius is half the X extent.
import { existsSync, readFileSync } from 'node:fs';
import path from 'node:path';

export interface Shape {
  kind: 'box' | 'circle';
  xMin: number;
  zMin: number;
  xMax: number;
  zMax: number;
}

const CELL = 150;
const PLAYER_RADIUS = 380;

/** The room file the game would load: the overlay's copy first, then the base data. */
export function roomFile(dirs: string[], stage: number, room: number): string {
  const digit = stage + 1;
  const name = `ROOM${digit}${room.toString(16).toUpperCase().padStart(2, '0')}0.RDT`;
  for (const dir of dirs) {
    const p = path.join(dir, `Stage${digit}`, name);
    if (existsSync(p)) return p;
  }
  throw new Error(`${name} not found in ${dirs.join(', ')}`);
}

/** The blocking shapes of a room: the push shapes 1, 3 and 5. */
export function collisionShapes(rdt: Uint8Array): Shape[] {
  const view = new DataView(rdt.buffer, rdt.byteOffset, rdt.byteLength);
  const at = view.getUint32(0x4c, true);
  let count = 0;
  for (let q = 0; q < 4; q++) count += view.getInt32(at + 4 + q * 4, true);
  const seen = new Set<string>();
  const shapes: Shape[] = [];
  for (let i = 0; i < count; i++) {
    const r = at + 0x18 + i * 12;
    // Coordinates are unsigned, like the camera zones: an east wall reads
    // xMax 32958, not -32578.
    const xMax = view.getUint16(r, true);
    const zMax = view.getUint16(r + 2, true);
    const xMin = view.getUint16(r + 4, true);
    const zMin = view.getUint16(r + 6, true);
    const shape = view.getUint16(r + 8, true) & 0xff;
    // Every push shape blocks the player; flag bit 8 (0x100) only marks some
    // walls, and many carry just bit 9.
    if (![1, 3, 5].includes(shape)) continue;
    const key = `${xMin},${zMin},${xMax},${zMax},${shape}`;
    if (seen.has(key)) continue; // records crossing a quadrant split are repeated
    seen.add(key);
    shapes.push({ kind: shape === 3 ? 'circle' : 'box', xMin, zMin, xMax, zMax });
  }
  return shapes;
}

export function blocked(shapes: Shape[], x: number, z: number): boolean {
  for (const s of shapes) {
    if (s.kind === 'circle') {
      const cx = (s.xMin + s.xMax) / 2;
      const cz = (s.zMin + s.zMax) / 2;
      const r = (s.xMax - s.xMin) / 2 + PLAYER_RADIUS;
      if ((x - cx) ** 2 + (z - cz) ** 2 < r * r) return true;
    } else if (x > s.xMin - PLAYER_RADIUS && x < s.xMax + PLAYER_RADIUS && z > s.zMin - PLAYER_RADIUS && z < s.zMax + PLAYER_RADIUS) {
      return true;
    }
  }
  return false;
}

/**
 * Waypoints from (fromX, fromZ) to (toX, toZ), or undefined when the grid has
 * no way through. The goal may sit inside a blocked cell (a door zone in a
 * wall): the search ends at the nearest free cell instead.
 */
export function planPath(shapes: Shape[], fromX: number, fromZ: number, toX: number, toZ: number): { x: number; z: number }[] | undefined {
  const xs = shapes.flatMap((s) => [s.xMin, s.xMax]).concat([fromX, toX]);
  const zs = shapes.flatMap((s) => [s.zMin, s.zMax]).concat([fromZ, toZ]);
  const x0 = Math.min(...xs) - 2 * CELL;
  const z0 = Math.min(...zs) - 2 * CELL;
  const w = Math.ceil((Math.max(...xs) + 2 * CELL - x0) / CELL);
  const h = Math.ceil((Math.max(...zs) + 2 * CELL - z0) / CELL);
  const cx = (i: number) => x0 + (i % w) * CELL + CELL / 2;
  const cz = (i: number) => z0 + Math.floor(i / w) * CELL + CELL / 2;
  const cellOf = (x: number, z: number) => Math.floor((z - z0) / CELL) * w + Math.floor((x - x0) / CELL);
  const free = new Uint8Array(w * h);
  for (let i = 0; i < w * h; i++) free[i] = blocked(shapes, cx(i), cz(i)) ? 0 : 1;

  const start = cellOf(fromX, fromZ);
  // She is standing there, whatever the grid says, and the margin round the
  // walls is wider than the engine's own: let her step out of it.
  for (let i = 0; i < w * h; i++) {
    if (Math.hypot(cx(i) - fromX, cz(i) - fromZ) <= PLAYER_RADIUS + CELL) free[i] = 1;
  }
  const goal = cellOf(toX, toZ);
  const g = new Float64Array(w * h).fill(Infinity);
  const came = new Int32Array(w * h).fill(-1);
  const open = new Set<number>([start]);
  g[start] = 0;
  const hdist = (i: number) => Math.hypot(cx(i) - toX, cz(i) - toZ);
  let best = start;
  while (open.size) {
    let cur = -1;
    let curF = Infinity;
    for (const i of open) {
      const f = g[i] + hdist(i);
      if (f < curF) {
        curF = f;
        cur = i;
      }
    }
    open.delete(cur);
    if (hdist(cur) < hdist(best)) best = cur;
    if (cur === goal) break;
    const x = cur % w;
    const y = Math.floor(cur / w);
    for (const [dx, dy] of [[1, 0], [-1, 0], [0, 1], [0, -1], [1, 1], [1, -1], [-1, 1], [-1, -1]]) {
      const nx = x + dx;
      const ny = y + dy;
      if (nx < 0 || ny < 0 || nx >= w || ny >= h) continue;
      const n = ny * w + nx;
      if (!free[n] || (dx && dy && (!free[y * w + nx] || !free[ny * w + x]))) continue;
      const cost = g[cur] + (dx && dy ? Math.SQRT2 : 1);
      if (cost < g[n]) {
        g[n] = cost;
        came[n] = cur;
        open.add(n);
      }
    }
  }
  const end = g[goal] < Infinity ? goal : best;
  if (end === start && hdist(start) > 3 * CELL) return undefined;
  const cells: number[] = [];
  for (let c = end; c !== -1; c = came[c]) cells.unshift(c);

  // Keep only the cells where the straight line from the last kept point stops being clear.
  const clear = (ax: number, az: number, bx: number, bz: number) => {
    const steps = Math.ceil(Math.hypot(bx - ax, bz - az) / (CELL / 2));
    for (let s = 1; s < steps; s++) {
      const t = s / steps;
      if (!free[cellOf(ax + (bx - ax) * t, az + (bz - az) * t)]) return false;
    }
    return true;
  };
  const points: { x: number; z: number }[] = [];
  let ax = fromX;
  let az = fromZ;
  for (let i = 1; i < cells.length; i++) {
    if (!clear(ax, az, cx(cells[i]), cz(cells[i]))) {
      ax = cx(cells[i - 1]);
      az = cz(cells[i - 1]);
      points.push({ x: ax, z: az });
    }
  }
  points.push(g[goal] < Infinity ? { x: toX, z: toZ } : { x: cx(end), z: cz(end) });
  return points;
}

export function loadShapes(dirs: string[], stage: number, room: number): Shape[] {
  return collisionShapes(new Uint8Array(readFileSync(roomFile(dirs, stage, room))));
}
