// Draw an area's floor plan as RE1 draws its maps: a 128 x 128 picture of CLUT
// indices, of which the map screen shows the top 128 x 100. Each room has a
// block of six palette entries of its own, so the engine can light it, dim it
// or hide it by rewriting the palette alone (map_display_load_textures):
//
//   7               the walls of every room, shown once the map is hers
//   13 + 6k + 0     room k's doors
//   13 + 6k + 1     room k's furniture
//   13 + 6k + 3     room k's floor
//
// Room k is the area's k-th place in maps.ts. The colours are RE1's own map
// colours: grey walls, gold doors, green floors.
import { AREAS } from '../plan/maps.ts';
import { isHole, SIDES, UNITS } from './floors.ts';
import { organic } from './outline.ts';
import { doorOnOutline, extent, inRoom, planArea, type AreaPlan, type Placed, type Pt } from './plans.ts';
import { ps1, rgbOf, type Tim8 } from './tim.ts';

export const MAP_W = 128;
export const MAP_H = 128;
/** The rows the map screen shows; the rest of the picture is never drawn. */
export const MAP_SHOWN = 100;
export const WALL = 7;
export const blockOf = (k: number) => 13 + 6 * k;
export const DOOR = 0;
export const MARK = 1;
export const FILL = 3;
/** Room blocks the picture's palette has room for. */
export const MAX_ROOMS = Math.floor((256 - 13) / 6);

/** RE1's map colours. */
const COLOURS = {
  wall: ps1(176, 176, 176),
  door: ps1(224, 176, 32),
  mark: ps1(8, 56, 0),
  fill: ps1(32, 104, 0, true),
};

export function mapClut(rooms: number): Uint16Array {
  if (rooms > MAX_ROOMS) throw new Error(`${rooms} rooms, but a map's palette has blocks for ${MAX_ROOMS}`);
  const clut = new Uint16Array(256);
  clut[WALL] = COLOURS.wall;
  for (let k = 0; k < rooms; k++) {
    const b = blockOf(k);
    clut[b + DOOR] = COLOURS.door;
    clut[b + MARK] = COLOURS.mark;
    clut[b + 2] = COLOURS.mark;
    clut[b + FILL] = COLOURS.fill;
    clut[b + 4] = COLOURS.fill;
  }
  return clut;
}

/** The most pixels to a metre: a small area stays at a size RE1's maps draw rooms. */
const MAX_SCALE = 5;
const MARGIN = 4;
/** A trail's width in metres; never under three pixels, a floor between two walls. */
const TRAIL_W = 1.6;

export interface Drawn {
  readonly plan: AreaPlan;
  /** MAP_W x MAP_H indices. */
  readonly pixels: Uint8Array;
  /** Which room's outline each pixel is in, by palette block (-1: none; the ways between are not counted). */
  readonly owner: Int16Array;
  /** Each door's pixel on its room's outline. */
  readonly doors: readonly { readonly place: string; readonly to: string; readonly x: number; readonly y: number }[];
  /** Pixels to a metre, and where the plan's origin falls. */
  readonly scale: number;
  readonly origin: Pt;
}

/** Whether a room point is furniture in a building, drawn as a mark on its floor. */
function markAt(r: Placed, x: number, z: number): boolean {
  if (!r.floor.inside) return false;
  return r.floor.solids.some((s) => !isHole(s) && (s.round ? Math.hypot((x - (s.x0 + s.x1) / 2) / Math.max(1, (s.x1 - s.x0) / 2), (z - (s.z0 + s.z1) / 2) / Math.max(1, (s.z1 - s.z0) / 2)) <= 1 : x >= s.x0 && x < s.x1 && z >= s.z0 && z < s.z1));
}

