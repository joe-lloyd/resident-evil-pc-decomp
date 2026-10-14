// Fit a skin we paint to a model's texture: a 256x256 RGB image in the
// model's own texture layout becomes 8 bpp indices and two 256-colour
// palettes, one per 128-texel half of the sheet (rowAt in emd.ts), the way
// RE1's character textures are stored.
import type { Image } from '../../harness/image.ts';
import { rowAt, type Texture } from './emd.ts';
import { to555 } from '../pak.ts';

const SIDE = 256;
const HALF = SIDE / 2;
const COLOURS = 256;

/**
 * 15-bit colour 0 is see-through on the PlayStation, so pure black is drawn
 * one step lighter.
 */
const opaque555 = (r: number, g: number, b: number) => to555(r, g, b) || 0x0421;

/** Split colours into at most `count` boxes by their widest channel, and average each box. */
function medianCut(colours: Map<number, number>, count: number): number[] {
  type Box = { colours: number[] };
  const channel = (c: number, k: number) => (c >> (k * 5)) & 31;
  const spread = (box: Box) =>
    [0, 1, 2].map((k) => {
      const vs = box.colours.map((c) => channel(c, k));
      return { k, range: Math.max(...vs) - Math.min(...vs) };
    }).sort((a, b) => b.range - a.range)[0]!;
  let boxes: Box[] = [{ colours: [...colours.keys()] }];
  while (boxes.length < count) {
    const splittable = boxes.filter((b) => b.colours.length > 1);
    if (!splittable.length) break;
    const box = splittable.sort((a, b) => spread(b).range * b.colours.length - spread(a).range * a.colours.length)[0]!;
    const { k } = spread(box);
    const sorted = [...box.colours].sort((a, b) => channel(a, k) - channel(b, k));
    const mid = sorted.length >> 1;
    boxes = [...boxes.filter((b) => b !== box), { colours: sorted.slice(0, mid) }, { colours: sorted.slice(mid) }];
  }
  return boxes.map((box) => {
    const weight = box.colours.reduce((n, c) => n + colours.get(c)!, 0);
    const avg = [0, 1, 2].map((k) => Math.round(box.colours.reduce((n, c) => n + channel(c, k) * colours.get(c)!, 0) / weight));
    return avg[0]! | (avg[1]! << 5) | (avg[2]! << 10) || 0x0421;
  });
}

const distance = (a: number, b: number) => [0, 1, 2].reduce((n, k) => n + (((a >> (k * 5)) & 31) - ((b >> (k * 5)) & 31)) ** 2, 0);

/** Our skin as the model's texture: each half gets its own palette of the colours it uses. */
export function fitSkin(texture: Texture, skin: Image): Texture {
  if (skin.width !== SIDE || skin.height !== SIDE) throw new Error(`a skin is ${SIDE}x${SIDE}, got ${skin.width}x${skin.height}`);
  if (texture.palettes.length !== 2) throw new Error('a skin fits a texture with one palette row per half');
  const c555 = Uint16Array.from({ length: SIDE * SIDE }, (_, i) => opaque555(skin.rgb[i * 3]!, skin.rgb[i * 3 + 1]!, skin.rgb[i * 3 + 2]!));
  const pixels = new Uint8Array(SIDE * SIDE);
  const palettes = [0, 1].map((row) => {
    const used = new Map<number, number>();
    for (let i = 0; i < SIDE * SIDE; i++) if (rowAt(i % SIDE) === row) used.set(c555[i]!, (used.get(c555[i]!) ?? 0) + 1);
    const palette = used.size <= COLOURS ? [...used.keys()] : medianCut(used, COLOURS);
    const index = new Map<number, number>();
    const nearest = (c: number) => {
      let at = index.get(c);
      if (at === undefined) {
        at = palette.reduce((best, p, k) => (distance(p, c) < distance(palette[best]!, c) ? k : best), 0);
        index.set(c, at);
      }
      return at;
    };
    for (let y = 0; y < SIDE; y++) for (let x = row * HALF; x < (row + 1) * HALF; x++) pixels[y * SIDE + x] = nearest(c555[y * SIDE + x]!);
    return Uint16Array.from({ length: COLOURS }, (_, k) => palette[k] ?? 0);
  });
  return { palettes, pixels };
}
