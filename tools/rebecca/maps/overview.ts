// The overview of her map screen: the mountain from above, as RE1's shows the
// Spencer estate, with the stages of her day unlocking as she reaches them.
// Drawn here from the plan's map of the mountain (plan/research/layout.ts):
// forest over a lit relief, the gorge's river, the trails between her
// places, a roof for each building and a clearing for each place outdoors,
// the gondola's cable down to the valley and the mansion at the bottom.
//
// The picture is RE1's overview file (map0d, map0c, map00, map0e: one per
// stage, each showing the places of its stage and those before), a 256 x 256
// 8-bit TIM laid out as the engine's browser sprites read it:
//
//   (0, 0)     160 x 72   the mountain
//   markers    each stage's places cut out of it, drawn over the mountain
//              bright for the stage chosen and dim for the others
//   labels     104 x 16   each area's name, under the mountain
//   (160, 64)  32 x 8     the up and down arrows, grey and lit, as RE1's
//
// Where the markers and labels are is decided here; engine.ts writes it into
// RebMaps.cpp for the browser to draw from.
import { LAYOUT } from '../plan/research/layout.ts';
import { day } from '../plan/day.ts';
import { AREAS, STAGES } from '../plan/maps.ts';
import { ADVANCE, glyph } from '../files/font.ts';
import { ps1, rgbOf, type Tim8 } from './tim.ts';

export const OV_W = 256;
export const OV_H = 256;
export const BASE_W = 160;
export const BASE_H = 72;
/** Where the browser draws the mountain on the 320 x 240 screen (g_MapBaseDesc). */
export const BASE_SCREEN = { x: 33, y: 32 } as const;
export const LABEL_W = 104;
export const LABEL_H = 16;
/** The label's place on the screen: where RE1 draws the building's name and floor together. */
export const LABEL_SCREEN = { x: 57, y: 104 } as const;
/** RE1's arrows: 8 x 8, up then down, each grey and lit. */
export const ARROWS = { u: 160, v: 64 } as const;

export interface Rect {
  readonly x: number;
  readonly y: number;
  readonly w: number;
  readonly h: number;
}

export interface Overview {
  /** One picture per stage: stage k shows the places of stages 0 to k. */
  readonly stages: readonly Tim8[];
  /** Each stage's cut-out: where it sits in the mountain (and so on the screen), and where in the picture. */
  readonly markers: readonly { readonly at: Rect; readonly u: number; readonly v: number }[];
  /** Each area's name, by index into AREAS: where in the picture. */
  readonly labels: readonly { readonly u: number; readonly v: number }[];
}

// --- The palette: ramps of shades for each material, index 0 clear. ---

type RGB = readonly [number, number, number];
const mix = (a: RGB, b: RGB, t: number): RGB => [a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, a[2] + (b[2] - a[2]) * t];

const RAMPS = {
  forest: { n: 64, dark: [10, 22, 8], light: [104, 132, 52] },
  meadow: { n: 16, dark: [44, 56, 20], light: [150, 150, 84] },
  rock: { n: 32, dark: [40, 38, 36], light: [196, 190, 176] },
  earth: { n: 12, dark: [70, 52, 30], light: [176, 150, 104] },
  water: { n: 12, dark: [18, 34, 60], light: [96, 140, 170] },
  roof: { n: 16, dark: [44, 30, 26], light: [150, 112, 88] },
  wall: { n: 12, dark: [60, 58, 60], light: [216, 212, 200] },
  mansion: { n: 16, dark: [70, 44, 52], light: [212, 200, 196] },
  ink: { n: 4, dark: [8, 8, 8], light: [48, 44, 40] },
  text: { n: 2, dark: [24, 24, 24], light: [192, 192, 184] },
  arrow: { n: 4, dark: [96, 96, 96], light: [40, 220, 80] },
} as const;
type Material = keyof typeof RAMPS;

const BASES = new Map<Material, number>();
const CLUT = new Uint16Array(256);
{
  let at = 1;
  for (const [m, r] of Object.entries(RAMPS) as [Material, (typeof RAMPS)[Material]][]) {
    BASES.set(m, at);
    for (let i = 0; i < r.n; i++) {
      const [cr, cg, cb] = mix(r.dark as RGB, r.light as RGB, r.n === 1 ? 1 : i / (r.n - 1));
      // A colour that rounds to black would read as see-through: keep it off zero.
      CLUT[at + i] = ps1(Math.max(8, cr), Math.max(8, cg), Math.max(8, cb));
    }
    at += r.n;
  }
  if (at > 256) throw new Error(`the overview's palette needs ${at} colours`);
}

