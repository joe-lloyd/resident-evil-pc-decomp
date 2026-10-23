// Rebecca's day as the game has it: every room's doors and pickups, read from
// the room scripts the overlay is built from (rebecca/day/<slug>/room.c), so a
// playthrough walks the same doors the game has rather than the plan's idea of
// them. Rooms are named by their folder (slug); the mansion's save room, which
// she reaches from under the floor, is ROOM100 and named "save".
import { readdirSync, readFileSync, existsSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { dayRooms } from '../rebecca/day/rooms.ts';

const dayDir = path.join(path.dirname(fileURLToPath(import.meta.url)), '..', 'rebecca', 'day');

export type Slug = string;
export interface Zone { x: number; z: number; w: number; d: number }

export interface Door {
  readonly from: Slug;
  readonly to: Slug;
  readonly zone: Zone;
  /** Where the door puts her in `to`. */
  readonly arrive: { x: number; z: number; angle: number };
  /** Fires as she walks into it, rather than on the action button. */
  readonly touch: boolean;
  /**
   * A locked door: the key item it takes and its FG_LOCK flag, raised once it
   * is open. `use`: the item does not turn by itself as she tries the door
   * (bolt cutters, a crowbar); she uses it from her case there.
   */
  readonly lock?: { item: number; flag: number; use?: boolean };
}

export interface Pickup {
  readonly room: Slug;
  readonly item: number;
  /** How many: rounds in a clip, uses in a key item. */
  readonly qty: number;
  /** FG_ITEM flag: clear once she has taken it. */
  readonly flag: number;
  readonly zone: Zone;
}

/** An item box (SCE_ITEMBOX): her bag on one side, the shared store on the other. */
export interface Box {
  readonly room: Slug;
  readonly zone: Zone;
}

const SAVE_ROOM = { slug: 'save', stage: 0, room: 0 } as const;
const rooms = [...dayRooms.map((r) => ({ slug: r.slug, stage: r.stage, room: r.room })), SAVE_ROOM];

/** The slug of the room at (stage, room), stage counted from 0 as the game does. */
export function slugAt(stage: number, room: number): Slug | undefined {
  return rooms.find((r) => r.stage === stage && r.room === room)?.slug;
}

/** ROOM_31A is stage 3 counted from 1, room 0x1A. */
function roomName(token: string): Slug {
  const m = /^ROOM_([0-9A-F])([0-9A-F]{2})$/.exec(token);
  if (!m) throw new Error(`not a room: ${token}`);
  const slug = slugAt(parseInt(m[1]!, 16) - 1, parseInt(m[2]!, 16));
  if (!slug) throw new Error(`no day room is ${token}`);
  return slug;
}

const args = (line: string, call: string): string[] | undefined => {
  const m = new RegExp(`${call}\\((.*)\\);`).exec(line.replace(/\/\*.*?\*\//g, ''));
  return m ? m[1]!.split(',').map((a) => a.trim()) : undefined;
};

function readRoom(slug: Slug): { doors: Door[]; pickups: Pickup[]; boxes: Box[] } {
  const doors: Door[] = [];
  const pickups: Pickup[] = [];
  const boxes: Box[] = [];
  const uses: Zone[] = [];
  const text = readFileSync(path.join(dayDir, slug, 'room.c'), 'utf8');
  // Init procedure only: main's doors are rewrites of the same ones.
  for (const line of text.split('\n')) {
    if (line.startsWith('// main procedure')) break;
    const d = args(line, 'door_aot_set');
    if (d) {
      // id, x, z, w, d, 4 animation bytes, lock id, room, x, y, z, angle, key item, trigger
      const n = d.map(Number);
      const to = roomName(d[10]!);
      const lockId = n[9]!;
      const door: Door = {
        from: slug,
        to,
        zone: { x: n[1]!, z: n[2]!, w: n[3]!, d: n[4]! },
        arrive: { x: n[11]!, z: n[13]!, angle: n[14]! },
        touch: (n[16]! & 0x80) === 0,
        ...(lockId & 0x80 ? { lock: { item: n[15]!, flag: lockId & 0x7f } } : {}),
      };
      // A door a script writes twice (before and after a change) is one way.
      if (!doors.some((o) => o.to === to && o.zone.x === door.zone.x && o.zone.z === door.zone.z)) doors.push(door);
      continue;
    }
    const it = args(line, 'item_aot_set');
    if (it) {
      // id, x, z, w, d, item, count, model, 255, 8 placement bytes, flag, ...
      const n = it.map(Number);
      pickups.push({ room: slug, item: n[5]!, qty: n[6]!, flag: n[17]!, zone: { x: n[1]!, z: n[2]!, w: n[3]!, d: n[4]! } });
      continue;
    }
    const aot = args(line, 'aot_set');
    if (aot?.[5] === 'SCE_ITEMBOX') {
      const n = aot.map(Number);
      boxes.push({ room: slug, zone: { x: n[1]!, z: n[2]!, w: n[3]!, d: n[4]! } });
    }
    if (aot?.[5] === 'SCE_USEITEM') {
      const n = aot.map(Number);
      uses.push({ x: n[1]!, z: n[2]!, w: n[3]!, d: n[4]! });
    }
  }
  // A lock with an item-use zone over its door is one she uses the item on.
  const same = (a: Zone, b: Zone) => a.x === b.x && a.z === b.z && a.w === b.w && a.d === b.d;
  const marked = doors.map((d) => (d.lock && uses.some((u) => same(u, d.zone)) ? { ...d, lock: { ...d.lock, use: true } } : d));
  return { doors: marked, pickups, boxes };
}

export interface World {
  readonly doors: readonly Door[];
  readonly pickups: readonly Pickup[];
  readonly boxes: readonly Box[];
}

export function loadWorld(): World {
  const slugs = readdirSync(dayDir).filter((f) => existsSync(path.join(dayDir, f, 'room.c')));
  const all = slugs.map(readRoom);
  return { doors: all.flatMap((r) => r.doors), pickups: all.flatMap((r) => r.pickups), boxes: all.flatMap((r) => r.boxes) };
}

/** The fewest doors from `from` to `to`, leaving out `closed` ones; undefined when there is no way. */
export function route(world: World, from: Slug, to: Slug, closed: (d: Door) => boolean): Door[] | undefined {
  if (from === to) return [];
  const back = new Map<Slug, Door>();
  const queue: Slug[] = [from];
  while (queue.length) {
    const here = queue.shift()!;
    for (const d of world.doors) {
      if (d.from !== here || d.to === from || back.has(d.to) || closed(d)) continue;
      back.set(d.to, d);
      if (d.to === to) {
        const way: Door[] = [];
        for (let at = to; at !== from; at = back.get(at)!.from) way.unshift(back.get(at)!);
        return way;
      }
      queue.push(d.to);
    }
  }
  return undefined;
}
