// Her inventory icons: the player's own item sheet (DATA/ITEM_ALL.PIX) with
// the rows of the donors her key items stand in for redrawn from the renders
// in items/icons/ (icons.py), named by the plan step that gives the item. A
// key item with no render keeps its donor's icon: the keys look like keys.
//
// The sheet is 40 x 30 icons, one 1200-byte row each, 8 bits an index into
// STATUS.TIM's third CLUT row (dump_item_pix.py). Which row an item draws is
// g_ItemImageLookupTable[id * 4] - 1 (src/Globals.cpp, LoadHeldItemsImages).
// Each render is shrunk to the icon's size, laid over the sheet's navy
// ground (each pixel's commonest colour over every icon on the sheet) and matched to
// the palette's nearest colour.
import { existsSync, readFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { readPng, type Image } from '../../harness/image.ts';
import { KEY_ITEMS } from './items.ts';

const here = path.dirname(fileURLToPath(import.meta.url));
const W = 40;
const H = 30;
const ROW = W * H;

type Rgb = readonly [number, number, number];

/** STATUS.TIM's CLUT row `row` as RGB, and which entries are 0x0000 (drawn see-through). */
export function readClut(tim: Uint8Array, row = 2): { rgb: Rgb[]; clear: boolean[] } {
  const v = new DataView(tim.buffer, tim.byteOffset, tim.byteLength);
  if (v.getUint32(0, true) !== 0x10 || !(v.getUint32(4, true) & 8)) throw new Error('STATUS.TIM: not a TIM with a CLUT');
  const w = v.getUint16(16, true);
  const h = v.getUint16(18, true);
  if (row >= h) throw new Error(`STATUS.TIM: no CLUT row ${row}`);
  const rgb: Rgb[] = [];
  const clear: boolean[] = [];
  for (let i = 0; i < w; i++) {
    const c = v.getUint16(20 + (row * w + i) * 2, true);
    const five = (n: number) => ((n & 31) << 3) | ((n & 31) >> 2);
    rgb.push([five(c), five(c >> 5), five(c >> 10)]);
    clear.push(c === 0);
  }
  return { rgb, clear };
}

/** g_ItemImageLookupTable from the decomp's source, the table the game itself uses. */
export function iconRows(globalsCpp: string): (id: number) => number {
  const head = 'g_ItemImageLookupTable[459] = {';
  const at = globalsCpp.indexOf(head);
  if (at < 0) throw new Error('src/Globals.cpp: no g_ItemImageLookupTable');
  const body = globalsCpp.slice(at + head.length, globalsCpp.indexOf('};', at)).replace(/\/\/[^\n]*|\/\*[\s\S]*?\*\//g, '');
  const table = [...body.matchAll(/0x[0-9a-fA-F]+|\d+/g)].map((m) => Number(m[0]));
  return (id) => {
    const r = table[id * 4];
    if (r === undefined || r === 0) throw new Error(`item ${id} has no icon`);
    return r - 1;
  };
}

/** Shrink a render to the icon's size, averaging colour by coverage. */
function shrink(img: Image): { rgb: Float64Array; alpha: Float64Array } {
  if (img.width !== W * 4 || img.height !== H * 4) throw new Error(`icon renders are ${W * 4} x ${H * 4}, not ${img.width} x ${img.height}`);
  const rgb = new Float64Array(ROW * 3);
  const alpha = new Float64Array(ROW);
  for (let y = 0; y < H; y++)
    for (let x = 0; x < W; x++) {
      let a = 0;
      const c = [0, 0, 0];
      for (let dy = 0; dy < 4; dy++)
        for (let dx = 0; dx < 4; dx++) {
          const p = (y * 4 + dy) * img.width + x * 4 + dx;
          const k = (img.alpha?.[p] ?? 255) / 255;
          a += k;
          for (let ch = 0; ch < 3; ch++) c[ch]! += img.rgb[p * 3 + ch]! * k;
        }
      const i = y * W + x;
      alpha[i] = a / 16;
      for (let ch = 0; ch < 3; ch++) rgb[i * 3 + ch] = a > 0 ? c[ch]! / a : 0;
    }
  return { rgb, alpha };
}

function nearest(palette: Rgb[], clear: boolean[], c: Rgb): number {
  let best = -1;
  let bestD = Infinity;
  for (let i = 0; i < palette.length; i++) {
    if (clear[i]) continue;
    const p = palette[i]!;
    const d = (p[0] - c[0]) ** 2 + (p[1] - c[1]) ** 2 + (p[2] - c[2]) ** 2;
    if (d < bestD) [best, bestD] = [i, d];
  }
  return best;
}

/** The sheet with her icons in: `sheet` and `statusTim` are the player's files. */
export function buildIconSheet(sheet: Uint8Array, statusTim: Uint8Array, globalsCpp: string, icons = path.join(here, 'icons')): Uint8Array {
  if (sheet.length % ROW) throw new Error(`ITEM_ALL.PIX is ${sheet.length} bytes, not whole ${ROW}-byte icons`);
  const { rgb: palette, clear } = readClut(statusTim);
  const rows = sheet.length / ROW;
  // The navy ground: each pixel's commonest colour over every icon on the
  // sheet. The items differ from icon to icon, the ground repeats.
  const ground: Rgb[] = [];
  for (let i = 0; i < ROW; i++) {
    const count = new Map<number, number>();
    for (let r = 0; r < rows; r++) count.set(sheet[r * ROW + i]!, (count.get(sheet[r * ROW + i]!) ?? 0) + 1);
    const common = [...count].sort((a, b) => b[1] - a[1])[0]![0];
    ground.push(palette[common]!);
  }
  const row = iconRows(globalsCpp);
  const out = Uint8Array.from(sheet);
  for (const k of KEY_ITEMS) {
    const file = path.join(icons, `${k.step}.png`);
    if (!existsSync(file)) continue;
    const { rgb, alpha } = shrink(readPng(file));
    const at = row(k.id) * ROW;
    for (let i = 0; i < ROW; i++) {
      const a = alpha[i]!;
      const g = ground[i]!;
      const mix = (ch: number) => rgb[i * 3 + ch]! * a + g[ch]! * (1 - a);
      out[at + i] = nearest(palette, clear, [mix(0), mix(1), mix(2)]);
    }
  }
  return out;
}

/** The decomp's src/Globals.cpp, for the icon table. */
export const globalsCpp = () => readFileSync(path.join(here, '..', '..', '..', 'src', 'Globals.cpp'), 'utf8');