/** A material's index at a shade from 0 (dark) to 1 (light). */
function shade(m: Material, t: number): number {
  const n = RAMPS[m].n;
  return BASES.get(m)! + Math.max(0, Math.min(n - 1, Math.round(t * (n - 1))));
}

// --- Noise ---

function hash(x: number, y: number, seed: number): number {
  let h = (x * 374761393 + y * 668265263 + seed * 2147483647) | 0;
  h = Math.imul(h ^ (h >>> 13), 1274126177);
  return ((h ^ (h >>> 16)) >>> 0) / 4294967296;
}

function valueNoise(x: number, y: number, seed: number): number {
  const xi = Math.floor(x);
  const yi = Math.floor(y);
  const fx = x - xi;
  const fy = y - yi;
  const s = (t: number) => t * t * (3 - 2 * t);
  const a = hash(xi, yi, seed);
  const b = hash(xi + 1, yi, seed);
  const c = hash(xi, yi + 1, seed);
  const d = hash(xi + 1, yi + 1, seed);
  return a + (b - a) * s(fx) + (c - a) * s(fy) + (a - b - c + d) * s(fx) * s(fy);
}

function fbm(x: number, y: number, seed: number, octaves = 4): number {
  let sum = 0;
  let amp = 0.5;
  let f = 1;
  for (let i = 0; i < octaves; i++) {
    sum += amp * valueNoise(x * f, y * f, seed + i * 17);
    amp /= 2;
    f *= 2;
  }
  return sum;
}

// --- Where things are ---

/**
 * The plan's mountain (metres, x east, y down the slope) on the panel: down
 * the slope runs left to right and east is up. The busy mountain top takes
 * most of the width, the long ride down and the estate the rest.
 */
const WORLD = { x0: 90, x1: 530 };
const ACROSS: readonly (readonly [number, number])[] = [
  [0, 4],
  [215, 96],
  [420, 128],
  [600, 156],
];
function toPanel(x: number, y: number): { x: number; y: number } {
  let px = ACROSS.at(-1)![1];
  for (let i = 1; i < ACROSS.length; i++) {
    const [y0, x0] = ACROSS[i - 1]!;
    const [y1, x1] = ACROSS[i]!;
    if (y <= y1) {
      px = x0 + ((Math.max(y, y0) - y0) / (y1 - y0)) * (x1 - x0);
      break;
    }
  }
  return { x: px, y: 3 + ((WORLD.x1 - x) / (WORLD.x1 - WORLD.x0)) * (BASE_H - 6) };
}
const placeAt = (id: string) => {
  const p = LAYOUT[id];
  if (!p) throw new Error(`${id} has no place on the mountain (plan/research/layout.ts)`);
  return toPanel(p[0], p[1]);
};

const stageOfPlace = (place: string) => STAGES.findIndex((s) => s.areas.some((a) => AREAS.find((x) => x.id === a)!.places.includes(place)));
const inside = (place: string) => ['cabin', 'shed', 'booth', 'bunkhouse', 'office', 'mess', 'workshop', 'sawmill', 'generator', 'switch', 'cottage', 'quarry-office', 'mine-office', 'weather', 'lower-station', 'lodge', 'garden-shed'].includes(place);
const underground = (place: string) => ['tunnel', 'mine-office', 'junction', 'gallery', 'mine-lift', 'cellar', 'wine', 'crawl', 'save'].includes(place);

/** The river: down from the camp's mill pond, through the gorge under the footbridge, to the creek in the valley. */
const RIVER: readonly (readonly [number, number])[] = [
  [150, 0], [184, 30], [222, 40], [262, 120], [300, 148], [318, 200], [340, 260], [330, 330], [300, 398], [270, 470], [250, 600],
];

/** The mountain's tops: the summit and the ridge where the day begins. */
const PEAKS = [
  { at: toPanel(492, 40), r: 16, h: 1 },
  { at: toPanel(300, 10), r: 12, h: 0.8 },
];

/** How high the ground is at a panel point, 0 to 1: the tops, the falling slope, folds in it. */
function height(px: number, py: number): number {
  const slope = Math.max(0, 1 - px / BASE_W) * 0.5;
  const peaks = Math.max(...PEAKS.map((p) => p.h * Math.exp(-((px - p.at.x) ** 2 + (py - p.at.y) ** 2) / (2 * p.r * p.r))));
  return slope + peaks * 0.45 + (fbm(px / 14, py / 7, 7) - 0.5) * 0.25;
}

// --- Drawing ---

interface Canvas {
  pixels: Uint8Array;
  /** Which stage drew each pixel above the forest: -1 for the land itself. */
  stage: Int8Array;
}

