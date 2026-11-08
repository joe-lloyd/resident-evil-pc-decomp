// The logging camp's dead: RE1's three zombie bodies, their skeletons,
// meshes and animations kept, with skins of ours painted from what each
// texel covers (paint.ts). build.ts ships them where her mode loads the
// camp's enemy models (enemy/stage<N>/), so the mansion's zombies stay RE1's.
//
// The bodies share a layout: 0 hips, 1 torso, 2 head, 3-5 right arm, 6-8 left
// arm (out level at rest), 9-11 right leg, 12-14 left leg. Some left and
// right parts share texels, so what is painted on one shows on the other.
// The face heights are measured from each body's own texture (the dark rows
// of its eyes and mouth), in game units from the floor.
import { readEmd, readMesh, readTexture, section, withSection, writeEmd, writeTexture } from './emd.ts';
import { cover } from './island.ts';
import { cloth, grain, hash, lit, mix, noise, scale, smooth } from './brush.ts';
import { paint, surfaceMap, type Rgb, type Texel } from './paint.ts';
import { fitSkin } from './skin.ts';

export interface Zombie {
  readonly slug: string;
  /** The entity id her room scripts place: one of RE1's three zombie ids, which all run zombie_update. */
  readonly entity: 0 | 1 | 17;
  /** The model g_emdPathTable names for that id (EntityModelLoader.cpp), in enemy/. */
  readonly model: string;
  readonly skin: (t: Texel) => Rgb;
}

// ---------------------------------------------------------------------------
// The dead

const ROT: Rgb = [124, 124, 104];
const BRUISE: Rgb = [92, 74, 88];
const BLOOD: Rgb = [118, 16, 12];
const DRIED: Rgb = [66, 22, 16];

/** Dead skin: grey-green, bruised in patches, veined, lit. */
function flesh(t: Texel, base: Rgb = ROT): Rgb {
  let c = scale(base, lit(t) * (0.88 + 0.2 * grain(t.at, 35)));
  c = mix(c, scale(BRUISE, lit(t)), 0.55 * smooth(0.58, 0.8, noise(t.at, 140)));
  const vein = Math.abs(noise([t.at[0] * 1.7, t.at[1] * 0.6, t.at[2] * 1.7], 28) - 0.5);
  if (vein < 0.025) c = mix(c, [70, 70, 86], 0.45);
  return c;
}

/** Blood over a colour: splashes where the noise runs high, and runs down from them. */
function bloodied(c: Rgb, t: Texel, amount: number, seed = 0): Rgb {
  const [x, y, z] = t.at;
  const splash = noise([x + seed * 97, y, z], 70) * 0.7 + noise([x, y + seed * 53, z], 18) * 0.3;
  const run = noise([x * 3.5 + seed * 31, y * 0.18, z * 3.5], 40);
  const wet = smooth(1 - amount * 0.45, 1 - amount * 0.3, splash) + smooth(1 - amount * 0.2, 1 - amount * 0.05, run) * 0.8;
  if (wet <= 0) return c;
  const tone = mix(BLOOD, DRIED, noise([x, y, z + seed * 7], 25));
  return mix(c, scale(tone, lit(t)), Math.min(0.92, wet));
}

/** A bite: torn flesh, wet red round a dark hole, centred on (cx, cy) on the front of the body. */
function bite(c: Rgb, t: Texel, cx: number, cy: number, r: number): Rgb {
  const [x, y, z] = t.at;
  if (t.normal[2] < 0.2) return c;
  const ragged = r * (0.8 + 0.4 * noise([x, y, z], 12));
  const d = Math.hypot(x - cx, (y - cy) * 1.2);
  if (d > ragged * 1.6) return c;
  if (d < ragged * 0.45) return [38, 6, 6];
  if (d < ragged) return scale(mix([150, 30, 26], [95, 16, 14], d / ragged), lit(t));
  return mix(c, scale(BLOOD, lit(t)), smooth(ragged * 1.6, ragged, d) * 0.8);
}