export function drawArea(areaId: string): Drawn {
  const plan = planArea(areaId);
  const e = extent(plan);
  const scale = Math.min(MAX_SCALE, (MAP_W - 2 * MARGIN) / (e.x1 - e.x0), (MAP_SHOWN - 2 * MARGIN) / (e.y1 - e.y0));
  const origin = {
    x: Math.floor((MAP_W - (e.x1 - e.x0) * scale) / 2 - e.x0 * scale),
    y: Math.floor((MAP_SHOWN - (e.y1 - e.y0) * scale) / 2 - e.y0 * scale),
  };
  const toPx = (p: Pt) => ({ x: p.x * scale + origin.x, y: p.y * scale + origin.y });
  const centreOf = (px: number, py: number): Pt => ({ x: (px + 0.5 - origin.x) / scale, y: (py + 0.5 - origin.y) / scale });
  const owner = new Int16Array(MAP_W * MAP_H).fill(-1);
  const roomOf = new Int16Array(MAP_W * MAP_H).fill(-1);
  const mark = new Uint8Array(MAP_W * MAP_H);
  const cable = new Uint8Array(MAP_W * MAP_H);
  const set = (px: number, py: number, k: number) => {
    if (px >= 0 && py >= 0 && px < MAP_W && py < MAP_SHOWN) owner[py * MAP_W + px] = k;
  };
  // Each room's palette block is its place in the area's list (maps.ts), drawn or not.
  const places = AREAS.find((a) => a.id === areaId)!.places;
  const index = new Map(plan.rooms.map((r) => [r.floor.place, places.indexOf(r.floor.place)]));
  // The ways first, under the rooms; each half in the colours of the room at its end.
  const r = Math.max(1.5, (TRAIL_W * scale) / 2);
  for (const t of plan.trails) {
    const pts = t.points.map(toPx);
    let total = 0;
    const lengths = pts.slice(1).map((p, i) => Math.hypot(p.x - pts[i]!.x, p.y - pts[i]!.y));
    const all = lengths.reduce((s, l) => s + l, 0);
    for (let i = 1; i < pts.length; i++) {
      const [a, b] = [pts[i - 1]!, pts[i]!];
      const n = Math.max(1, Math.ceil(lengths[i - 1]! * 2));
      for (let s = 0; s <= n; s++) {
        const x = a.x + ((b.x - a.x) * s) / n;
        const y = a.y + ((b.y - a.y) * s) / n;
        const along = (total + (lengths[i - 1]! * s) / n) / (all || 1);
        const k = index.get(t.to !== undefined && along >= 0.5 ? t.to : t.from)!;
        if (t.kind === 'cable') {
          // A ride's cable: a dashed line, a pixel wide, in the walls' colour.
          if (Math.floor((total + (lengths[i - 1]! * s) / n) / 3) % 2 === 0) {
            const px = Math.floor(x);
            const py = Math.floor(y);
            if (px >= 0 && py >= 0 && px < MAP_W && py < MAP_SHOWN) cable[py * MAP_W + px] = 1;
          }
          continue;
        }
        const w = t.kind === 'step' ? Math.max(1.5, r * 0.8) : r;
        for (let py = Math.floor(y - w); py <= Math.ceil(y + w); py++)
          for (let px = Math.floor(x - w); px <= Math.ceil(x + w); px++) if (Math.hypot(px + 0.5 - x, py + 0.5 - y) <= w) set(px, py, k);
      }
      total += lengths[i - 1]!;
    }
  }
  // Outdoor rooms, then buildings: a building's straight walls are drawn over a yard's wandering edge.
  const order = plan.rooms.map((rm) => [rm, index.get(rm.floor.place)!] as const).sort(([a], [b]) => Number(organic(b.floor)) - Number(organic(a.floor)));
  for (const [rm, k] of order) {
    for (let py = 0; py < MAP_SHOWN; py++)
      for (let px = 0; px < MAP_W; px++) {
        const p = centreOf(px, py);
        if (!inRoom(rm, p)) continue;
        owner[py * MAP_W + px] = k;
        roomOf[py * MAP_W + px] = k;
        mark[py * MAP_W + px] = markAt(rm, (p.x - rm.at.x) * UNITS, (p.y - rm.at.y) * UNITS) ? 1 : 0;
      }
  }
  const pixels = new Uint8Array(MAP_W * MAP_H);
  const own = (x: number, y: number) => (x < 0 || y < 0 || x >= MAP_W || y >= MAP_SHOWN ? -1 : owner[y * MAP_W + x]!);
  for (let y = 0; y < MAP_SHOWN; y++)
    for (let x = 0; x < MAP_W; x++) {
      const k = own(x, y);
      if (k < 0) {
        if (cable[y * MAP_W + x]) pixels[y * MAP_W + x] = WALL;
        continue;
      }
      // A wall where the floor meets nothing, or a room drawn later in the
      // area's order: one pixel between two rooms, as RE1's walls are.
      const edge = [own(x - 1, y), own(x + 1, y), own(x, y - 1), own(x, y + 1)].some((n) => n < 0 || n > k);
      pixels[y * MAP_W + x] = edge ? WALL : blockOf(k) + (mark[y * MAP_W + x] ? MARK : FILL);
    }
  // Doors: on the outline where each opens (plans.ts doorOnOutline), two pixels deep.
  const doors: { place: string; to: string; x: number; y: number }[] = [];
  const inside = (x: number, y: number) => (x < 0 || y < 0 || x >= MAP_W || y >= MAP_SHOWN ? -1 : roomOf[y * MAP_W + x]!);
  for (const rm of plan.rooms) {
    const k = index.get(rm.floor.place)!;
    for (const d of rm.floor.doors) {
      const side = d.side;
      const [dx, dy] = SIDES[side]!;
      const { at, edge } = doorOnOutline(rm, d);
      const p = toPx(at);
      let wx = Math.floor(p.x);
      let wy = Math.floor(p.y);
      // The point in metres lands on a pixel: onto the room's, and on its edge.
      for (let i = 0; i < 2 && inside(wx, wy) !== k; i++) [wx, wy] = [wx - dx, wy - dy];
      if (inside(wx, wy) !== k) continue;
      for (let i = 0; edge && i < 2 && inside(wx + dx, wy + dy) === k; i++) [wx, wy] = [wx + dx, wy + dy];
      doors.push({ place: rm.floor.place, to: d.to, x: wx, y: wy });
      const along = side % 2 === 0 ? d.zone.x1 - d.zone.x0 : d.zone.z1 - d.zone.z0;
      const span = Math.max(2, Math.min(4, Math.round((along / UNITS) * scale)));
      for (let depth = 0; depth < 2; depth++)
        for (let s = 0; s < span; s++) {
          const off = s - Math.floor((span - 1) / 2);
          const x = wx - dx * depth + (dy !== 0 ? off : 0);
          const y = wy - dy * depth + (dx !== 0 ? off : 0);
          if (inside(x, y) === k) pixels[y * MAP_W + x] = blockOf(k) + DOOR;
        }
    }
  }
  return { plan, pixels, owner: roomOf, doors, scale, origin };
}