function put(c: Canvas, x: number, y: number, index: number, stage: number): void {
  const px = Math.round(x);
  const py = Math.round(y);
  if (px < 0 || py < 0 || px >= BASE_W || py >= BASE_H) return;
  c.pixels[py * BASE_W + px] = index;
  c.stage[py * BASE_W + px] = stage;
}

function line(c: Canvas, a: { x: number; y: number }, b: { x: number; y: number }, index: (t: number) => number, stage: number): void {
  const steps = Math.ceil(Math.hypot(b.x - a.x, b.y - a.y) * 2) + 1;
  for (let i = 0; i <= steps; i++) {
    const t = i / steps;
    put(c, a.x + (b.x - a.x) * t, a.y + (b.y - a.y) * t, index(t), stage);
  }
}

function land(): Canvas {
  const c: Canvas = { pixels: new Uint8Array(BASE_W * BASE_H), stage: new Int8Array(BASE_W * BASE_H).fill(-1) };
  const river = RIVER.map(([x, y]) => toPanel(x, y));
  const toRiver = (x: number, y: number) => {
    let best = Infinity;
    for (let i = 1; i < river.length; i++) {
      const a = river[i - 1]!;
      const b = river[i]!;
      const len2 = (b.x - a.x) ** 2 + (b.y - a.y) ** 2;
      const t = Math.max(0, Math.min(1, ((x - a.x) * (b.x - a.x) + (y - a.y) * (b.y - a.y)) / len2));
      best = Math.min(best, Math.hypot(x - a.x - t * (b.x - a.x), y - a.y - t * (b.y - a.y)));
    }
    return best;
  };
  for (let y = 0; y < BASE_H; y++)
    for (let x = 0; x < BASE_W; x++) {
      const h = height(x, y);
      // Light from the top left, off the slope of the ground.
      const lit = Math.max(0, Math.min(1, 0.5 + (height(x - 1, y - 1) - height(x + 1, y + 1)) * 6));
      // Tree crowns: blobs a pixel or two across, each lit on its top left.
      const crown = valueNoise(x / 1.4, y / 1.4, 11);
      const crowns = Math.max(0, Math.min(1, (crown - valueNoise((x + 0.7) / 1.4, (y + 0.7) / 1.4, 11)) * 2.2 + crown * 0.6 + hash(x, y, 3) * 0.15));
      const r = toRiver(x, y);
      let index: number;
      if (r < 0.9) index = shade('water', 0.35 + lit * 0.4);
      else if (r < 1.6) index = shade('rock', 0.2 + lit * 0.3);
      else if (h > 0.78) index = shade('rock', 0.25 + lit * 0.6 + crowns * 0.15); // bare rock above the trees
      else if (h > 0.7) index = shade('meadow', 0.2 + lit * 0.5 + crowns * 0.3);
      else index = shade('forest', 0.02 + lit * 0.35 + crowns * 0.5 + (1 - h) * 0.08);
      c.pixels[y * BASE_W + x] = index;
    }
  return c;
}