/** Cloth torn through to the dead skin under it, where the noise says so. */
function torn(c: Rgb, t: Texel, amount: number): Rgb {
  const n = noise([t.at[0] * 1.3, t.at[1], t.at[2] * 1.3], 45);
  if (n > 1 - amount * 0.18) return flesh(t);
  if (n > 1 - amount * 0.22) return scale(c, 0.55);
  return c;
}

interface DeadFace {
  readonly chin: number;
  readonly mouth: number;
  /** Half the height of the mouth's opening: wide on a body that gapes. */
  readonly gape: number;
  readonly nose: number;
  readonly eyes: number;
  readonly brows: number;
  readonly eyeX: number;
}

/** A dead face: sunken sockets with milky eyes, the nose's dark holes, the mouth open on its teeth, blood down the chin. */
function deadFace(t: Texel, f: DeadFace, skin: Rgb = [136, 134, 112]): Rgb {
  const [x, y, z] = t.at;
  const ax = Math.abs(x);
  let c = flesh(t, skin);
  if (t.normal[2] < 0.2 || z < 0) return c;
  // The sockets: dark, sunken, with a milky eye in each.
  const ex = (ax - f.eyeX) / 17;
  const ey = (y - f.eyes) / 10;
  const r = Math.hypot(ex, ey);
  if (r < 0.55) return mix([196, 200, 182], [150, 150, 140], r / 0.55);
  if (r < 1.05) return mix([40, 24, 32], [80, 52, 62], (r - 0.55) / 0.5);
  if (r < 1.6) c = scale(c, 0.7 + 0.18 * (r - 1.05));
  // The brow's shadow over them.
  if (Math.abs(y - f.brows) < 6 && ax < f.eyeX * 1.6) c = scale(c, 0.8);
  // The nose: a lit ridge, its holes.
  if (y > f.nose && y < f.eyes - 12 && ax < 8) c = scale(c, 1.08);
  if (Math.hypot(ax - 9, (y - f.nose) * 1.4) < 6) return [30, 14, 14];
  // The mouth: open, its teeth, gums and blood round it.
  const lipW = f.eyeX * 0.95;
  if (ax < lipW) {
    const d = Math.abs(y - f.mouth) / (f.gape * (1 - (ax / lipW) ** 2 * 0.6));
    if (d < 1) {
      const toothRow = Math.abs(Math.abs(y - f.mouth) - f.gape * 0.55) < f.gape * 0.35;
      if (toothRow && Math.sin(x * 0.55) > -0.4) return mix([206, 196, 150], [150, 130, 90], hash(Math.round(x / 4), 1, 2) * 0.6);
      return [42, 10, 10];
    }
    if (d < 1.5) return scale([110, 40, 38], lit(t));
  }
  // Blood from the mouth down the chin.
  if (y < f.mouth && y > f.chin - 40 && ax < lipW) {
    const run = noise([x * 3, y * 0.2, z], 30);
    if (run > 0.55 - (f.mouth - y) * 0.0008) c = mix(c, scale(BLOOD, lit(t)), 0.85);
  }
  return c;
}

/** Hands: dead skin, dark under the nails and in the creases, blood on the fingers. */
const deadHand = (t: Texel) => bloodied(scale(flesh(t), t.normal[1] < -0.2 ? 0.85 : 1), t, 0.5, 3);

/** Boots: scuffed leather, dark soles, laced up the front, caked with mud. */
function boot(t: Texel, leather: Rgb = [62, 44, 30]): Rgb {
  const [x, y, z] = t.at;
  if (y < 30) return [26, 22, 20];
  let c = scale(leather, lit(t) * (0.85 + 0.25 * grain(t.at, 25)));
  if (z > 300 && Math.abs(Math.abs(x) - 190) < 35 && Math.sin(y * 0.32) > 0.55) c = [140, 120, 85];
  return mix(c, scale([74, 60, 42], lit(t)), 0.6 * smooth(90, 20, y));
}

