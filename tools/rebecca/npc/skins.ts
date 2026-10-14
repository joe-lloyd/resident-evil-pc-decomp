// The two people's skins, painted from what each texel covers (paint.ts).
// Positions are body axes in game units: x to the character's right, y up
// from the floor, z forward. Landmark heights come from each model's own
// head and body (docs/REBECCA_NPC.md); nothing is taken from the game's art.
import type { Vec3 } from './emd.ts';
import type { Rgb, Texel } from './paint.ts';

// ---------------------------------------------------------------------------
// Helpers

const clamp = (v: number, lo = 0, hi = 1) => Math.max(lo, Math.min(hi, v));
const smooth = (e0: number, e1: number, v: number) => {
  const t = clamp((v - e0) / (e1 - e0));
  return t * t * (3 - 2 * t);
};
const mix = (a: Rgb, b: Rgb, t: number): Rgb => [a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, a[2] + (b[2] - a[2]) * t];
const scale = (c: Rgb, k: number): Rgb => [c[0] * k, c[1] * k, c[2] * k];

function hash(x: number, y: number, z: number): number {
  let h = (x * 374761393 + y * 668265263 + z * 2147483647) | 0;
  h = Math.imul(h ^ (h >>> 13), 1274126177);
  return ((h ^ (h >>> 16)) >>> 0) / 4294967296;
}