/** The places of the stages up to `upTo` on the land: the trails first, then clearings, roofs, the cable and the mansion. */
function places(c: Canvas, upTo: number): void {
  const shown = (p: string) => stageOfPlace(p) <= upTo;
  // Trails and roads, between places both shown. Underground ways are not seen from above.
  for (const l of day.links) {
    if (!shown(l.from) || !shown(l.to) || l.kind === 'ride' || l.kind === 'lift') continue;
    if (underground(l.from) && underground(l.to)) continue;
    const stage = Math.max(stageOfPlace(l.from), stageOfPlace(l.to));
    line(c, placeAt(l.from), placeAt(l.to), (t) => shade('earth', 0.7 + 0.3 * hash(Math.round(t * 40), 1, 5)), stage);
  }
  // The gondola's cable, from the upper station to the lower.
  if (shown('car')) {
    const a = placeAt('platform');
    const b = placeAt('lower-station');
    line(c, a, b, () => shade('ink', 0.6), stageOfPlace('car'));
    const pylon = placeAt('pylon');
    for (let d = -1; d <= 1; d++) put(c, pylon.x, pylon.y + d, shade('wall', 0.3), stageOfPlace('pylon'));
  }
  for (const p of day.places) {
    if (!shown(p.id) || p.id === 'save') continue;
    const s = stageOfPlace(p.id);
    const at = placeAt(p.id);
    if (underground(p.id)) continue;
    if (inside(p.id)) {
      // A roof, three by two, lit on its top left, and its shadow.
      for (let dx = -1; dx <= 2; dx++) put(c, at.x + dx, at.y + 1, shade('ink', 0.3), s);
      put(c, at.x + 2, at.y, shade('ink', 0.3), s);
      for (let dy = -1; dy <= 0; dy++)
        for (let dx = -1; dx <= 1; dx++) put(c, at.x + dx, at.y + dy, shade('wall', dy < 0 ? 0.95 : 0.6), s);
    } else {
      // A clearing.
      for (let dy = -1; dy <= 1; dy++)
        for (let dx = -2; dx <= 2; dx++) {
          if (Math.abs(dx) === 2 && dy !== 0) continue;
          put(c, at.x + dx, at.y + dy, shade('meadow', 0.55 + 0.3 * hash(Math.round(at.x) + dx, Math.round(at.y) + dy, 9)), s);
        }
    }
  }
  // The mine's way in: a dark mouth in the rock.
  if (shown('mine-entrance')) {
    const m = placeAt('tunnel');
    for (let dx = -1; dx <= 0; dx++) put(c, m.x + dx, m.y, shade('ink', 0), stageOfPlace('tunnel'));
  }
  // The mansion over its cellar: RE1's house from above, a long front with
  // its two wings back, pale roofs lit on their top left, a dark edge.
  if (shown('save')) {
    const at = placeAt('save');
    const s = stageOfPlace('save');
    const part = (dx: number, dy: number) => (dy >= -4 && dy <= -1 && Math.abs(dx) <= 6) || (dy >= -4 && dy <= 4 && Math.abs(dx) >= 4 && Math.abs(dx) <= 6);
    for (let dy = -5; dy <= 5; dy++)
      for (let dx = -7; dx <= 7; dx++) {
        if (!part(dx, dy)) {
          if (part(dx - 1, dy - 1)) put(c, at.x + dx, at.y + dy, shade('ink', 0.1), s); // its shadow
          continue;
        }
        const edge = !part(dx - 1, dy) || !part(dx + 1, dy) || !part(dx, dy - 1) || !part(dx, dy + 1);
        const ridge = (dy === -3 && Math.abs(dx) <= 4) || (Math.abs(dx) === 5 && dy >= -3);
        put(c, at.x + dx, at.y + dy, shade('mansion', edge ? 0.2 : ridge ? 0.95 : 0.65 + 0.1 * ((dx + dy) & 1)), s);
      }
  }
}

// --- Text ---

function label(text: string): Uint8Array {
  const out = new Uint8Array(LABEL_W * LABEL_H);
  const width = text.length * ADVANCE - (ADVANCE - 5);
  if (width > LABEL_W) throw new Error(`"${text}" is ${width} pixels, a label ${LABEL_W}`);
  const x0 = Math.floor((LABEL_W - width) / 2);
  const y0 = 3;
  [...text].forEach((ch, i) => {
    const g = glyph(ch);
    g.forEach((row, gy) =>
      row.forEach((ink, gx) => {
        if (!ink) return;
        const x = x0 + i * ADVANCE + gx;
        const y = y0 + gy;
        out[y * LABEL_W + x] = shade('text', 1);
        // A shadow below and right, as the game's own lettering has.
        if (y + 1 < LABEL_H && x + 1 < LABEL_W && !out[(y + 1) * LABEL_W + x + 1]) out[(y + 1) * LABEL_W + x + 1] = shade('text', 0);
      }),
    );
  });
  return out;
}

function arrows(): Uint8Array {
  // 32 x 8: up grey, up lit, down grey, down lit.
  const out = new Uint8Array(32 * 8);
  for (let k = 0; k < 4; k++) {
    const up = k < 2;
    const colour = shade('arrow', k % 2 ? 1 : 0);
    for (let row = 0; row < 4; row++) {
      const y = up ? 2 + row : 5 - row;
      for (let x = 4 - row; x <= 3 + row; x++) out[y * 32 + k * 8 + x] = colour;
    }
  }
  return out;
}

// --- Laying out the picture ---

/** Free space in the picture, filled first fit. */
function packer(free: Rect[]) {
  return (w: number, h: number): { u: number; v: number } => {
    for (let i = 0; i < free.length; i++) {
      const f = free[i]!;
      if (w > f.w || h > f.h) continue;
      free.splice(i, 1, { x: f.x + w, y: f.y, w: f.w - w, h }, { x: f.x, y: f.y + h, w: f.w, h: f.h - h });
      return { u: f.x, v: f.y };
    }
    throw new Error(`no room in the overview for ${w} x ${h}`);
  };
}