// ---------------------------------------------------------------------------
// Cloth

/** Buffalo check: red and black squares `size` across, the crossings black, by two coordinates on the cloth. */
function buffalo(t: Texel, u: number, v: number, size = 46, red: Rgb = [150, 26, 24]): Rgb {
  const a = Math.floor(u / size) & 1;
  const b = Math.floor(v / size) & 1;
  const tone: Rgb = a && b ? [24, 20, 20] : a || b ? mix(red, [24, 20, 20], 0.55) : red;
  return cloth(t, tone, 60, 0.22);
}

/** Hickory stripe: a blue shirting with narrow white stripes `pitch` apart, along u. */
function hickory(t: Texel, u: number, pitch = 14): Rgb {
  const stripe = Math.abs(((u % pitch) + pitch) % pitch - pitch / 2) < 2.2;
  return cloth(t, stripe ? [200, 200, 196] : [52, 64, 104], 50, 0.18);
}

/** Denim: blue twill, worn pale where it rubs. */
function denim(t: Texel, worn = 0): Rgb {
  const [x, y, z] = t.at;
  const twill = Math.sin((x + y) * 0.9 + z * 0.4) > 0.6 ? 0.92 : 1;
  const base = mix([44, 62, 98], [104, 122, 150], worn);
  return scale(cloth(t, base, 50, 0.2), twill);
}

// ---------------------------------------------------------------------------
// The faller: a red and black flannel shirt torn open on a bitten chest,
// jeans held up by red braces, work boots, a black knit cap, a dark beard.

const FALLER_FACE: DeadFace = { chin: 2600, mouth: 2655, gape: 7, nose: 2715, eyes: 2790, brows: 2825, eyeX: 45 };

function fallerHead(t: Texel): Rgb {
  const [x, y, z] = t.at;
  // The cap, ribbed, its turned-up band low on the brow.
  if (y > 2848 - smooth(80, -150, z) * 30) {
    const band = y < 2880 - smooth(80, -150, z) * 30;
    const rib = Math.sin(Math.atan2(x, z) * 60) > 0 ? 1 : 0.85;
    return scale(cloth(t, [30, 30, 34], 20, 0.15), rib * (band ? 0.82 : 1));
  }
  let c = deadFace(t, FALLER_FACE);
  // A dark beard over the jaw, the mouth left open through it.
  const ax = Math.abs(x);
  if (y < 2700 && t.normal[2] > 0.1 && !(ax < 40 && Math.abs(y - FALLER_FACE.mouth) < 12)) {
    if (hash(Math.round(x / 3), Math.round(y / 3), Math.round(z / 3)) < 0.75) c = mix(c, [42, 32, 26], 0.8);
  }
  return c;
}

function fallerShirt(t: Texel): Rgb {
  const [x, y, z] = t.at;
  const ax = Math.abs(x);
  // Torn open down the front on the dead chest and its bite.
  const open = t.normal[2] > 0.45 && ax < 55 + (y - 1900) * 0.06 && y > 1950;
  if (open) return bloodied(bite(flesh(t), t, -30, 2250, 55), t, 0.6, 1);
  // Red braces over the shirt, front and back.
  if (Math.abs(ax - 105) < 13 && y > 1880) return scale([150, 30, 26], lit(t) * (0.9 + 0.1 * grain(t.at, 20)));
  let c = buffalo(t, x, y);
  c = torn(c, t, 0.6);
  return bloodied(c, t, 0.7, 2);
}

/** A sleeve of the shirt, rolled to the elbow: beyond `cuff` (along the arm) the forearm is bare. */
function rolledSleeve(t: Texel, cuff: number): Rgb {
  const [x, y, z] = t.at;
  const along = Math.abs(x);
  if (along > cuff + 40) return bloodied(flesh(t), t, 0.4, 4);
  if (along > cuff) return scale(buffalo(t, along * 2.4, y + z, 30), 0.85);
  return bloodied(torn(buffalo(t, along, y + z * 0.5), t, 0.5), t, 0.5, 5);
}

