// Which camera shows each part of a room's floor, worked out from the scene:
// for every half-metre cell, the camera that shows Rebecca whole, unhidden
// and nearest the middle of the screen. The engine cuts to a camera when she
// walks into one of its rectangles (room.ts switchZones), so the cells are
// merged into rectangles per camera.
//
// Hidden means a foreground object of the scene (blender reb.mask) is nearer
// the camera than she is where her body lands on screen: the depth renders
// hold exactly those objects.
import { readPng } from '../../harness/image.ts';
import { FRAME_H, FRAME_W } from '../masks.ts';

type V3 = [number, number, number];
export type Rect = { readonly x0: number; readonly z0: number; readonly x1: number; readonly z1: number };
export interface FloorScene {
  cameras: { from: V3; to: V3; fov: number }[];
  walls: Rect[];
  bounds: Rect;
}

/** Her height in game units (tools/harness/measure-height.ts). */
export const HEIGHT = 2700;
/** Screen margin in pixels: a character half off the edge is not seen. */
const MARGIN = 12;
/** Cells along each side of the floor reach this far past it, so the edge is covered. */
const OVERHANG = 3000;

const sub = (a: V3, b: V3): V3 => [a[0] - b[0], a[1] - b[1], a[2] - b[2]];
const dot = (a: V3, b: V3) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
const cross = (a: V3, b: V3): V3 => [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];
const norm = (a: V3): V3 => {
  const l = Math.hypot(...a);
  return [a[0] / l, a[1] / l, a[2] / l];
};

/** Screen position (320x240) and view depth of a game point; undefined behind the camera. */
export function project(cam: FloorScene['cameras'][number], p: V3): { x: number; y: number; z: number } | undefined {
  const fwd = norm(sub(cam.to, cam.from));
  const right = norm(cross(fwd, [0, -1, 0]));
  const up = cross(right, fwd);
  const d = sub(p, cam.from);
  const z = dot(d, fwd);
  if (z <= 1) return undefined;
  return { x: 160 - (dot(d, right) * cam.fov) / z, y: 120 - (dot(d, up) * cam.fov) / z, z };
}

/** Foreground depth from cam<N>.depth.png: view Z / 16 as R * 256 + G, Infinity where nothing is in front. */
export function readDepth(file: string): Float32Array {
  const img = readPng(file);
  if (img.width !== FRAME_W || img.height !== FRAME_H) throw new Error(`${file} is not ${FRAME_W}x${FRAME_H}`);
  const depth = new Float32Array(FRAME_W * FRAME_H);
  for (let i = 0; i < depth.length; i++) {
    const v = img.rgb[i * 3]! * 256 + img.rgb[i * 3 + 1]!;
    depth[i] = v === 0 ? Infinity : v * 16;
  }
  return depth;
}

const offscreen = (s: { x: number; y: number }) =>
  Math.max(0, MARGIN - s.x) + Math.max(0, s.x - (320 - MARGIN)) + Math.max(0, MARGIN / 2 - s.y) + Math.max(0, s.y - (240 - MARGIN / 2));

/** How badly camera `c` shows her standing at (x, z): 0 is centred, whole and in plain view. */
export function badness(scene: FloorScene, c: number, x: number, z: number, depth?: Float32Array): number {
  const cam = scene.cameras[c]!;
  const feet = project(cam, [x, 0, z]);
  const head = project(cam, [x, -HEIGHT, z]);
  if (!feet || !head) return 1e9;
  let score = (offscreen(feet) + offscreen(head)) * 0.5;
  const mid = project(cam, [x, -HEIGHT / 2, z])!;
  score += Math.abs(mid.x - 160) / 160 + (Math.abs(mid.y - 120) / 120) * 0.5;
  const tall = feet.y - head.y;
  if (tall < 50) score += (50 - tall) / 25;
  if (depth) {
    // Legs behind a table are fine; a hidden head and chest are not.
    const weight = [0.2, 0.3, 0.6, 1.5, 2.5];
    for (let k = 1; k <= 5; k++) {
      const p = project(cam, [x, (-HEIGHT * k) / 6, z]);
      if (!p) continue;
      const px = Math.round(p.x);
      const py = Math.round(p.y);
      if (px < 0 || px >= FRAME_W || py < 0 || py >= FRAME_H) continue;
      if (depth[py * FRAME_W + px]! < p.z - 400) score += weight[k - 1]!;
    }
  }
  return score;
}

