// What a floor plan needs to know of each room of her day: its walkable
// floor (renders/room.json: the bounds, the gaps cut out of them, the walls
// and furniture), and its doors (the door_aot_set lines of its room.c), each
// with the side of the room it opens on. Game units throughout; a metre is
// 1700 (reb.UNITS).
import { existsSync, readFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { dayRooms } from '../day/rooms.ts';
import { day } from '../plan/day.ts';

const dayDir = path.join(path.dirname(fileURLToPath(import.meta.url)), '..', 'day');

export const UNITS = 1700;

export type Rect = { readonly x0: number; readonly z0: number; readonly x1: number; readonly z1: number };
/** A side of a room, in its own axes: -z, +x, +z, -x. Turning a room a quarter turn adds one. */
export type Side = 0 | 1 | 2 | 3;
export const SIDES: readonly (readonly [number, number])[] = [
  [0, -1],
  [1, 0],
  [0, 1],
  [-1, 0],
];

export interface Door {
  /** The place it leads to. */
  readonly to: string;
  readonly zone: Rect;
  /** The side of the room it opens on, outward. */
  readonly side: Side;
}

export interface RoomFloor {
  /** The plan's place id. */
  readonly place: string;
  readonly bounds: Rect;
  /** Parts of the bounds that are not floor. */
  readonly voids: readonly Rect[];
  /** Solid things on the floor: buildings drawn as holes, furniture as marks. */
  readonly solids: readonly (Rect & { readonly round: boolean })[];
  readonly doors: readonly Door[];
  readonly inside: boolean;
}

interface RoomJson {
  bounds: Rect;
  voids?: Rect[];
  walls?: (Rect & { shape: 'box' | 'circle'; name?: string })[];
}

/** The place a room name (ROOM_<stage><id>, stage from 1) is, if it is one of her day's. */
function placeOfRoomName(name: string): string | undefined {
  const m = /^ROOM_(\d)([0-9A-F]{2})$/i.exec(name);
  if (!m) return undefined;
  const [stage, room] = [Number(m[1]) - 1, parseInt(m[2]!, 16)];
  if (stage === 0 && room === 0) return 'save';
  const slug = dayRooms.find((r) => r.stage === stage && r.room === room)?.slug;
  return slug && placeOfSlug(slug);
}

const placeOfSlug = (slug: string) => day.places.find((p) => (p.room ?? p.id) === slug)?.id;
export const slugOfPlace = (place: string) => day.places.find((p) => p.id === place)?.room ?? place;

interface RawDoor {
  to: string;
  zone: Rect;
  /** Where she lands in the room it leads to. */
  arrive: { x: number; z: number };
}

/** The doors a room's script sets, once each by where they lead. */
function scriptDoors(slug: string): RawDoor[] {
  const file = path.join(dayDir, slug, 'room.c');
  if (!existsSync(file)) return [];
  const out: RawDoor[] = [];
  for (const m of readFileSync(file, 'utf8').matchAll(/door_aot_set\(([^;]*)\);/g)) {
    const a = m[1]!.replace(/\/\*.*?\*\//g, '').split(',').map((t) => t.trim());
    const to = placeOfRoomName(a[10]!);
    if (!to || out.some((d) => d.to === to)) continue;
    const [x, z, w, d] = a.slice(1, 5).map(Number) as [number, number, number, number];
    out.push({ to, zone: { x0: x, z0: z, x1: x + w, z1: z + d }, arrive: { x: Number(a[11]), z: Number(a[13]) } });
  }
  return out;
}

/**
 * The side a door opens on. A zone against the room's edge opens through that
 * edge. One out in the room, a building's door in a yard, opens away from
 * where she stands on coming back through it.
 */
function sideOf(zone: Rect, bounds: Rect, arrive: { x: number; z: number } | undefined): Side {
  const gaps = [zone.z0 - bounds.z0, bounds.x1 - zone.x1, bounds.z1 - zone.z1, zone.x0 - bounds.x0];
  const nearest = gaps.indexOf(Math.min(...gaps)) as Side;
  if (gaps[nearest]! <= 340 || !arrive) return nearest;
  const dx = (zone.x0 + zone.x1) / 2 - arrive.x;
  const dz = (zone.z0 + zone.z1) / 2 - arrive.z;
  return Math.abs(dx) > Math.abs(dz) ? (dx > 0 ? 1 : 3) : dz > 0 ? 2 : 0;
}

/** Furniture this big or more, or anything named a footprint this big, is a hole in the floor plan; less is a mark. */
const HOLE_M2 = 6;

/** The mansion's 1F save room is RE1's own and has no scene: a room of its size, the hatch she comes up through in its floor. */
const SAVE_ROOM: RoomFloor = {
  place: 'save',
  bounds: { x0: 0, z0: 0, x1: 7 * UNITS, z1: 5 * UNITS },
  voids: [],
  solids: [],
  doors: [{ to: 'crawl', zone: { x0: 2.6 * UNITS, z0: 2.6 * UNITS, x1: 3.6 * UNITS, z1: 3.6 * UNITS }, side: 2 }],
  inside: true,
};

let cache: Map<string, RoomFloor> | undefined;

/** Every place's floor, by place id; a place whose room is not rendered yet is missing. */
export function floors(): ReadonlyMap<string, RoomFloor> {
  if (cache) return cache;
  cache = new Map([['save', SAVE_ROOM]]);
  const raw = new Map(day.places.map((p) => [p.id, scriptDoors(slugOfPlace(p.id))]));
  for (const p of day.places) {
    if (p.id === 'save') continue;
    const slug = slugOfPlace(p.id);
    const file = path.join(dayDir, slug, 'renders', 'room.json');
    if (!existsSync(file)) continue;
    const json = JSON.parse(readFileSync(file, 'utf8')) as RoomJson;
    const spec = dayRooms.find((r) => r.slug === slug);
    const inside = spec && 'inside' in spec ? spec.inside : slug === 'lookout' || slug === 'shed';
    const doors = raw.get(p.id)!.map((d): Door => {
      // Where she stands here on coming back through it: the far side's door says.
      const back = raw.get(d.to)?.find((b) => b.to === p.id)?.arrive;
      return { to: d.to, zone: d.zone, side: sideOf(d.zone, json.bounds, back) };
    });
    const solids = (json.walls ?? []).map((w) => ({ x0: w.x0, z0: w.z0, x1: w.x1, z1: w.z1, round: w.shape === 'circle' }));
    cache.set(p.id, { place: p.id, bounds: json.bounds, voids: json.voids ?? [], solids, doors, inside });
  }
  return cache;
}

/** A solid that the plan draws as a hole rather than a mark. */
export const isHole = (s: Rect) => ((s.x1 - s.x0) * (s.z1 - s.z0)) / (UNITS * UNITS) >= HOLE_M2;