function fallerJeans(t: Texel): Rgb {
  const [x, y, z] = t.at;
  if (t.part === 0 && y > 1760) {
    // The belt and its buckle.
    if (z > 300 && Math.abs(x) < 26) return [168, 156, 120];
    return scale([50, 34, 24], lit(t));
  }
  // Worn at the knees, mud up from the boots.
  let c = denim(t, z > 150 && Math.abs(y - 980) < 80 ? 0.6 : 0.1);
  c = mix(c, scale([72, 58, 40], lit(t)), 0.65 * smooth(420, 160, y));
  return bloodied(c, t, 0.4, 6);
}

export function faller(t: Texel): Rgb {
  switch (t.part) {
    case 2:
      return fallerHead(t);
    case 1:
      return fallerShirt(t);
    case 3:
    case 6:
    case 4:
    case 7:
      return rolledSleeve(t, 1050);
    case 5:
    case 8:
      return deadHand(t);
    case 11:
    case 14:
      return boot(t);
    default:
      return fallerJeans(t);
  }
}

// ---------------------------------------------------------------------------
// The bucker: stripped to a sweat-yellowed undershirt, his arms bare and
// bitten, orange chainsaw chaps over grey work trousers, black braces, boots,
// and the orange ear defenders still clamped over his bald head.

const BUCKER_FACE: DeadFace = { chin: 2660, mouth: 2738, gape: 18, nose: 2785, eyes: 2812, brows: 2842, eyeX: 44 };
const CHAPS: Rgb = [204, 92, 28];
const WORK_GREY: Rgb = [92, 94, 90];

function buckerHead(t: Texel): Rgb {
  const [x, y, z] = t.at;
  const ax = Math.abs(x);
  // The ear defenders: an orange cup over each ear, a black band over the crown.
  const cup = Math.hypot((y - 2800) * 0.9, z - 200);
  if (ax > 105 && cup < 70) return scale(cup < 58 ? [214, 104, 26] : [40, 40, 40], lit(t));
  if (Math.abs(z - 200) < 18 && y > 2850) return scale([36, 36, 38], lit(t));
  let c = deadFace(t, BUCKER_FACE, [146, 144, 116]);
  // Grey stubble on the scalp and jaw.
  if ((y > 2880 || (y < 2760 && z > 150)) && hash(Math.round(x / 3), Math.round(y / 3), Math.round(z / 3)) < 0.35) c = scale(c, 0.78);
  return c;
}

function buckerTorso(t: Texel): Rgb {
  const [x, y, z] = t.at;
  const ax = Math.abs(x);
  // The undershirt: deep armholes, a scooped neck, black braces over it.
  const armhole = ax > 250 - (y - 2350) * 0.4 && y > 2350;
  const neck = y > 2520 - Math.max(0, 110 - ax) * 0.4 && ax < 110;
  if (armhole || neck) return bloodied(flesh(t), t, 0.45, 7);
  if (Math.abs(ax - 100) < 12) return scale([30, 28, 28], lit(t));
  let c = cloth(t, [206, 198, 168], 50, 0.14);
  c = mix(c, scale([168, 146, 92], lit(t)), 0.5 * smooth(0.5, 0.75, noise(t.at, 90)));
  c = torn(c, t, 0.8);
  return bloodied(bite(c, t, 70, 2320, 60), t, 0.8, 8);
}

function buckerArm(t: Texel): Rgb {
  const [x] = t.at;
  // A bite out of each forearm.
  return bite(bloodied(flesh(t), t, 0.5, 9), t, Math.sign(x) * 1100, 2400, 45);
}

