// Foreground masks for a new room: the parts of a camera's background that
// are drawn over a character standing behind them (a door frame, a table
// edge, a tree trunk). The engine draws them as sprites cut from one 256x256
// 8 bpp texture, each with its own depth (Room.cpp: Room_LoadCameraSprites,
// load_room_masks, DrawRoomSpr; docs/RDT_FILE_FORMAT.md).
//
// Input is the camera's background and, per pixel, the view-space depth of a
// foreground surface there (Infinity where there is none), from the Blender
// render. Output is the camera's mask block for the room file and the mask
// texture, a TIM to pack as objspr\osp0<stage><room, decimal><camera>.pak.
//
// The format, read from the shipped rooms (ROOM2030 camera 0 and its pak):
//   block: int32 groupCount; per group {u16 spriteCount, u16 texBits,
//          i16 originX, i16 originY}; then the sprites, group by group:
//          {u16 u | v << 8, u16 dx | dy << 8, u16 depth, u16 flags, u16 w, u16 h}
//          with flags 0x00C0 (explicit width and height, the shipped blend).
//          A sprite covers frame pixels (originX + dx, originY + dy).
//   depth: view-space Z / 16 (DrawRoomSpr sorts it at depth << 4, the units
//          entities use).
//   TIM:   8 bpp, a 256-colour CLUT at VRAM (0, 480), the image 256x256 at
//          (0, 0). Colour 0 (0x0000) is transparent.
import type { Image } from '../harness/image.ts';
import { lzwPack } from './pak.ts';

export const FRAME_W = 320;
export const FRAME_H = 240;
const ATLAS = 256;
const TILE = 16;
/** Room_LoadCameraSprites fills g_RoomSprEntries[128]. */
const MAX_SPRITES = 128;
const SPRITE_FLAGS = 0x00c0;
const TEX_BITS = 0x7800;
/** Tiles whose depths differ by no more than this many units merge into one sprite. */
const MERGE_DEPTH = 6;

export interface MaskSprite {
  /** Frame pixels covered. */
  readonly x: number;
  readonly y: number;
  readonly w: number;
  readonly h: number;
  /** View-space Z / 16. */
  readonly depth: number;
}

/** Cut the foreground into sprites: 16-pixel tiles, merged along rows where their depth agrees. */
export function cutSprites(depth: Float32Array, tile = TILE): MaskSprite[] {
  const cols = Math.ceil(FRAME_W / tile);
  const rows = Math.ceil(FRAME_H / tile);
  const tileDepth = (cx: number, cy: number): number | undefined => {
    let min = Infinity;
    for (let y = cy * tile; y < Math.min(FRAME_H, (cy + 1) * tile); y++) {
      for (let x = cx * tile; x < Math.min(FRAME_W, (cx + 1) * tile); x++) min = Math.min(min, depth[y * FRAME_W + x]!);
    }
    return Number.isFinite(min) ? Math.max(1, Math.floor(min / 16)) : undefined;
  };
  const sprites: MaskSprite[] = [];
  for (let cy = 0; cy < rows; cy++) {
    let run: { x0: number; x1: number; depth: number } | undefined;
    const flush = () => {
      if (!run) return;
      const y = cy * tile;
      sprites.push({ x: run.x0 * tile, y, w: Math.min(FRAME_W, run.x1 * tile) - run.x0 * tile, h: Math.min(FRAME_H, y + tile) - y, depth: run.depth });
      run = undefined;
    };
    for (let cx = 0; cx < cols; cx++) {
      const d = tileDepth(cx, cy);
      if (d === undefined) {
        flush();
        continue;
      }
      // A sprite is one depth: keep the nearest, and stop where depth jumps or the
      // sprite would be wider than the texture rows the packer fills.
      if (run && Math.abs(run.depth - d) <= MERGE_DEPTH && (run.x1 - run.x0 + 1) * tile <= 128) {
        run.x1 = cx + 1;
        run.depth = Math.min(run.depth, d);
      } else {
        flush();
        run = { x0: cx, x1: cx + 1, depth: d };
      }
    }
    flush();
  }
  return sprites;
}

