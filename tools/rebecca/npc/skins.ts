// The two people's skins, painted from what each texel covers (paint.ts).
// Positions are body axes in game units: x to the character's right, y up
// from the floor, z forward. Landmark heights come from each model's own
// head and body (docs/REBECCA_NPC.md); nothing is taken from the game's art.
import type { Vec3 } from './emd.ts';
import type { Rgb, Texel } from './paint.ts';
import { cloth, face, front, grain, hash, lit, mix, noise, scale, smooth, type Face } from './brush.ts';

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
// Dana Whitlock, the ranger's partner: Forest Service uniform, a khaki shirt
// under a green jacket, a campaign hat, boots. Jill's body, taller and slimmer
// than Rebecca's. Dark blonde hair cut short at the sides and pinned in a low
// bun, weathered, freckled. Her heights are Jill's model's (docs/REBECCA_NPC.md).

const FOREST: Rgb = [58, 74, 50];
const KHAKI: Rgb = [176, 162, 120];
const HER_SKIN: Rgb = [210, 158, 125];
const HER_HAIR: Rgb = [160, 125, 78];
const FELT: Rgb = [150, 120, 80];

const herFace: Face = {
  chin: 2350, mouth: 2384, nose: 2432, eyes: 2487, brows: 2506, eyeX: 55,
  skin: HER_SKIN, lips: [175, 100, 95], iris: [90, 110, 70], brow: [100, 75, 48],
  eyeH: 6.5, eyeW: 17, browThick: 6, age: 0.1,
};

/**
 * Her head: where its joint stands, and the hat. Heights are game units from
 * the floor; the hat's axis sits `axis` forward of the joint.
 */
const HEAD = { joint: 2232, axis: -10, brim: 2560, brimReach: 215, crownBase: 2572, crownTop: 2680, crownR: 115, top: 2700 };
/** The bun: where the back of her hair is gathered, and how tight. */
const BUN = { forward: -150, up: 2390, pull: 0.55 };

/**
 * Dana's head from Jill's, vertices moved and nothing added, in the head's own
 * space (game axes: x forward, y down, z left):
 * - a felt hat: the ring of vertices round her hairline is laid out level
 *   as the brim's edge, the beret's lower ring drawn in as the crown's base
 *   just above it (so the brim lies flat), its upper ring stood straight
 *   above that as the crown's top, and its middle as the top's centre;
 * - the hair hanging beside her face is tucked up against her head to ear
 *   level, a short cut;
 * - the hair at the back is drawn in to a low bun at the nape.
 */
export function danaHead([x, y, z]: Vec3): Vec3 {
  const up = HEAD.joint - y;
  const at = (u: number) => HEAD.joint - u;
  const fx = x - HEAD.axis;
  const r = Math.hypot(fx, z);
  const ring = (reach: number, height: number): Vec3 => [HEAD.axis + (fx * reach) / r, at(height), (z * reach) / r];
  if (up >= 2595 && r < 30) return [x, at(HEAD.top), z];
  if (up >= 2595) return ring(HEAD.crownR, HEAD.crownTop);
  if (up >= 2545 && r > 100) return ring(HEAD.crownR, HEAD.crownBase);
  if (up >= 2495 && r > 100) return ring(HEAD.brimReach, HEAD.brim);
  if (up < 2440 && x < -95) {
    return [BUN.forward + (x - BUN.forward) * BUN.pull, at(BUN.up + (up - BUN.up) * BUN.pull), z * BUN.pull];
  }
  if (up < 2440 && Math.abs(z) > 95 && x > -95) return [x, at(Math.max(up, 2400)), Math.sign(z) * 100];
  return [x, y, z];
}

function herHead(t: Texel): Rgb {
  const [x, y, z] = t.at;
  const ax = Math.abs(x);
  const r = Math.hypot(x, z - HEAD.axis);
  // The hat: a felt crown above the brim, the brim lit on top and shaded
  // underneath, a dark band where it sits on her head, its shadow on her brow.
  if (y > HEAD.crownBase + 18) return scale(FELT, lit(t) * (0.95 + 0.07 * grain(t.at, 70)));
  if (y > HEAD.brim + 4 && r < HEAD.crownR + 15) return scale([60, 40, 25], lit(t));
  if (r > HEAD.crownR + 15 && y > 2520) return scale(FELT, (t.normal[1] > 0 ? lit(t) : 0.55) * (0.95 + 0.07 * grain(t.at, 70)));
  // Her hair: short at the sides above the ears, the back and the bun.
  const bunAt = Math.hypot(z - BUN.forward, y - BUN.up, x * 1.3);
  if (bunAt < 70 && Math.abs(bunAt - 38) < 5) return [40, 30, 22];
  const bun = bunAt < 70;
  const hair = bun || (z < -40 && y > 2300) || (ax > 92 && y > 2405 && z < 70);
  if (hair) {
    const strand = noise(bun ? [x * 2, y * 2, z * 2] : [x * 4, y * 0.6, z * 4], 12);
    return scale(mix(HER_HAIR, [110, 82, 48], strand), lit(t) * (bun ? 0.95 : 1));
  }
  let c = face(t, herFace);
  if (y > 2530 && z > 0) c = scale(c, 0.8);
  // Freckles over the nose and cheeks.
  if (front(t) && y > herFace.nose - 15 && y < herFace.eyes - 10 && ax < 85 && hash(Math.round(x / 3), Math.round(y / 3), 7) < 0.05) {
    c = scale(c, 0.88);
  }
  if (y < herFace.chin && z < 60) c = scale(c, 0.88);
  return c;
}