/** The camera for each cell of the floor, rows by Z then X; walls take their neighbours' camera. */
export function floorCells(scene: FloorScene, depths: readonly (Float32Array | undefined)[], step = 850): { cols: number; rows: number; cam: number[]; wall: boolean[] } {
  const { bounds } = scene;
  const cols = Math.ceil((bounds.x1 - bounds.x0) / step);
  const rows = Math.ceil((bounds.z1 - bounds.z0) / step);
  const cam = new Array<number>(cols * rows).fill(-1);
  const wall = new Array<boolean>(cols * rows).fill(false);
  for (let j = 0; j < rows; j++) {
    for (let i = 0; i < cols; i++) {
      const x = bounds.x0 + (i + 0.5) * step;
      const z = bounds.z0 + (j + 0.5) * step;
      if (scene.walls.some((w) => x >= w.x0 && x < w.x1 && z >= w.z0 && z < w.z1)) {
        wall[j * cols + i] = true;
        continue;
      }
      let best = 0;
      let bestScore = Infinity;
      scene.cameras.forEach((_, c) => {
        const s = badness(scene, c, x, z, depths[c]);
        if (s < bestScore) [best, bestScore] = [c, s];
      });
      cam[j * cols + i] = best;
    }
  }
  // Smooth out single cells, so walking along a boundary does not flicker.
  for (let pass = 0; pass < 2; pass++) {
    const next = cam.slice();
    for (let j = 0; j < rows; j++) {
      for (let i = 0; i < cols; i++) {
        if (wall[j * cols + i]) continue;
        const votes = new Map<number, number>();
        for (let dj = -1; dj <= 1; dj++) {
          for (let di = -1; di <= 1; di++) {
            const ii = i + di;
            const jj = j + dj;
            if (ii < 0 || jj < 0 || ii >= cols || jj >= rows || wall[jj * cols + ii]) continue;
            const c = cam[jj * cols + ii]!;
            votes.set(c, (votes.get(c) ?? 0) + 1);
          }
        }
        const [top, n] = [...votes].sort((a, b) => b[1] - a[1])[0]!;
        if (top !== cam[j * cols + i] && n >= 5) next[j * cols + i] = top;
      }
    }
    for (let k = 0; k < cam.length; k++) cam[k] = next[k]!;
  }
  // Walls: the camera of the nearest floor, spreading outward.
  for (let changed = true; changed; ) {
    changed = false;
    for (let k = 0; k < cam.length; k++) {
      if (cam[k] !== -1) continue;
      const i = k % cols;
      const j = Math.floor(k / cols);
      const n = [[i - 1, j], [i + 1, j], [i, j - 1], [i, j + 1]].find(([a, b]) => a! >= 0 && b! >= 0 && a! < cols && b! < rows && cam[b! * cols + a!]! >= 0);
      if (n) {
        cam[k] = cam[n[1]! * cols + n[0]!]!;
        changed = true;
      }
    }
  }
  return { cols, rows, cam, wall };
}

/** The cells as rectangles per camera: runs along each row, stacked where they line up. */
export function autoFloors(scene: FloorScene, depths: readonly (Float32Array | undefined)[], step = 850): Rect[][] {
  const { bounds } = scene;
  const { cols, rows, cam } = floorCells(scene, depths, step);
  const edgeX = (i: number) => (i <= 0 ? Math.max(0, bounds.x0 - OVERHANG) : i >= cols ? bounds.x1 + OVERHANG : bounds.x0 + i * step);
  const edgeZ = (j: number) => (j <= 0 ? Math.max(0, bounds.z0 - OVERHANG) : j >= rows ? bounds.z1 + OVERHANG : bounds.z0 + j * step);
  return scene.cameras.map((_, c) => {
    const out: Rect[] = [];
    let open: { i0: number; i1: number; j0: number; j1: number }[] = [];
    for (let j = 0; j <= rows; j++) {
      const runs: { i0: number; i1: number }[] = [];
      if (j < rows) {
        for (let i = 0; i < cols; i++) {
          if (cam[j * cols + i] !== c) continue;
          const last = runs[runs.length - 1];
          if (last && last.i1 === i) last.i1 = i + 1;
          else runs.push({ i0: i, i1: i + 1 });
        }
      }
      const still: typeof open = [];
      for (const o of open) {
        const k = runs.findIndex((r) => r.i0 === o.i0 && r.i1 === o.i1);
        if (k >= 0) {
          o.j1 = j + 1;
          runs.splice(k, 1);
          still.push(o);
        } else {
          out.push({ x0: edgeX(o.i0), z0: edgeZ(o.j0), x1: edgeX(o.i1), z1: edgeZ(o.j1) });
        }
      }
      open = [...still, ...runs.map((r) => ({ ...r, j0: j, j1: j + 1 }))];
    }
    return out;
  });
}