/** Place sprites in the 256x256 texture, shelf by shelf; undefined when they do not fit. */
function pack(sprites: readonly MaskSprite[]): { u: number; v: number }[] | undefined {
  const order = sprites.map((s, i) => i).sort((a, b) => sprites[b]!.h - sprites[a]!.h);
  const at: { u: number; v: number }[] = new Array(sprites.length);
  let u = 0;
  let v = 0;
  let shelf = 0;
  for (const i of order) {
    const s = sprites[i]!;
    if (u + s.w > ATLAS) {
      u = 0;
      v += shelf;
      shelf = 0;
    }
    if (v + s.h > ATLAS) return undefined;
    at[i] = { u, v };
    u += s.w;
    shelf = Math.max(shelf, s.h);
  }
  return at;
}

/** 8 bits per channel to PS1 15-bit colour; black is 0x8000 so it is not the transparent 0x0000. */
function to555(r: number, g: number, b: number): number {
  const ch = (v: number) => Math.min((v + 4) >> 3, 31);
  const c = (ch(b) << 10) | (ch(g) << 5) | ch(r);
  return c === 0 ? 0x8000 : c;
}

/** At most `max` colours for `colors` (15-bit), by median cut; returns the palette and a lookup. */
function quantize(colors: readonly number[], max: number): { palette: number[]; index: (c: number) => number } {
  const unique = [...new Set(colors)];
  if (unique.length <= max) {
    const at = new Map(unique.map((c, i) => [c, i]));
    return { palette: unique, index: (c) => at.get(c)! };
  }
  const chan = (c: number, k: number) => (c >> (5 * k)) & 31;
  let boxes: number[][] = [unique];
  while (boxes.length < max) {
    // Split the box with the widest channel range.
    let best = -1;
    let bestRange = -1;
    let bestChan = 0;
    boxes.forEach((box, i) => {
      if (box.length < 2) return;
      for (let k = 0; k < 3; k++) {
        const vals = box.map((c) => chan(c, k));
        const range = Math.max(...vals) - Math.min(...vals);
        if (range > bestRange) [bestRange, best, bestChan] = [range, i, k];
      }
    });
    if (best < 0 || bestRange === 0) break;
    const box = boxes[best]!.sort((a, b) => chan(a, bestChan) - chan(b, bestChan));
    const mid = box.length >> 1;
    boxes = [...boxes.slice(0, best), box.slice(0, mid), box.slice(mid), ...boxes.slice(best + 1)];
  }
  const palette = boxes.map((box) => {
    const avg = (k: number) => Math.round(box.reduce((n, c) => n + chan(c, k), 0) / box.length);
    const c = avg(0) | (avg(1) << 5) | (avg(2) << 10);
    return c === 0 ? 0x8000 : c;
  });
  const at = new Map<number, number>();
  boxes.forEach((box, i) => box.forEach((c) => at.set(c, i)));
  return { palette, index: (c) => at.get(c)! };
}

export interface CameraMasks {
  /** The camera's mask block, for the room file. */
  readonly block: Uint8Array;
  /** The objspr pak (an LZW-packed TIM), or undefined when the camera has no masks. */
  readonly pak?: Uint8Array;
  readonly sprites: readonly MaskSprite[];
}

