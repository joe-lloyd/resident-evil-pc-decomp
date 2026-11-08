// The brushes the skins paint with: noise, cloth, the light RE1 paints into
// its textures, and a face. A brush is a function of what a texel covers
// (paint.ts), in body axes and game units.
import type { Rgb, Texel } from './paint.ts';

export const clamp = (v: number, lo = 0, hi = 1) => Math.max(lo, Math.min(hi, v));
export const smooth = (e0: number, e1: number, v: number) => {
  const t = clamp((v - e0) / (e1 - e0));
  return t * t * (3 - 2 * t);
};
export const mix = (a: Rgb, b: Rgb, t: number): Rgb => [a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, a[2] + (b[2] - a[2]) * t];
export const scale = (c: Rgb, k: number): Rgb => [c[0] * k, c[1] * k, c[2] * k];

export function hash(x: number, y: number, z: number): number {
  let h = (x * 374761393 + y * 668265263 + z * 2147483647) | 0;
  h = Math.imul(h ^ (h >>> 13), 1274126177);
  return ((h ^ (h >>> 16)) >>> 0) / 4294967296;
}

/** Smooth value noise in 0..1 with features about `size` game units across. */
export function noise(p: readonly number[], size: number): number {
  const [x, y, z] = [p[0]! / size, p[1]! / size, p[2]! / size];
  const [ix, iy, iz] = [Math.floor(x), Math.floor(y), Math.floor(z)];
  const [fx, fy, fz] = [x - ix, y - iy, z - iz].map((f) => f * f * (3 - 2 * f));
  const v = (dx: number, dy: number, dz: number) => hash(ix + dx, iy + dy, iz + dz);
  const lerp = (a: number, b: number, t: number) => a + (b - a) * t;
  return lerp(
    lerp(lerp(v(0, 0, 0), v(1, 0, 0), fx!), lerp(v(0, 1, 0), v(1, 1, 0), fx!), fy!),
    lerp(lerp(v(0, 0, 1), v(1, 0, 1), fx!), lerp(v(0, 1, 1), v(1, 1, 1), fx!), fy!),
    fz!,
  );
}

/** Two octaves: broad variation with a finer grain on top. */
export const grain = (p: readonly number[], size: number) => 0.65 * noise(p, size) + 0.35 * noise(p, size / 3.1);

/** The light painted into RE1's textures: from above and a little in front, never black. */
export const lit = (t: Texel) => 0.72 + 0.2 * t.normal[1] + 0.08 * t.normal[2];

/** Cloth: its colour, mottled and lit, with darker creases. */
export function cloth(t: Texel, base: Rgb, size = 90, depth = 0.16): Rgb {
  const g = grain(t.at, size);
  const crease = smooth(0.62, 0.8, noise([t.at[0], t.at[1] * 2.2, t.at[2]], size * 1.4)) * 0.18;
  return scale(base, lit(t) * (1 - depth / 2 + depth * g) * (1 - crease));
}

/** The facing of a texel on the front of the head: true when it looks forward. */
export const front = (t: Texel, at = 0.35) => t.normal[2] > at;

export interface Face {
  /** Heights of the features, game units from the floor. */
  readonly chin: number;
  readonly mouth: number;
  readonly nose: number;
  readonly eyes: number;
  readonly brows: number;
  /** Half the distance between the eyes. */
  readonly eyeX: number;
  readonly skin: Rgb;
  readonly lips: Rgb;
  readonly iris: Rgb;
  readonly brow: Rgb;
  /** Eye opening, half-height and half-width. */
  readonly eyeH: number;
  readonly eyeW: number;
  readonly browThick: number;
  /** Lines and sag of age, 0..1. */
  readonly age: number;
}

/** A face: skin shaded by the head's shape, eyes, brows, nose, mouth. */
export function face(t: Texel, f: Face): Rgb {
  const [x, y] = t.at;
  const ax = Math.abs(x);
  // Skin, darker where it turns away, warmer on the nose and cheeks.
  let c = scale(f.skin, lit(t) * (0.92 + 0.12 * grain(t.at, 30)));
  const cheek = Math.exp(-((ax - f.eyeX * 1.1) ** 2 + (y - (f.nose + f.mouth) / 2) ** 2) / (2 * (f.eyeX * 0.55) ** 2));
  c = mix(c, scale([200, 95, 80], lit(t)), 0.18 * cheek);
  if (!front(t, 0.2)) return c;

  // Brows.
  const browY = f.brows - (ax - f.eyeX) ** 2 * 0.004;
  if (ax > f.eyeX * 0.3 && ax < f.eyeX * 1.75 && Math.abs(y - browY) < f.browThick * (1.15 - ax / (f.eyeX * 2.6))) {
    return mix(c, f.brow, 0.85 * (0.75 + 0.25 * noise(t.at, 6)));
  }
  // Eyes: an almond opening, a dark upper lid, the iris and pupil.
  const ex = (ax - f.eyeX) / f.eyeW;
  const ey = (y - f.eyes) / f.eyeH;
  const almond = ex * ex + ey * ey * (1 + 0.6 * ex * ex);
  if (almond < 1) {
    const iris = Math.hypot((ax - f.eyeX) / (f.eyeH * 1.05), ey);
    if (iris < 0.45) return [24, 18, 16];
    if (iris < 1) return mix(f.iris, scale(f.iris, 0.6), iris);
    return mix([215, 205, 195], [170, 150, 140], Math.abs(ex));
  }
  if (almond < 1.6 && ey > 0) return mix(c, [45, 30, 25], 0.75);
  if (almond < 2.2 && ey < 0) c = scale(c, 0.86 - 0.1 * f.age);
  // Lines at the corners of the eyes and across the brow, with age.
  if (f.age > 0 && ax > f.eyeX + f.eyeW && ax < f.eyeX + f.eyeW * 1.9 && Math.abs(y - f.eyes) < f.eyeH * 1.8) {
    if (Math.sin((y - f.eyes) * 0.55 + ax * 0.15) > 0.82) c = scale(c, 1 - 0.18 * f.age);
  }
  if (f.age > 0 && y > browY + f.browThick * 1.2 && ax < f.eyeX * 1.4 && Math.sin(y * 0.28) > 0.9) c = scale(c, 1 - 0.12 * f.age);
  // Nose: a lit ridge, shaded sides, the nostrils.
  if (y > f.nose - 8 && y < f.eyes - f.eyeH && ax < f.eyeX * 0.25) c = scale(c, 1.06);
  if (Math.hypot(ax - f.eyeX * 0.28, (y - (f.nose - 8)) * 1.6) < f.eyeX * 0.12) return scale(c, 0.55);
  if (y > f.nose - 12 && y < f.nose + 30 && ax > f.eyeX * 0.27 && ax < f.eyeX * 0.42) c = scale(c, 1 - 0.12 * Math.max(f.age, 0.4));
  // Mouth: the parting line and the lips around it.
  const lipW = f.eyeX * 0.85;
  if (ax < lipW) {
    const curve = f.mouth - (ax / lipW) ** 2 * 4;
    const d = y - curve;
    if (Math.abs(d) < 2.5) return mix(c, [60, 30, 28], 0.85);
    const lip = d > 0 ? 7 : 10;
    if (Math.abs(d) < lip * (1 - (ax / lipW) ** 2)) c = mix(c, scale(f.lips, lit(t)), d > 0 ? 0.55 : 0.7);
  }
  // Under the lower lip and the chin's shadow.
  if (ax < f.eyeX * 0.5 && y < f.mouth - 12 && y > f.mouth - 22) c = scale(c, 0.9);
  return c;
}
