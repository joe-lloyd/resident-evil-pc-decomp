// What in a camera's background should be drawn over Rebecca: every surface
// nearer the camera than somewhere she can stand behind it, worked out from
// the depth of every surface (cam<N>.zall.png, blender reb.py _all_depth) and
// the floor this camera shows her on. Nobody tags objects by hand: a post, a
// truck or a tree trunk is a mask where she can walk behind it, and nowhere
// else, which keeps a camera inside the engine's one 256x256 mask texture.
//
// Nothing low covers her: a surface less than LOW above the floor (the ground,
// a board lying on it, a puddle) is not a mask, which keeps the masks to the
// things she stands behind and the texture for them.
import { FRAME_H, FRAME_W } from './masks.ts';
import { HEIGHT, project, type Rect } from './day/floors.ts';

type V3 = [number, number, number];
export interface Camera {
  readonly from: V3;
  readonly to: V3;
  readonly fov: number;
}

/** Her half-width across the screen, in game units. */
const HALF_WIDTH = 260;
/** Floor cells this far apart, in game units. */
const STEP = 170;
/** A surface must be this much nearer than her to cover her: her own surface is not an occluder. */
const AHEAD = 150;
/** Surfaces lower than this above the floor (25 cm) never cover her. */
const LOW = 425;

const sub = (a: V3, b: V3): V3 => [a[0] - b[0], a[1] - b[1], a[2] - b[2]];
const dot = (a: V3, b: V3) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
const cross = (a: V3, b: V3): V3 => [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];
const norm = (a: V3): V3 => {
  const l = Math.hypot(...a);
  return [a[0] / l, a[1] / l, a[2] / l];
};

/** The game y (down) of the surface at view depth `z` under pixel (px, py): project's inverse. */
export function heightAt(cam: Camera, px: number, py: number, z: number): number {
  const fwd = norm(sub(cam.to, cam.from));
  const right = norm(cross(fwd, [0, -1, 0]));
  const up = cross(right, fwd);
  const a = (px + 0.5 - 160) / cam.fov;
  const b = (120 - py - 0.5) / cam.fov;
  return cam.from[1] + z * (fwd[1] + right[1] * a + up[1] * b);
}

/**
 * The farthest view depth at which some part of her lands on each pixel,
 * standing anywhere in `floor` (the camera's floor) where `standable` says
 * she can: her body is a box HEIGHT tall and 2 * HALF_WIDTH across.
 */
export function bodyReach(cam: Camera, floor: readonly Rect[], standable: (x: number, z: number) => boolean): Float32Array {
  const far = new Float32Array(FRAME_W * FRAME_H);
  for (const r of floor) {
    for (let x = r.x0 + STEP / 2; x < r.x1; x += STEP) {
      for (let z = r.z0 + STEP / 2; z < r.z1; z += STEP) {
        if (!standable(x, z)) continue;
        const feet = project(cam, [x, 0, z]);
        const head = project(cam, [x, -HEIGHT, z]);
        if (!feet || !head) continue;
        const half = Math.ceil((HALF_WIDTH * cam.fov) / feet.z);
        const x0 = Math.max(0, Math.floor(feet.x) - half);
        const x1 = Math.min(FRAME_W - 1, Math.ceil(feet.x) + half);
        const y0 = Math.max(0, Math.floor(Math.min(head.y, feet.y)));
        const y1 = Math.min(FRAME_H - 1, Math.ceil(Math.max(head.y, feet.y)));
        for (let y = y0; y <= y1; y++) {
          for (let px = x0; px <= x1; px++) {
            const i = y * FRAME_W + px;
            if (feet.z > far[i]!) far[i] = feet.z;
          }
        }
      }
    }
  }
  return far;
}

/**
 * Every surface of `all` (view depth per pixel, Infinity where nothing) that
 * covers her somewhere she can stand on this camera's floor: its depth where
 * it does, Infinity elsewhere, for buildMasks.
 */