function herJacket(t: Texel): Rgb {
  const [x, y, z] = t.at;
  const ax = Math.abs(x);
  // The shirt shows in the open front, its collar at the neck.
  const opening = 26 + (y - 1620) * 0.065;
  if (z > 40 && ax < opening && y > 1620) {
    let c = cloth(t, KHAKI, 60, 0.12);
    if (ax < 3) c = scale(c, 0.8);
    if (ax < 4 && Math.abs(((y - 1640) % 70) - 35) < 4) return [220, 215, 200];
    return c;
  }
  if (y > 2260) return cloth(t, z > 0 && ax < 70 ? KHAKI : FOREST, 50, 0.1);
  let c = cloth(t, FOREST);
  // The jacket's edge beside the shirt.
  if (z > 40 && ax < opening + 6) c = scale(c, 0.7);
  if (z > 40) {
    // The gold shield on her left chest, the name plate on her right.
    if (x < 0 && Math.hypot((x + 100) * 1.1, (y - 2140) * (y > 2140 ? 1 : 1.5)) < 30) return scale([205, 165, 70], lit(t) * 1.1);
    if (x > 0 && Math.abs(x - 100) < 34 && Math.abs(y - 2155) < 8) return [30, 30, 28];
    // Pocket flaps.
    if (Math.abs(ax - 100) < 40 && (Math.abs(y - 2100) < 3 || (y < 2100 && y > 2020 && Math.abs(ax - 100) > 37))) c = scale(c, 0.72);
  }
  if (y < 1640) c = scale(c, 0.85);
  return c;
}

function herSleeve(t: Texel): Rgb {
  const [x, y] = t.at;
  // The Forest Service shield on each shoulder: a brown shield, gold edge, a green tree.
  const out = Math.abs(x) - 320;
  if (t.part !== 10 && t.part !== 13 && t.normal[0] * Math.sign(x) > 0.3 && Math.abs(out) < 34 && y > 2060 && y < 2160) {
    const sy = (y - 2060) / 100;
    const half = 30 * (sy > 0.35 ? 1 : 0.5 + sy * 1.4);
    if (Math.abs(out) < half) {
      if (Math.abs(out) > half - 5 || y > 2152) return [210, 175, 80];
      if (Math.abs(out) < (sy - 0.2) * 22 && sy < 0.85) return [60, 110, 55];
      return [110, 75, 40];
    }
  }
  let c = cloth(t, FOREST);
  if ((t.part === 10 || t.part === 13) && y < 1440) c = scale(c, 0.78);
  return c;
}

function herHand(t: Texel): Rgb {
  return scale(HER_SKIN, lit(t) * (0.94 + 0.1 * grain(t.at, 15)));
}

function herTrousers(t: Texel): Rgb {
  const [x, y, z] = t.at;
  if (t.part === 2 && y > 1640) {
    if (z > 100 && Math.abs(x) < 24) return [200, 170, 90];
    return scale([95, 62, 35], lit(t));
  }
  let c = cloth(t, [44, 54, 38], 70, 0.18);
  // A cargo pocket on the outside of each thigh.
  if (t.part === 3 || t.part === 6) {
    const side = Math.abs(t.normal[0]) > 0.6;
    if (side && y > 1050 && y < 1300 && (Math.abs(y - 1290) < 4 || (Math.abs(z) > 60 && Math.abs(Math.abs(z) - 64) < 4))) c = scale(c, 0.7);
  }
  if (y < 320) c = mix(c, scale([80, 65, 45], lit(t)), smooth(320, 120, y) * 0.5);
  return c;
}

function herBoot(t: Texel): Rgb {
  const [x, y, z] = t.at;
  if (y < -65) return [35, 28, 22];
  let c = scale([110, 72, 40], lit(t) * (0.9 + 0.2 * grain(t.at, 20)));
  if (z > 60 && y > -45 && Math.abs(Math.abs(x) - 150) < 25 && Math.sin(y * 0.35) > 0.6) c = [60, 45, 30];
  return c;
}

export function dana(t: Texel): Rgb {
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
