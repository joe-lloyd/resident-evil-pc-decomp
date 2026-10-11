// Moving parts of a camera's background, for the engine's BgAnim
// (src/game/BgAnim.cpp has the file format).
//
// The Blender scene renders the camera's background once (the base) and then
// again for each animation frame and each change of state. Here each of those
// renders becomes a layer of patches: the 16-pixel tiles where it differs from
// the base. Renders share a noise seed, so tiles the moving parts never touch
// match the base and are left out.
import type { Image } from '../harness/image.ts';
import { to555 } from './pak.ts';

const W = 320;
const H = 240;
const TILE = 16;
/** A pixel has changed when a 5-bit channel moves by at least this much. */
const PIXEL_STEP = 2;
/** A tile has changed when at least this many of its pixels have. */
const TILE_PIXELS = 3;

export interface AnimLayer {
  /** Renders after the base, in order; one for a change of state. */
  readonly frames: readonly Image[];
  /** Game frames (30 a second) per animation frame. */
  readonly ticks: number;
  /** Shown only while FG_SCENARIO (0) or FG_COMMON (1) flag `bit` is `value`. */
  readonly when?: { readonly bank: 0 | 1; readonly bit: number; readonly value: boolean };
}

interface Rect {
  readonly x: number;
  readonly y: number;
  readonly w: number;
  readonly h: number;
}

const to15 = (img: Image): Uint16Array => {
  if (img.width !== W || img.height !== H) throw new Error(`animation frames must be ${W}x${H}`);
  const out = new Uint16Array(W * H);
  for (let i = 0; i < out.length; i++) out[i] = to555(img.rgb[i * 3]!, img.rgb[i * 3 + 1]!, img.rgb[i * 3 + 2]!);
  return out;
};

const moved = (a: number, b: number) =>
  Math.abs((a & 31) - (b & 31)) >= PIXEL_STEP ||
  Math.abs(((a >> 5) & 31) - ((b >> 5) & 31)) >= PIXEL_STEP ||
  Math.abs(((a >> 10) & 31) - ((b >> 10) & 31)) >= PIXEL_STEP;

/** The tiles where any frame differs from the base, merged into rectangles along rows. */
export function changedRects(base: Uint16Array, frames: readonly Uint16Array[]): Rect[] {
  const cols = W / TILE;
  const rows = H / TILE;
  const dirty = new Array<boolean>(cols * rows).fill(false);
  for (const f of frames) {
    for (let ty = 0; ty < rows; ty++) {
      for (let tx = 0; tx < cols; tx++) {
        if (dirty[ty * cols + tx]) continue;
        let n = 0;
        for (let y = ty * TILE; y < (ty + 1) * TILE && n < TILE_PIXELS; y++) {
          for (let x = tx * TILE; x < (tx + 1) * TILE; x++) if (moved(base[y * W + x]!, f[y * W + x]!)) n++;
        }
        dirty[ty * cols + tx] = n >= TILE_PIXELS;
      }
    }
  }
  // Runs of dirty tiles per row, then runs stacked when they line up exactly.
  const open: { x0: number; x1: number; y0: number; y1: number }[] = [];
  const done: Rect[] = [];
  for (let ty = 0; ty < rows; ty++) {
    const runs: { x0: number; x1: number }[] = [];
    for (let tx = 0; tx < cols; tx++) {
      if (!dirty[ty * cols + tx]) continue;
      const last = runs[runs.length - 1];
      if (last && last.x1 === tx) last.x1 = tx + 1;
      else runs.push({ x0: tx, x1: tx + 1 });
    }
    for (let i = open.length - 1; i >= 0; i--) {
      const o = open[i]!;
      const k = runs.findIndex((r) => r.x0 === o.x0 && r.x1 === o.x1);
      if (k >= 0) {
        o.y1 = ty + 1;
        runs.splice(k, 1);
      } else {
        done.push({ x: o.x0 * TILE, y: o.y0 * TILE, w: (o.x1 - o.x0) * TILE, h: (o.y1 - o.y0) * TILE });
        open.splice(i, 1);
      }
    }
    for (const r of runs) open.push({ ...r, y0: ty, y1: ty + 1 });
  }
  for (const o of open) done.push({ x: o.x0 * TILE, y: o.y0 * TILE, w: (o.x1 - o.x0) * TILE, h: (o.y1 - o.y0) * TILE });
  return done;
}

/** The camera's RBA1 file, or undefined when nothing in it moves or changes. */
export function buildAnim(base: Image, layers: readonly AnimLayer[]): Uint8Array | undefined {
  const base15 = to15(base);
  const built: { layer: AnimLayer; frames: Uint16Array[]; rects: Rect[] }[] = [];
  for (const layer of layers) {
    if (layer.frames.length === 0) throw new Error('an animation layer needs at least one frame');
    if (layer.frames.length > 1 && (layer.ticks < 1 || layer.ticks > 255)) throw new Error(`ticks ${layer.ticks} out of range`);
    if (layer.when && (layer.when.bit < 0 || layer.when.bit > (layer.when.bank === 0 ? 127 : 255))) {
      throw new Error(`flag ${layer.when.bank}:${layer.when.bit} out of range`);
    }
    const frames = layer.frames.map(to15);
    const rects = changedRects(base15, frames);
    if (rects.length) built.push({ layer, frames, rects });
  }
  if (!built.length) return undefined;

  const bytes: number[] = [];
  const u16 = (v: number) => bytes.push(v & 0xff, (v >> 8) & 0xff);
  bytes.push(...'RBA1'.split('').map((c) => c.charCodeAt(0)));
  u16(built.length);
  for (const { layer, frames, rects } of built) {
    bytes.push(layer.when ? layer.when.bank : 0xff, layer.when?.bit ?? 0, layer.when?.value === false ? 0 : 1, frames.length > 1 ? layer.ticks : 0);
    u16(frames.length);
    for (const f of frames) {
      u16(rects.length);
      for (const r of rects) {
        u16(r.x);
        u16(r.y);
        u16(r.w);
        u16(r.h);
        for (let y = r.y; y < r.y + r.h; y++) for (let x = r.x; x < r.x + r.w; x++) u16(f[y * W + x]!);
      }
    }
  }
  return Uint8Array.from(bytes);
}

/** objspr\anm0<stage><room, two decimal digits><camera>.dat, beside the mask paks (BgAnim_Load). */
export const animFileName = (stage: number, room: number, camera: number) =>
  `ANM0${stage}${String(room).padStart(2, '0')}${camera}.dat`;