function buckerLegs(t: Texel): Rgb {
  const [x, y, z] = t.at;
  if (t.part === 0 && y > 1780) return scale([40, 38, 36], lit(t));
  let c = cloth(t, WORK_GREY, 60, 0.2);
  // The chaps down the front of each leg, quilted, to the boot.
  if (t.normal[2] > 0.1 && y > 200 && t.part !== 0) {
    const quilt = Math.sin(y * 0.11) > 0.85 ? 0.82 : 1;
    c = scale(cloth(t, CHAPS, 50, 0.16), quilt);
    // The buckle straps round the back of the thigh show at the sides.
    if (Math.abs(y - 1300) < 14 || Math.abs(y - 700) < 14) c = scale([30, 28, 28], lit(t));
  }
  c = mix(c, scale([72, 58, 40], lit(t)), 0.6 * smooth(380, 160, y));
  return bloodied(c, t, 0.35, 10);
}

export function bucker(t: Texel): Rgb {
  switch (t.part) {
    case 2:
      return buckerHead(t);
    case 1:
      return buckerTorso(t);
    case 3:
    case 4:
    case 6:
    case 7:
      return buckerArm(t);
    case 5:
    case 8:
      return deadHand(t);
    case 11:
    case 14:
      return boot(t, [52, 40, 30]);
    default:
      return buckerLegs(t);
  }
}

// ---------------------------------------------------------------------------
// The rigger: a tan waxed-canvas cruiser coat with an orange hi-vis band,
// open on a blue hickory-stripe shirt, dark canvas trousers cut short over
// high boots, and a yellow hard hat.

const RIGGER_FACE: DeadFace = { chin: 2600, mouth: 2655, gape: 9, nose: 2715, eyes: 2790, brows: 2825, eyeX: 45 };
const TIN_CLOTH: Rgb = [146, 116, 70];
const HI_VIS: Rgb = [232, 112, 24];

function riggerHead(t: Texel): Rgb {
  const [x, y, z] = t.at;
  // The hard hat: a yellow dome, its ridge down the middle, the rim's line.
  const rim = 2860 - smooth(100, -150, z) * 20;
  if (y > rim) {
    let c = scale([214, 176, 40], lit(t) * (0.92 + 0.12 * grain(t.at, 60)));
    if (Math.abs(x) < 10) c = scale(c, 1.12);
    if (y < rim + 10) c = scale(c, 0.7);
    return bloodied(c, t, 0.25, 11);
  }
  let c = deadFace(t, RIGGER_FACE);
  // The hat's shadow on the brow, grey stubble at the jaw and the sides.
  if (y > rim - 20 && t.normal[2] > 0.1) c = scale(c, 0.75);
  if (y < 2700 && t.normal[2] > 0.1 && hash(Math.round(x / 3), Math.round(y / 3), Math.round(z / 3)) < 0.4) c = mix(c, [150, 148, 140], 0.5);
  return c;
}

/** Waxed canvas: tan, stiff, darker in its creases and where it is greasy. */
const tinCloth = (t: Texel) => mix(cloth(t, TIN_CLOTH, 80, 0.28), scale([86, 70, 44], lit(t)), 0.4 * smooth(0.55, 0.8, noise(t.at, 110)));

function riggerCoat(t: Texel): Rgb {
  const [x, y, z] = t.at;
  const ax = Math.abs(x);
  // Open down the front on the hickory shirt.
  if (t.normal[2] > 0.45 && ax < 45 && y > 1900) return bloodied(hickory(t, x), t, 0.6, 12);
  // The collar, corduroy brown.
  if (y > 2500) return scale([84, 58, 36], lit(t) * (Math.sin(x * 0.5) > 0.3 ? 1 : 0.88));
  let c = tinCloth(t);
  // The hi-vis band round the chest and back, a silver line along it.
  if (Math.abs(y - 2280) < 34) c = Math.abs(y - 2280) < 6 ? [200, 204, 206] : scale(HI_VIS, lit(t));
  // Chest pockets with flaps.
  if (t.normal[2] > 0.45 && Math.abs(ax - 140) < 60 && y > 2080 && y < 2210 && (Math.abs(ax - 140) > 56 || Math.abs(y - 2190) < 4)) c = scale(c, 0.7);
  return bloodied(torn(c, t, 0.4), t, 0.6, 13);
}