export function occluders(cam: Camera, all: Float32Array, floor: readonly Rect[], standable: (x: number, z: number) => boolean): Float32Array {
  const reach = bodyReach(cam, floor, standable);
  const out = new Float32Array(FRAME_W * FRAME_H).fill(Infinity);
  for (let y = 0; y < FRAME_H; y++) {
    for (let x = 0; x < FRAME_W; x++) {
      const i = y * FRAME_W + x;
      const d = all[i]!;
      if (!Number.isFinite(d) || d >= reach[i]! - AHEAD) continue;
      if (heightAt(cam, x, y, d) > -LOW) continue;
      out[i] = d;
    }
  }
  return out;
}

/**
 * Where she can stand in a scene: inside its bounds, clear of its edge, its
 * walls and voids by her reach, and reachable on foot from a door she comes in by, so
 * a closed-off pocket behind a wall does not count. Without doors, every
 * clear spot counts.
 */
export function standableIn(
  scene: { bounds: Rect; walls: readonly Rect[]; voids?: readonly Rect[]; doors?: readonly { arrive: { x: number; z: number } }[] },
  reach = 300,
): (x: number, z: number) => boolean {
  const solid = [...scene.walls, ...(scene.voids ?? [])];
  const b = scene.bounds;
  // The room's edge is a wall too, drawn with some thickness: she keeps a little more than her reach from it.
  const edge = reach * 1.5;
  const clear = (x: number, z: number) =>
    x > b.x0 + edge && x < b.x1 - edge && z > b.z0 + edge && z < b.z1 - edge && !solid.some((w) => x > w.x0 - reach && x < w.x1 + reach && z > w.z0 - reach && z < w.z1 + reach);
  const seeds = (scene.doors ?? []).map((d) => d.arrive);
  if (!seeds.length) return clear;
  // Flood the clear floor from each door's arrival, cell by cell.
  const cell = 170;
  const cols = Math.ceil((b.x1 - b.x0) / cell);
  const rows = Math.ceil((b.z1 - b.z0) / cell);
  const at = (i: number, j: number) => [b.x0 + (i + 0.5) * cell, b.z0 + (j + 0.5) * cell] as const;
  const reached = new Uint8Array(cols * rows);
  const queue: number[] = [];
  for (const s of seeds) {
    // The nearest clear cell to where the door puts her.
    let best = -1;
    let bestD = Infinity;
    const si = Math.floor((s.x - b.x0) / cell);
    const sj = Math.floor((s.z - b.z0) / cell);
    for (let j = Math.max(0, sj - 6); j <= Math.min(rows - 1, sj + 6); j++) {
      for (let i = Math.max(0, si - 6); i <= Math.min(cols - 1, si + 6); i++) {
        const [x, z] = at(i, j);
        const d = Math.hypot(x - s.x, z - s.z);
        if (d < bestD && clear(x, z)) [best, bestD] = [j * cols + i, d];
      }
    }
    if (best >= 0 && !reached[best]) {
      reached[best] = 1;
      queue.push(best);
    }
  }
  while (queue.length) {
    const k = queue.pop()!;
    const i = k % cols;
    const j = (k - i) / cols;
    for (const [di, dj] of [[1, 0], [-1, 0], [0, 1], [0, -1]] as const) {
      const ni = i + di;
      const nj = j + dj;
      if (ni < 0 || nj < 0 || ni >= cols || nj >= rows) continue;
      const nk = nj * cols + ni;
      if (reached[nk] || !clear(...at(ni, nj))) continue;
      reached[nk] = 1;
      queue.push(nk);
    }
  }
  return (x, z) => {
    const i = Math.floor((x - b.x0) / cell);
    const j = Math.floor((z - b.z0) / cell);
    return i >= 0 && j >= 0 && i < cols && j < rows && reached[j * cols + i] === 1 && clear(x, z);
  };
}