/** An area's map file: its picture and palette, placed in VRAM where RE1's map files are. */
export function areaTim(areaId: string): Tim8 {
  const d = drawArea(areaId);
  return { width: MAP_W, height: MAP_H, clut: mapClut(AREAS.find((a) => a.id === areaId)!.places.length), pixels: d.pixels, clutAt: [0, 480], imageAt: [768, 0] };
}

/** What the map screen knows when it draws an area. */
export interface MapState {
  /** She has the area's map. */
  readonly owned: boolean;
  /** Rooms (palette blocks) she has been in. */
  readonly visited: ReadonlySet<number>;
  /** Her room's block, when she is in this area. */
  readonly here?: number;
  /** Whether the blinking room is at its bright phase. */
  readonly lit?: boolean;
}

/** Halve a colour's channels, keeping its top bit: an unvisited room on a map she owns (her mode). */
export const dim = (c: number) => ((c >> 1) & 0x3def) | (c & 0x8000);

/**
 * The palette the engine draws an area with, rewritten as
 * map_display_load_textures does in her mode: rooms she has not seen are
 * hidden, or dim walls and doors once the map is hers; her room is red.
 */
export function paletteFor(clut: Uint16Array, rooms: number, s: MapState): Uint16Array {
  const out = new Uint16Array(clut);
  if (!s.owned) out.fill(0, 7, 13);
  for (let k = 0; k < rooms; k++) {
    const b = blockOf(k);
    if (!s.visited.has(k)) {
      if (!s.owned) out.fill(0, b, b + 6);
      else for (let i = 1; i <= 3; i++) out[b + i] = dim(out[b + i]!);
    } else if (k === s.here) {
      for (let i = 1; i <= 3; i++) out[b + i] = s.lit === false ? 0 : 0x1f;
    }
  }
  return out;
}

/** The map as the screen shows it, over a dark blue grid, `zoom` pixels to one. */
export function preview(t: Tim8, rooms: number, s: MapState, zoom = 3): { width: number; height: number; rgb: Uint8Array } {
  const clut = paletteFor(t.clut, rooms, s);
  const w = t.width * zoom;
  const h = MAP_SHOWN * zoom;
  const rgb = new Uint8Array(w * h * 3);
  for (let y = 0; y < h; y++)
    for (let x = 0; x < w; x++) {
      const i = t.pixels[Math.floor(y / zoom) * t.width + Math.floor(x / zoom)]!;
      const grid = Math.floor(x / zoom) % 8 === 0 || Math.floor(y / zoom) % 8 === 0;
      const c = i && clut[i] ? rgbOf(clut[i]!) : grid ? [16, 40, 96] : [8, 8, 72];
      rgb.set(c, (y * w + x) * 3);
    }
  return { width: w, height: h, rgb };
}
