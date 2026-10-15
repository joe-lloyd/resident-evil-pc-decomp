// Her key items' game models, from what models.py exports (models/<step>.json
// and .png): the model she turns over in her inventory, an ITEM_M2 .IVM, and
// the one lying in the room until she takes it, a TMD and TIM for the room's
// item model table (rdt.ts).
//
// Both are what RE1's own are (tools/dump_ivm.py): one TMD object of lit,
// textured, gouraud triangles (mode 0x34), and an 8-bit TIM, its CLUT one row
// at (0, 480). RE1's corners run clockwise seen from outside: the cross product
// of (v1 - v0) and (v2 - v0) points against the normal. The examined model is
// centred and RE1_VIEW_SIZE units across its longest side, as RE1's are; the
// one in the room is in millimetres, standing on y = 0 (up is -y).
import { readFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { readPng, type Image } from '../../harness/image.ts';

const here = path.dirname(fileURLToPath(import.meta.url));

type Vec3 = readonly [number, number, number];
type Corner = { readonly pos: Vec3; readonly normal: Vec3; readonly uv: readonly [number, number] };
type Triangle = readonly [Corner, Corner, Corner];

export interface ItemMesh {
  readonly step: string;
  readonly view: readonly Triangle[];
  readonly pickup: readonly Triangle[];
}

/** RE1's examined models are about this many units along their longest side (the knife's 5000, the others' 4500). */
const VIEW_SIZE = 4800;

function numbers(v: unknown, n: number, what: string): number[] {
  if (!Array.isArray(v) || v.length !== n || !v.every((x) => typeof x === 'number' && Number.isFinite(x))) throw new Error(`${what}: not ${n} numbers`);
  return v;
}

function triangles(v: unknown, what: string): Triangle[] {
  if (!Array.isArray(v)) throw new Error(`${what}: not a list of triangles`);
  return v.map((t, i): Triangle => {
    if (!Array.isArray(t) || t.length !== 3) throw new Error(`${what} ${i}: not three corners`);
    const corner = (c: unknown): Corner => {
      if (!Array.isArray(c) || c.length !== 3) throw new Error(`${what} ${i}: a corner is not [pos, normal, uv]`);
      const [x, y, z] = numbers(c[0], 3, `${what} ${i} position`);
      const [nx, ny, nz] = numbers(c[1], 3, `${what} ${i} normal`);
      const [u, w] = numbers(c[2], 2, `${what} ${i} uv`);
      return { pos: [x!, y!, z!], normal: [nx!, ny!, nz!], uv: [u!, w!] };
    };
    return [corner(t[0]), corner(t[1]), corner(t[2])];
  });
}

/** models/<step>.json, checked. */
export function parseItemMesh(json: unknown): ItemMesh {
  if (typeof json !== 'object' || json === null || !('step' in json) || typeof json.step !== 'string') throw new Error('item model: no step');
  if (!('view' in json) || !('pickup' in json)) throw new Error(`${json.step}: no view or pickup triangles`);
  return { step: json.step, view: triangles(json.view, `${json.step} view`), pickup: triangles(json.pickup, `${json.step} pickup`) };
}

/** The item's exported model and texture, if models.py has made it. */
export function readItemModel(step: string, dir = path.join(here, 'models')): { mesh: ItemMesh; texture: Image } | undefined {
  try {
    return { mesh: parseItemMesh(JSON.parse(readFileSync(path.join(dir, `${step}.json`), 'utf8'))), texture: readPng(path.join(dir, `${step}.png`)) };
  } catch (err) {
    if (err instanceof Error && 'code' in err && err.code === 'ENOENT') return undefined;
    throw err;
  }
}

type Rgb = [number, number, number];

/** Median cut: at most `colours` colours, and each pixel's index into them. */
export function quantize(img: Image, colours = 256): { palette: Rgb[]; index: Uint8Array } {
  const n = img.width * img.height;
  const px = (i: number, ch: number) => img.rgb[i * 3 + ch]!;
  let boxes: number[][] = [Array.from({ length: n }, (_, i) => i)];
  const range = (b: number[], ch: number) => {
    let lo = 255;
    let hi = 0;
    for (const i of b) {
      lo = Math.min(lo, px(i, ch));
      hi = Math.max(hi, px(i, ch));
    }
    return hi - lo;
  };
  while (boxes.length < colours) {
    let best = -1;
    let bestCh = 0;
    let bestRange = 0;
    boxes.forEach((b, k) => {
      for (let ch = 0; ch < 3; ch++) {
        const r = range(b, ch);
        if (r > bestRange) [best, bestCh, bestRange] = [k, ch, r];
      }
    });
    if (best < 0) break;
    const b = boxes[best]!.sort((x, y) => px(x, bestCh) - px(y, bestCh));
    const mid = b.length >> 1;
    boxes = [...boxes.slice(0, best), b.slice(0, mid), b.slice(mid), ...boxes.slice(best + 1)];
  }
  const index = new Uint8Array(n);
  const palette = boxes.map((b, k): Rgb => {
    let [r, g, bl] = [0, 0, 0];
    for (const i of b) {
      index[i] = k;
      r += px(i, 0);
      g += px(i, 1);
      bl += px(i, 2);
    }
    return [Math.round(r / b.length), Math.round(g / b.length), Math.round(bl / b.length)];
  });
  return { palette, index };
}

/** An 8-bit TIM of `img`, its CLUT one row at (0, 480). No colour is 0x0000, which the game draws see-through. */
export function tim8(img: Image): Uint8Array {
  if (img.width % 2) throw new Error('an 8-bit TIM is a whole number of 16-bit words wide');
  const { palette, index } = quantize(img);
  const clutLen = 12 + 256 * 2;
  const imgLen = 12 + img.width * img.height;
  const out = new Uint8Array(8 + clutLen + imgLen);
  const v = new DataView(out.buffer);
  v.setUint32(0, 0x10, true);
  v.setUint32(4, 8 | 1, true);
  v.setUint32(8, clutLen, true);
  v.setUint16(12, 0, true);
  v.setUint16(14, 480, true);
  v.setUint16(16, 256, true);
  v.setUint16(18, 1, true);
  palette.forEach(([r, g, b], i) => {
    const c = (r >> 3) | ((g >> 3) << 5) | ((b >> 3) << 10);
    v.setUint16(20 + i * 2, c || 0x0421, true);
  });
  for (let i = palette.length; i < 256; i++) v.setUint16(20 + i * 2, 0x0421, true);
  const at = 8 + clutLen;
  v.setUint32(at, imgLen, true);
  v.setUint16(at + 4, 0, true);
  v.setUint16(at + 6, 0, true);
  v.setUint16(at + 8, img.width / 2, true);
  v.setUint16(at + 10, img.height, true);
  out.set(index, at + 12);
  return out;
}

/** Half the width, each pixel the mean of two: the room's models have 128-pixel-wide textures. */
export function halfWidth(img: Image): Image {
  const w = img.width >> 1;
  const rgb = new Uint8Array(w * img.height * 3);
  for (let y = 0; y < img.height; y++)
    for (let x = 0; x < w; x++)
      for (let ch = 0; ch < 3; ch++) {
        const a = img.rgb[(y * img.width + 2 * x) * 3 + ch]!;
        const b = img.rgb[(y * img.width + 2 * x + 1) * 3 + ch]!;
        rgb[(y * w + x) * 3 + ch] = (a + b + 1) >> 1;
      }
  return { width: w, height: img.height, rgb };
}

/**
 * One TMD object of `tris`, each point through `place` into game units and
 * each normal through `turn` (the same turn, without the move and scale), the
 * texture `w` x `h` pixels. Blender's corners run anticlockwise seen from
 * outside; RE1's the other way, so each triangle's last two swap.
 */
export function tmd(tris: readonly Triangle[], place: (p: Vec3) => Vec3, w: number, h: number, turn: (n: Vec3) => Vec3 = ([x, y, z]) => [x, -z, y]): Uint8Array {
  const verts: Vec3[] = [];
  const normals: Vec3[] = [];
  const keyed = (list: Vec3[], seen: Map<string, number>, p: Vec3) => {
    const k = p.join(',');
    let i = seen.get(k);
    if (i === undefined) {
      i = list.length;
      list.push(p);
      seen.set(k, i);
    }
    return i;
  };
  const vSeen = new Map<string, number>();
  const nSeen = new Map<string, number>();
  const int16 = (x: number) => Math.max(-32768, Math.min(32767, Math.round(x)));
  const prims = tris.map((t) =>
    [t[0], t[2], t[1]].map((c) => {
      const p = place(c.pos);
      const n = turn(c.normal);
      const len = Math.hypot(...n) || 1;
      return {
        v: keyed(verts, vSeen, [int16(p[0]), int16(p[1]), int16(p[2])]),
        n: keyed(normals, nSeen, [int16((n[0] / len) * 4096), int16((n[1] / len) * 4096), int16((n[2] / len) * 4096)]),
        u: Math.max(0, Math.min(w - 1, Math.round(c.uv[0] * w - 0.5))),
        t: Math.max(0, Math.min(h - 1, Math.round((1 - c.uv[1]) * h - 0.5))),
      };
    }),
  );
  const primTop = 28;
  const vertTop = primTop + prims.length * 28;
  const normalTop = vertTop + verts.length * 8;
  const out = new Uint8Array(12 + normalTop + normals.length * 8);
  const v = new DataView(out.buffer);
  v.setUint32(0, 0x41, true);
  v.setUint32(4, 0, true);
  v.setUint32(8, 1, true);
  [vertTop, verts.length, normalTop, normals.length, primTop, prims.length, 0].forEach((x, i) => v.setUint32(12 + i * 4, x, true));
  prims.forEach((c, i) => {
    const at = 12 + primTop + i * 28;
    v.setUint32(at, 0x34000609, true);
    const [a, b, d] = [c[0]!, c[1]!, c[2]!];
    out.set([a.u, a.t], at + 4);
    v.setUint16(at + 6, 0x7800, true); // CLUT at (0, 480)
    out.set([b.u, b.t], at + 8);
    v.setUint16(at + 10, 0x0080, true); // texture page 0, 8-bit
    out.set([d.u, d.t], at + 12);
    [a.n, a.v, b.n, b.v, d.n, d.v].forEach((x, k) => v.setUint16(at + 16 + k * 2, x, true));
  });
  verts.forEach((p, i) => p.forEach((x, k) => v.setInt16(12 + vertTop + i * 8 + k * 2, x, true)));
  normals.forEach((p, i) => p.forEach((x, k) => v.setInt16(12 + normalTop + i * 8 + k * 2, x, true)));
  return out;
}

/**
 * The model she turns over examining the item: its TIM, then its TMD, centred
 * and VIEW_SIZE across. The viewer looks along x, so it is turned as RE1's
 * are (the knife is 700 units in x, 3000 in y, 5000 in z): its thinnest side
 * along x, facing her, its longest along z, across the screen. An item that
 * stands keeps its height up the screen instead.
 */
export function itemView(mesh: ItemMesh, texture: Image): Uint8Array {
  const pts = mesh.view.flatMap((t) => t.map((c) => c.pos));
  const lo = [0, 1, 2].map((k) => Math.min(...pts.map((p) => p[k]!)));
  const hi = [0, 1, 2].map((k) => Math.max(...pts.map((p) => p[k]!)));
  const mid = lo.map((l, k) => (l + hi[k]!) / 2);
  const span = hi.map((h, k) => h - lo[k]!);
  const s = VIEW_SIZE / Math.max(...span);
  // Game axes x, y, z take the item's thinnest, middle and longest sides,
  // but an item that stands (a can: its height is not its thinnest side)
  // stays standing, its height up the screen. y, up, is negated. x is negated
  // too unless the reordering is odd, so that the whole is a turn, not a
  // mirror, and keeps the triangles' winding.
  const bySize = [0, 1, 2].sort((a, b) => span[a]! - span[b]!);
  const [thin, middle, long] = bySize[0] === 2 ? bySize : [...bySize.filter((k) => k !== 2).slice(0, 1), 2, ...bySize.filter((k) => k !== 2).slice(1)];
  const odd = (thin === 1 && middle === 0) || (thin === 0 && middle === 2) || (thin === 2 && middle === 1);
  const axes = (c: readonly number[]): Vec3 => [(odd ? 1 : -1) * c[thin]!, -c[middle]!, c[long]!];
  const model = tmd(mesh.view, (p) => axes(p.map((x, k) => (x - mid[k]!) * s)), texture.width, texture.height, axes);
  const tim = tim8(texture);
  const out = new Uint8Array(tim.length + model.length);
  out.set(tim);
  out.set(model, tim.length);
  return out;
}

/** The model lying in the room until she takes it, in millimetres, standing on the floor. */
export function itemPickup(mesh: ItemMesh, texture: Image): { tmd: Uint8Array; tim: Uint8Array } {
  const half = halfWidth(texture);
  return { tmd: tmd(mesh.pickup, ([x, y, z]) => [x * 1000, -z * 1000, y * 1000], half.width, half.height), tim: tim8(half) };
}

/** The item's own model lying in the room, from what models.py made. */
export function ownPickup(step: string): { tmd: Uint8Array; tim: Uint8Array } {
  const m = readItemModel(step);
  if (!m) throw new Error(`items/models/${step}.json is missing: run items/render-items.ts`);
  return itemPickup(m.mesh, m.texture);
}

/**
 * Which ITEM_M2 file an item's examined model is: g_ItemModelFileNames (the
 * decomp's src/game/MenuData.cpp) at its image type, which is its icon row + 1
 * (iconRows, from g_ItemImageLookupTable).
 */
export function itemViewFiles(menuDataCpp: string, iconRow: (id: number) => number): (id: number) => string {
  const head = 'g_ItemModelFileNames[75][8] = {';
  const at = menuDataCpp.indexOf(head);
  if (at < 0) throw new Error('src/game/MenuData.cpp: no g_ItemModelFileNames');
  const body = menuDataCpp.slice(at + head.length, menuDataCpp.indexOf('};', at)).replace(/\/\/[^\n]*/g, '');
  const names = [...body.matchAll(/"([^"]*)"/g)].map((m) => m[1]!);
  return (id) => {
    const name = names[iconRow(id) + 1];
    if (!name) throw new Error(`item ${id} has no examined model`);
    return `${name.toUpperCase()}.IVM`;
  };
}

/** The decomp's src/game/MenuData.cpp, for the model file names. */
export const menuDataCpp = () => readFileSync(path.join(here, '..', '..', '..', 'src', 'game', 'MenuData.cpp'), 'utf8');