/** Smooth value noise in 0..1 with features about `size` game units across. */
function noise(p: readonly number[], size: number): number {
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
const grain = (p: readonly number[], size: number) => 0.65 * noise(p, size) + 0.35 * noise(p, size / 3.1);

/** The light painted into RE1's textures: from above and a little in front, never black. */
const lit = (t: Texel) => 0.72 + 0.2 * t.normal[1] + 0.08 * t.normal[2];

/** Cloth: its colour, mottled and lit, with darker creases. */
function cloth(t: Texel, base: Rgb, size = 90, depth = 0.16): Rgb {
  const g = grain(t.at, size);
  const crease = smooth(0.62, 0.8, noise([t.at[0], t.at[1] * 2.2, t.at[2]], size * 1.4)) * 0.18;
  return scale(base, lit(t) * (1 - depth / 2 + depth * g) * (1 - crease));
}

/** Distance from p to the segment a-b in the x-y plane. */
function toSegment(px: number, py: number, ax: number, ay: number, bx: number, by: number): number {
  const [dx, dy] = [bx - ax, by - ay];
  const k = clamp(((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy));
  return Math.hypot(px - ax - k * dx, py - ay - k * dy);
}

/** The facing of a texel on the front of the head: true when it looks forward. */
const front = (t: Texel, at = 0.35) => t.normal[2] > at;

interface Face {
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
function face(t: Texel, f: Face): Rgb {
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
  if (y > f.nose - 12 && y < f.nose + 30 && ax > f.eyeX * 0.27 && ax < f.eyeX * 0.42) c = scale(c, 0.88);
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

// ---------------------------------------------------------------------------
// Hal: heavyset, fifties, grey stubble, a navy Arklay Skyway work jacket with
// a patch, a cap, brown canvas trousers, work boots. The bite on his right
// forearm is bandaged and bleeding through; his left forearm has its own
// place on the sheet (island.ts) so the bandage shows on one arm only.

const NAVY: Rgb = [38, 48, 78];
const CANVAS: Rgb = [112, 84, 52];
const HAL_SKIN: Rgb = [196, 138, 108];
const GREY_HAIR: Rgb = [150, 146, 140];

const halFace: Face = {
  chin: 2680, mouth: 2738, nose: 2795, eyes: 2868, brows: 2905, eyeX: 42,
  skin: HAL_SKIN, lips: [135, 70, 62], iris: [80, 95, 110], brow: [120, 116, 110],
  eyeH: 6, eyeW: 15, browThick: 10, age: 1,
};

function halHead(t: Texel): Rgb {
  const [x, y, z] = t.at;
  const ax = Math.abs(x);
  // The cap: navy, its crown seams, the Skyway patch on the front, and the
  // shadow of its brim across the top of the brow.
  const capLine = 2962 - smooth(60, -200, z) * 25;
  if (y > capLine) {
    let c = cloth(t, NAVY, 40, 0.2);
    if (Math.abs(x) < 4 || Math.abs(Math.atan2(x, z) - 1.2) < 0.03 || Math.abs(Math.atan2(x, z) + 1.2) < 0.03) c = scale(c, 0.7);
    if (z > 40 && Math.hypot(x, (y - 3010) * 1.3) < 34) {
      const r = Math.hypot(x, (y - 3010) * 1.3);
      if (r > 29) return [200, 190, 160];
      // A white peak and the cable line across a sky-blue disc.
      if (y < 3000 + (24 - Math.abs(x)) * 0.9 && y > 2992) return [235, 235, 230];
      if (Math.abs(y - 3018 + x * 0.3) < 1.6) return [40, 40, 45];
      return [95, 140, 185];
    }
    if (y < capLine + 12 && z > 30) c = scale(c, 0.65);
    return c;
  }
  // Short grey hair at the back and sides under the cap.
  if ((z < 20 && y > 2760) || (ax > 98 && y > 2830 && z < 60)) {
    return scale(mix(GREY_HAIR, [95, 92, 88], noise([x * 3, y, z * 3], 10)), lit(t));
  }
  let c = face(t, halFace);
  // The brim's shadow on the forehead.
  if (y > capLine - 18) c = scale(c, 0.78);
  // Grey stubble over the jaw, cheeks and lip.
  const jaw = y < 2788 && y > 2640 && z > -60 && !(Math.abs(y - (halFace.mouth - (ax / 36) ** 2 * 4)) < 7 && ax < 30);
  if (jaw) {
    const density = y < 2770 || ax < 30 ? 0.6 : 0.35;
    if (hash(Math.round(x / 3), Math.round(y / 3), Math.round(z / 3)) < density) c = mix(c, [130, 125, 120], 0.55);
  }
  // The neck under the jaw.
  if (y < 2680 && z < 60) c = scale(c, 0.85);
  return c;
}

function halJacket(t: Texel): Rgb {
  const [x, y, z] = t.at;
  const ax = Math.abs(x);
  // Brown corduroy collar round the neck, and the flannel shirt in the open neck.
  if (y > 2610 && ax < 150) {
    if (z > 40 && ax < (y - 2600) * 0.9 && y > 2640) {
      const check = (Math.floor((x + 400) / 14) + Math.floor(y / 14)) % 2;
      return scale(check ? [150, 40, 35] : [60, 25, 25], lit(t));
    }
    const rib = Math.sin(x * 0.5) > 0.3 ? 1 : 0.88;
    return scale([110, 72, 45], lit(t) * rib);
  }
  let c = cloth(t, NAVY);
  // Ribbed hem at the waist.
  if (y < 1990) c = scale(c, Math.sin(x * 0.45) > 0 ? 0.82 : 0.72);
  // The zip down the front.
  if (z > 60 && ax < 5) return mix(c, [150, 150, 145], 0.8);
  if (z > 60 && ax < 9) c = scale(c, 0.8);
  // Chest pockets with flaps, and the Skyway patch on his left chest.
  if (z > 60) {
    const px = ax - 120;
    if (Math.abs(px) < 62 && y > 2330 && y < 2470 && (Math.abs(px) > 58 || y < 2334 || Math.abs(y - 2440) < 3)) c = scale(c, 0.72);
    if (x < 0 && Math.hypot(x + 120, (y - 2510) * 1.5) < 46) {
      const r = Math.hypot(x + 120, (y - 2510) * 1.5);
      if (r > 39) return [205, 195, 165];
      if (y < 2505 + (30 - Math.abs(x + 120)) * 0.8 && y > 2490) return [240, 240, 235];
      if (Math.abs(y - 2522 + (x + 120) * 0.3) < 2) return [35, 35, 40];
      return [95, 140, 185];
    }
  }
  return c;
}

function halSleeve(t: Texel): Rgb {
  const [x, y] = t.at;
  let c = cloth(t, NAVY);
  // A round Skyway patch on the outside of each shoulder.
  const out = Math.abs(x) - 470;
  if (Math.hypot(out * 1.2, y - 2470) < 38 && t.normal[0] * Math.sign(x) > 0.3) {
    return Math.hypot(out * 1.2, y - 2470) > 32 ? [205, 195, 165] : [95, 140, 185];
  }
  if (y < 2140) c = scale(c, 0.85);
  return c;
}

/** His bitten right forearm: the sleeve pushed up, gauze wound round, blood through it. */
function halBitten(t: Texel): Rgb {
  const [x, y, z] = t.at;
  if (y > 2085) return scale(cloth(t, NAVY), y < 2110 ? 0.75 : 1);
  if (y < 1735) return scale(HAL_SKIN, lit(t) * 0.95);
  const wrap = Math.sin((y + Math.atan2(z, x - 460) * 40) * 0.22);
  let c = scale(mix([228, 222, 205], [196, 188, 170], wrap * 0.5 + 0.5), lit(t));
  // Blood soaked through on the inside of the arm, darkest at the bite.
  const bite = Math.hypot((y - 1900) * 0.9, (z + 60) * 1.4);
  const soak = smooth(110, 40, bite + (noise(t.at, 25) - 0.5) * 70);
  c = mix(c, mix([150, 28, 22], [92, 14, 12], smooth(0.4, 1, soak)), soak);
  // A run of blood down toward the wrist.
  if (Math.abs(z + 60 + Math.sin(y * 0.05) * 6) < 7 && y < 1880 && y > 1760) c = mix(c, [120, 20, 16], 0.75);
  return c;
}

function halLeftForearm(t: Texel): Rgb {
  const [, y] = t.at;
  if (y < 1720) return scale(cloth(t, NAVY), 0.75);
  return cloth(t, NAVY);
}

function halHand(t: Texel): Rgb {
  const g = grain(t.at, 20);
  const knuckle = t.normal[1] < -0.2 ? 0.82 : 1;
  return scale(mix(HAL_SKIN, [150, 100, 80], 0.3 * g), lit(t) * knuckle);
}

function halTrousers(t: Texel): Rgb {
  const [x, y, z] = t.at;
  if (t.part === 2 && y > 1880) {
    // The belt and its buckle.
    if (z > 100 && Math.abs(x) < 30) return [170, 160, 130];
    return scale([55, 38, 28], lit(t));
  }
  let c = cloth(t, CANVAS, 70, 0.22);
  // Worn knees, a seam down the outside, mud toward the cuffs.
  if (z > 40 && Math.abs(y - 1010) < 70) c = mix(c, scale([150, 125, 90], lit(t)), 0.35);
  if (Math.abs(t.normal[0]) > 0.85) c = scale(c, 0.85);
  if (y < 420) c = mix(c, scale([70, 55, 40], lit(t)), smooth(420, 140, y) * 0.6);
  return c;
}

function halBoot(t: Texel): Rgb {
  const [x, y, z] = t.at;
  if (y < 40) return [30, 26, 24];
  let c = scale([70, 46, 30], lit(t) * (0.9 + 0.2 * grain(t.at, 25)));
  // Laces up the front.
  if (z > 60 && y > 60 && Math.abs(Math.abs(x) - 210) < 30 && Math.sin(y * 0.3) > 0.6) c = [150, 130, 95];
  return c;
}

export function hal(t: Texel): Rgb {
  switch (t.part) {
    case 1:
      return halHead(t);
    case 0:
      return halJacket(t);
    case 9:
    case 12:
      return halSleeve(t);
    case 13:
      return halBitten(t);
    case 10:
      return halLeftForearm(t);
    case 11:
    case 14:
      return halHand(t);
    case 5:
    case 8:
      return halBoot(t);
    default:
      return halTrousers(t);
  }
}

// ---------------------------------------------------------------------------
// The ranger's partner: Forest Service uniform, a khaki shirt under a green
// jacket, a ranger's hat, boots. Dark blonde, weathered, freckled.

const FOREST: Rgb = [58, 74, 50];
const KHAKI: Rgb = [176, 162, 120];
const HER_SKIN: Rgb = [210, 158, 125];
const HER_HAIR: Rgb = [150, 115, 70];
const FELT: Rgb = [150, 120, 80];

const herFace: Face = {
  chin: 2295, mouth: 2346, nose: 2392, eyes: 2436, brows: 2460, eyeX: 48,
  skin: HER_SKIN, lips: [175, 100, 95], iris: [90, 110, 70], brow: [95, 70, 45],
  eyeH: 6, eyeW: 15, browThick: 6, age: 0.35,
};

/** The hat: the head's vertical axis, the brim's height and reach (game units, body axes). */
const HAT = { axisZ: -20, brim: 2528, band: 2546, reach: 210 };

/**
 * The partner's campaign hat from Rebecca's head: the ring of vertices where
 * her bob flares at the back is pushed out level into a brim. In the head's
 * own space (game axes: x forward, y down, z left), where the head joint
 * stands 2243 units up.
 */
export function campaignHat([x, y, z]: Vec3): Vec3 {
  const up = 2243 - y;
  if (up < 2495 || up > 2560) return [x, y, z];
  const dx = x - HAT.axisZ;
  const r = Math.hypot(dx, z) || 1;
  const k = Math.max(1, HAT.reach / r);
  return [HAT.axisZ + dx * k, 2243 - HAT.brim, z * k];
}

function herHead(t: Texel): Rgb {
  const [x, y, z] = t.at;
  const ax = Math.abs(x);
  const r = Math.hypot(x, z - HAT.axisZ);
  // The hat: a felt crown, a dark band, the brim lit on
  // top and shaded underneath, and its shadow across her brow.
  if (y > HAT.band) return scale(FELT, lit(t) * (0.9 + 0.15 * grain(t.at, 30)));
  if (r > 150 && y > 2470) return scale(FELT, (t.normal[1] > 0 ? lit(t) : 0.55) * (0.9 + 0.12 * grain(t.at, 25)));
  if (y > HAT.brim - 4) return scale([60, 40, 25], lit(t));
  // Her hair: the sides and back of the bob, under the hat.
  const hair = (z < 30 && y > 2300) || (ax > 92 && y > 2330);
  if (hair) {
    const strand = noise([x * 4, y * 0.6, z * 4], 12);
    return scale(mix(HER_HAIR, [105, 78, 45], strand), lit(t));
  }
  let c = face(t, herFace);
  if (y > HAT.brim - 70 && z > 0) c = scale(c, 0.8);
  // Freckles over the nose and cheeks.
  if (front(t) && y > herFace.nose - 15 && y < herFace.eyes - 10 && ax < 80 && hash(Math.round(x / 3), Math.round(y / 3), 7) < 0.05) {
    c = scale(c, 0.88);
  }
  if (y < herFace.chin && z < 60) c = scale(c, 0.88);
  return c;
}

function herJacket(t: Texel): Rgb {
  const [x, y, z] = t.at;
  const ax = Math.abs(x);
  // The shirt shows in the open front, its collar at the neck.
  const opening = 26 + (y - 1700) * 0.07;
  if (z > 40 && ax < opening && y > 1700) {
    let c = cloth(t, KHAKI, 60, 0.12);
    if (ax < 3) c = scale(c, 0.8);
    if (ax < 4 && Math.abs(((y - 1720) % 70) - 35) < 4) return [220, 215, 200];
    return c;
  }
  if (y > 2215) return cloth(t, z > 0 && ax < 70 ? KHAKI : FOREST, 50, 0.1);
  let c = cloth(t, FOREST);
  // The jacket's edge beside the shirt.
  if (z > 40 && ax < opening + 6) c = scale(c, 0.7);
  if (z > 40) {
    // The gold shield on her left chest, the name plate on her right.
    if (x < 0 && Math.hypot((x + 95) * 1.1, (y - 2110) * (y > 2110 ? 1 : 1.5)) < 30) return scale([205, 165, 70], lit(t) * 1.1);
    if (x > 0 && Math.abs(x - 95) < 34 && Math.abs(y - 2125) < 8) return [30, 30, 28];
    // Pocket flaps.
    if (Math.abs(ax - 95) < 40 && (Math.abs(y - 2070) < 3 || (y < 2070 && y > 1990 && Math.abs(ax - 95) > 37))) c = scale(c, 0.72);
  }
  if (y < 1720) c = scale(c, 0.85);
  return c;
}

function herSleeve(t: Texel): Rgb {
  const [x, y] = t.at;
  // The Forest Service shield on each shoulder: a brown shield, gold edge, a green tree.
  const out = Math.abs(x) - 300;
  if (t.part !== 10 && t.part !== 13 && t.normal[0] * Math.sign(x) > 0.3 && Math.abs(out) < 34 && y > 2040 && y < 2140) {
    const sy = (y - 2040) / 100;
    const half = 30 * (sy > 0.35 ? 1 : 0.5 + sy * 1.4);
    if (Math.abs(out) < half) {
      if (Math.abs(out) > half - 5 || y > 2132) return [210, 175, 80];
      if (Math.abs(out) < (sy - 0.2) * 22 && sy < 0.85) return [60, 110, 55];
      return [110, 75, 40];
    }
  }
  let c = cloth(t, FOREST);
  if ((t.part === 10 || t.part === 13) && y < 1470) c = scale(c, 0.78);
  return c;
}

function herHand(t: Texel): Rgb {
  return scale(HER_SKIN, lit(t) * (0.94 + 0.1 * grain(t.at, 15)));
}

function herTrousers(t: Texel): Rgb {
  const [x, y, z] = t.at;
  if (t.part === 2 && y > 1660) {
    if (z > 100 && Math.abs(x) < 24) return [200, 170, 90];
    return scale([95, 62, 35], lit(t));
  }
  let c = cloth(t, [44, 54, 38], 70, 0.18);
  // A cargo pocket on the outside of each thigh.
  if (t.part === 3 || t.part === 6) {
    const side = Math.abs(t.normal[0]) > 0.6;
    if (side && y > 1000 && y < 1250 && (Math.abs(y - 1240) < 4 || Math.abs(z) > 60 && Math.abs(Math.abs(z) - 64) < 4)) c = scale(c, 0.7);
  }
  if (y < 320) c = mix(c, scale([80, 65, 45], lit(t)), smooth(320, 120, y) * 0.5);
  return c;
}

function herBoot(t: Texel): Rgb {
  const [x, y, z] = t.at;
  if (y < 35) return [35, 28, 22];
  let c = scale([110, 72, 40], lit(t) * (0.9 + 0.2 * grain(t.at, 20)));
  if (z > 60 && y > 50 && Math.abs(Math.abs(x) - 150) < 25 && Math.sin(y * 0.35) > 0.6) c = [60, 45, 30];
  return c;
}

export function partner(t: Texel): Rgb {
  switch (t.part) {
    case 1:
      return herHead(t);
    case 0:
      return herJacket(t);
    case 9:
    case 10:
    case 12:
    case 13:
      return herSleeve(t);
    case 11:
    case 14:
      return herHand(t);
    case 5:
    case 8:
      return herBoot(t);
    default:
      return herTrousers(t);
  }
}