export function overview(): Overview {
  const full = land();
  places(full, STAGES.length - 1);
  // Each stage's cut-out: what its places drew, in a box round them.
  const pack = packer([
    { x: BASE_W, y: 0, w: OV_W - BASE_W, h: ARROWS.v },
    { x: 0, y: BASE_H + 6 * LABEL_H, w: OV_W, h: OV_H - BASE_H - 6 * LABEL_H },
    { x: 2 * LABEL_W, y: BASE_H, w: OV_W - 2 * LABEL_W, h: 6 * LABEL_H },
  ]);
  const markers = STAGES.map((_, s) => {
    let [x0, y0, x1, y1] = [BASE_W, BASE_H, -1, -1];
    for (let y = 0; y < BASE_H; y++)
      for (let x = 0; x < BASE_W; x++)
        if (full.stage[y * BASE_W + x] === s) [x0, y0, x1, y1] = [Math.min(x0, x), Math.min(y0, y), Math.max(x1, x), Math.max(y1, y)];
    if (x1 < 0) throw new Error(`stage ${s} draws nothing on the overview`);
    const at = { x: x0, y: y0, w: x1 - x0 + 1, h: y1 - y0 + 1 };
    return { at, ...pack(at.w, at.h) };
  });
  // The labels, two columns of six under the mountain.
  const labels = AREAS.map((_, i) => ({ u: (i % 2) * LABEL_W, v: BASE_H + Math.floor(i / 2) * LABEL_H }));
  const stages = STAGES.map((_, upTo) => {
    const c = land();
    places(c, upTo);
    const pixels = new Uint8Array(OV_W * OV_H);
    const blit = (src: Uint8Array, w: number, h: number, u: number, v: number) => {
      for (let y = 0; y < h; y++) pixels.set(src.subarray(y * w, y * w + w), (v + y) * OV_W + u);
    };
    blit(c.pixels, BASE_W, BASE_H, 0, 0);
    markers.forEach((m, s) => {
      if (s > upTo) return;
      for (let y = 0; y < m.at.h; y++)
        for (let x = 0; x < m.at.w; x++) {
          const i = (m.at.y + y) * BASE_W + m.at.x + x;
          if (c.stage[i] === s) pixels[(m.v + y) * OV_W + m.u + x] = c.pixels[i]!;
        }
    });
    AREAS.forEach((a, i) => blit(label(a.name), LABEL_W, LABEL_H, labels[i]!.u, labels[i]!.v));
    blit(arrows(), 32, 8, ARROWS.u, ARROWS.v);
    return { width: OV_W, height: OV_H, clut: CLUT, pixels, clutAt: [0, 480] as const, imageAt: [0, 0] as const };
  });
  return { stages, markers, labels };
}

/** The browser as the screen shows it for a stage, with stage `chosen` bright and the others dim, and an area's label: for previews. */
export function browserPreview(o: Overview, upTo: number, chosen: number, area: number, zoom = 3): { width: number; height: number; rgb: Uint8Array } {
  const t = o.stages[upTo]!;
  const W = 176;
  const H = 104;
  const rgb = new Uint8Array(W * zoom * H * zoom * 3);
  const px = (x: number, y: number, index: number, k: number) => {
    if (!index || x < 0 || y < 0 || x >= W || y >= H) return;
    const c = rgbOf(t.clut[index]!).map((v) => (v * k) / 128);
    for (let dy = 0; dy < zoom; dy++)
      for (let dx = 0; dx < zoom; dx++) rgb.set(c, (((y * zoom + dy) * W * zoom) + x * zoom + dx) * 3);
  };
  // Screen positions less (25, 24), so the panel sits near the corner.
  const ox = BASE_SCREEN.x - 25;
  const oy = BASE_SCREEN.y - 24;
  for (let y = 0; y < BASE_H; y++) for (let x = 0; x < BASE_W; x++) px(ox + x, oy + y, t.pixels[y * OV_W + x]!, 128);
  o.markers.forEach((m, s) => {
    if (s > upTo) return;
    for (let y = 0; y < m.at.h; y++)
      for (let x = 0; x < m.at.w; x++) px(ox + m.at.x + x, oy + m.at.y + y, t.pixels[(m.v + y) * OV_W + m.u + x]!, s === chosen ? 128 : 64);
  });
  const l = o.labels[area]!;
  for (let y = 0; y < LABEL_H; y++)
    for (let x = 0; x < LABEL_W; x++) px(LABEL_SCREEN.x - 25 + x, LABEL_SCREEN.y - 24 + y, t.pixels[(l.v + y) * OV_W + l.u + x]!, 128);
  return { width: W * zoom, height: H * zoom, rgb };
}