function riggerSleeve(t: Texel): Rgb {
  const [x] = t.at;
  let c = tinCloth(t);
  // The hi-vis band round the upper arm.
  if (Math.abs(Math.abs(x) - 600) < 40) c = Math.abs(Math.abs(x) - 600) < 7 ? [200, 204, 206] : scale(HI_VIS, lit(t));
  if (Math.abs(x) > 1240) c = scale(c, 0.8);
  return bloodied(c, t, 0.45, 14);
}

function riggerTrousers(t: Texel): Rgb {
  const [x, y, z] = t.at;
  if (t.part === 0 && y > 1760) {
    if (z > 300 && Math.abs(x) < 24) return [150, 150, 140];
    return scale([42, 32, 24], lit(t));
  }
  // Dark canvas, cut off short over the boots.
  if (y < 380) return boot(t, [40, 30, 22]);
  const c = cloth(t, [66, 62, 50], 60, 0.24);
  return bloodied(mix(c, scale([72, 58, 40], lit(t)), 0.5 * smooth(620, 380, y)), t, 0.4, 16);
}

export function rigger(t: Texel): Rgb {
  switch (t.part) {
    case 2:
      return riggerHead(t);
    case 1:
      return riggerCoat(t);
    case 3:
    case 4:
    case 6:
    case 7:
      return riggerSleeve(t);
    case 5:
    case 8:
      return deadHand(t);
    case 11:
    case 14:
      return boot(t, [40, 30, 22]);
    default:
      return riggerTrousers(t);
  }
}

// ---------------------------------------------------------------------------

/** The stages the logging camp's rooms sit in (day/rooms.ts): Stage 2 0x1a-0x1f and Stage 3 0x12-0x18. */
export const CAMP_STAGES = [2, 3] as const;

export const zombies: readonly Zombie[] = [
  { slug: 'faller', entity: 0, model: 'EM1000.EMD', skin: faller },
  { slug: 'bucker', entity: 1, model: 'EM1001.EMD', skin: bucker },
  { slug: 'rigger', entity: 17, model: 'EM1011.EMD', skin: rigger },
];

/**
 * Texels the head shares with another part. RE1's zombies reuse one patch of
 * the sheet for the head and some limbs (the first body's left forearm and
 * right shin), and the sheet has no room to part them (island.ts finds none),
 * so they are painted as RE1 paints them: bare dead skin, the only thing
 * right on a head and a torn sleeve or trouser leg alike.
 */
function sharedWithHead(tmd: Uint8Array): Set<number> {
  const owners = new Map<number, Set<number>>();
  readMesh(tmd).forEach((o, part) => {
    for (const t of o.triangles) cover(t.uv, (x, y) => {
      const k = y * 256 + x;
      (owners.get(k) ?? owners.set(k, new Set()).get(k)!).add(part);
    });
  });
  return new Set([...owners].filter(([, parts]) => parts.has(2) && parts.size > 1).map(([k]) => k));
}

/** The zombie's own model with our skin in place of its texture: the same size, and every other byte as it was. */
export function zombieModel(file: Uint8Array, zombie: Zombie): Uint8Array {
  const emd = readEmd(file);
  const tim = section(emd, 'tim');
  const shared = sharedWithHead(section(emd, 'tmd'));
  const map = surfaceMap(file);
  const bare = new Set([...shared].map((i) => map[i]));
  const skin = paint(map, (t) => (bare.has(t) ? bloodied(flesh(t), t, 0.6, 20) : zombie.skin(t)));
  return writeEmd(withSection(emd, 'tim', writeTexture(tim, fitSkin(readTexture(tim), skin))));
}