/** Masks for one camera. `depth` is view-space Z per frame pixel, Infinity where nothing is in front. */
export function buildMasks(background: Image, depth: Float32Array): CameraMasks {
  if (background.width !== FRAME_W || background.height !== FRAME_H || depth.length !== FRAME_W * FRAME_H) {
    throw new Error(`masks need a ${FRAME_W}x${FRAME_H} frame`);
  }
  let sprites = cutSprites(depth);
  let tile = TILE;
  let at = pack(sprites);
  while ((sprites.length > MAX_SPRITES || !at) && tile < 64) {
    tile *= 2;
    sprites = cutSprites(depth, tile);
    at = pack(sprites);
  }
  if (!at || sprites.length > MAX_SPRITES) throw new Error(`${sprites.length} mask sprites do not fit one camera`);
  if (sprites.length === 0) return { block: new Uint8Array(4), sprites };

  // The texture: each sprite's frame pixels, transparent where nothing is in front.
  const isFront = (x: number, y: number) => Number.isFinite(depth[y * FRAME_W + x]!);
  const colorAt = (x: number, y: number) => {
    const i = (y * FRAME_W + x) * 3;
    return to555(background.rgb[i]!, background.rgb[i + 1]!, background.rgb[i + 2]!);
  };
  const used: number[] = [];
  sprites.forEach((s) => {
    for (let y = s.y; y < s.y + s.h; y++) for (let x = s.x; x < s.x + s.w; x++) if (isFront(x, y)) used.push(colorAt(x, y));
  });
  const { palette, index } = quantize(used, 255);
  const pixels = new Uint8Array(ATLAS * ATLAS);
  sprites.forEach((s, i) => {
    const { u, v } = at![i]!;
    for (let y = 0; y < s.h; y++) {
      for (let x = 0; x < s.w; x++) {
        const fx = s.x + x;
        const fy = s.y + y;
        pixels[(v + y) * ATLAS + u + x] = isFront(fx, fy) ? 1 + index(colorAt(fx, fy)) : 0;
      }
    }
  });
  const tim = new Uint8Array(20 + 512 + 12 + ATLAS * ATLAS);
  const t = new DataView(tim.buffer);
  t.setUint32(0, 0x10, true);
  t.setUint32(4, 0x09, true); // 8 bpp with a CLUT
  t.setUint32(8, 12 + 512, true);
  t.setUint16(12, 0, true);
  t.setUint16(14, 480, true);
  t.setUint16(16, 256, true);
  t.setUint16(18, 1, true);
  palette.forEach((c, i) => t.setUint16(20 + 2 * (i + 1), c, true));
  const img = 20 + 512;
  t.setUint32(img, 12 + ATLAS * ATLAS, true);
  t.setUint16(img + 4, 0, true);
  t.setUint16(img + 6, 0, true);
  t.setUint16(img + 8, ATLAS / 2, true);
  t.setUint16(img + 10, ATLAS, true);
  tim.set(pixels, img + 12);

  // The block: two groups, so every sprite's offset from its origin fits a byte.
  const groups = [sprites.map((s, i) => i).filter((i) => sprites[i]!.x < 256), sprites.map((s, i) => i).filter((i) => sprites[i]!.x >= 256)].filter((g) => g.length);
  const origins = groups.map((g) => ({ x: Math.min(...g.map((i) => sprites[i]!.x)), y: Math.min(...g.map((i) => sprites[i]!.y)) }));
  const block = new Uint8Array(4 + groups.length * 8 + sprites.length * 12);
  const b = new DataView(block.buffer);
  b.setInt32(0, groups.length, true);
  let p = 4;
  groups.forEach((g, gi) => {
    b.setUint16(p, g.length, true);
    b.setUint16(p + 2, TEX_BITS, true);
    b.setInt16(p + 4, origins[gi]!.x, true);
    b.setInt16(p + 6, origins[gi]!.y, true);
    p += 8;
  });
  groups.forEach((g, gi) => {
    for (const i of g) {
      const s = sprites[i]!;
      const { u, v } = at![i]!;
      b.setUint16(p, u | (v << 8), true);
      b.setUint16(p + 2, (s.x - origins[gi]!.x) | ((s.y - origins[gi]!.y) << 8), true);
      b.setUint16(p + 4, Math.min(s.depth, 0xffff), true);
      b.setUint16(p + 6, SPRITE_FLAGS, true);
      b.setUint16(p + 8, s.w, true);
      b.setUint16(p + 10, s.h, true);
      p += 12;
    }
  });
  return { block, pak: lzwPack(tim), sprites };
}

/** The objspr pak name for a camera: osp0<stage><room as two decimal digits><camera>.pak (Room.cpp load_room_bg_masks). */
export function maskPakName(stage: number, room: number, camera: number): string {
  return `OSP0${stage}${String(room).padStart(2, '0')}${camera}.pak`;
}
