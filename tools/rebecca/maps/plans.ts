// Lay out each area of her map as the research map of the mountain does
// (plan/research/layout.ts), north up, each room at its real size by its
// outline (outline.ts). The room with most ways to the others goes first;
// each other room goes out from the room that leads to it, on the bearing
// the research map has between the two, as near as it fits: a gap from
// every room, a trail's length from a room it walks to. So the area keeps
// the research map's shape while its rooms are big enough to read. The ways
// between rooms run from door to door: a trail that wanders between two
// places outdoors, a short straight way into a building, a cable for a
// ride, and a stub of trail out of the area where a walk leaves it.
import { AREAS } from '../plan/maps.ts';
import { day } from '../plan/day.ts';
import { LAYOUT } from '../plan/research/layout.ts';
import { floors, SIDES, UNITS, type Door, type RoomFloor, type Side } from './floors.ts';
import { CELL, inOutline, noise, organic, outlineOf, type Outline } from './outline.ts';

/** A point in the plan, in metres: x east, y south, down the page. */
export type Pt = { readonly x: number; readonly y: number };

export interface Placed {
  readonly floor: RoomFloor;
  readonly outline: Outline;
  /** Where the room's origin lands. */
  readonly at: Pt;
}

/** How a way between two rooms is drawn. */
export type WayKind = 'trail' | 'step' | 'cable';

export interface Trail {
  readonly from: string;
  /** The room at the far end; undefined for a stub out of the area. */
  readonly to?: string;
  readonly kind: WayKind;
  /** The line it follows, from `from`'s door. */
  readonly points: readonly Pt[];
}

export interface AreaPlan {
  readonly area: string;
  /** In the area's order (maps.ts), which is the order of its rooms' palette blocks. */
  readonly rooms: readonly Placed[];
  readonly trails: readonly Trail[];
  /** Rooms whose outlines meet another's: the layout's faults, empty when it is clean. */
  readonly overlaps: readonly string[];
}

/** A room point (game units) in the plan (metres). */
export function toPlan(p: Placed, x: number, z: number): Pt {
  return { x: x / UNITS + p.at.x, y: z / UNITS + p.at.y };
}

/** Whether a plan point is in a placed room's outline. */
export const inRoom = (p: Placed, pt: Pt) => inOutline(p.outline, pt.x - p.at.x, pt.y - p.at.y);

/** The middle of a door's outer face, in the room's units. */
function doorFace(d: Door): { x: number; z: number } {
  const cx = (d.zone.x0 + d.zone.x1) / 2;
  const cz = (d.zone.z0 + d.zone.z1) / 2;
  return [
    { x: cx, z: d.zone.z0 },
    { x: d.zone.x1, z: cz },
    { x: cx, z: d.zone.z1 },
    { x: d.zone.x0, z: cz },
  ][d.side]!;
}

/** Where a door is in the plan, and the way it faces. */
export function doorInPlan(p: Placed, d: Door): { at: Pt; side: Side } {
  const f = doorFace(d);
  return { at: toPlan(p, f.x, f.z), side: d.side };
}

/** How far past a door its room's floor may run and the door still be on the floor's edge, in metres. */
export const DOOR_REACH = 1.5;

/**
 * Where a door meets its room's outline: from the door, out along the way it
 * faces to the last point of the outline, or in to the first when the door
 * is outside it. A door with floor past DOOR_REACH beyond it stands out in
 * the floor (a tower's door in its clearing) and stays where it is.
 */
export function doorOnOutline(p: Placed, d: Door): { at: Pt; edge: boolean } {
  const { at, side } = doorInPlan(p, d);
  const [dx, dy] = SIDES[side]!;
  const step = (t: number): Pt => ({ x: at.x + dx * t, y: at.y + dy * t });
  if (!inRoom(p, at)) {
    for (let t = 0; t >= -3; t -= 0.05) if (inRoom(p, step(t))) return { at: step(t), edge: true };
    return { at, edge: false };
  }
  for (let t = 0; t <= DOOR_REACH; t += 0.05) if (!inRoom(p, step(t + 0.05))) return { at: step(t), edge: true };
  return { at, edge: false };
}

/** The gap kept between two rooms' outlines, in metres. */
const GAP = 1.5;
/** How far a stub of trail runs out of the area, in metres. */
const STUB = 5;

/** A room's outline grown by `by` metres, for the gap test. */
function widened(o: Outline, by: number): Outline {
  const r = Math.ceil(by / CELL);
  const cols = o.cols + 2 * r;
  const rows = o.rows + 2 * r;
  const cells = new Uint8Array(cols * rows);
  for (let j = 0; j < o.rows; j++)
    for (let i = 0; i < o.cols; i++) {
      if (!o.cells[j * o.cols + i]) continue;
      for (let dj = -r; dj <= r; dj++)
        for (let di = -r; di <= r; di++) if (di * di + dj * dj <= r * r) cells[(j + r + dj) * cols + i + r + di] = 1;
    }
  return { x0: o.x0 - r * CELL, y0: o.y0 - r * CELL, cols, rows, cells };
}

/** Whether two outlines, at plan offsets `a` and `b`, share a cell. */
function touch(oa: Outline, a: Pt, ob: Outline, b: Pt): boolean {
  const x0 = Math.max(oa.x0 + a.x, ob.x0 + b.x);
  const y0 = Math.max(oa.y0 + a.y, ob.y0 + b.y);
  const x1 = Math.min(oa.x0 + a.x + oa.cols * CELL, ob.x0 + b.x + ob.cols * CELL);
  const y1 = Math.min(oa.y0 + a.y + oa.rows * CELL, ob.y0 + b.y + ob.rows * CELL);
  for (let y = y0 + CELL / 2; y < y1; y += CELL)
    for (let x = x0 + CELL / 2; x < x1; x += CELL) if (inOutline(oa, x - a.x, y - a.y) && inOutline(ob, x - b.x, y - b.y)) return true;
  return false;
}

const linkOf = (a: string, b: string) => day.links.find((l) => (l.from === a && l.to === b) || (l.from === b && l.to === a));
const spot = (place: string): Pt => {
  const at = LAYOUT[place] ?? day.places.find((p) => p.id === place)!.at;
  return { x: at[0], y: at[1] };
};

/** A room placed with its outline's middle at `c`. */
function placeAt(floor: RoomFloor, c: Pt): Placed {
  const b = floor.bounds;
  return { floor, outline: outlineOf(floor), at: { x: c.x - (b.x0 + b.x1) / 2 / UNITS, y: c.y - (b.z0 + b.z1) / 2 / UNITS } };
}

/** A line from a to b that wanders off the straight like a path through woods. */
export function wander(a: Pt, b: Pt, key: string): Pt[] {
  const dx = b.x - a.x;
  const dy = b.y - a.y;
  const length = Math.hypot(dx, dy) || 1;
  const nx = -dy / length;
  const ny = dx / length;
  const n = noise(key);
  const steps = Math.max(2, Math.ceil(length / 0.5));
  return Array.from({ length: steps + 1 }, (_, i) => {
    const s = i / steps;
    // Pinned at both doors, free in the middle: up to a sixth of its length off the line.
    const bend = Math.sin(Math.PI * s) * (length / 6) * (2 * n(s * 9, 0.5) - 1);
    return { x: a.x + dx * s + nx * bend, y: a.y + dy * s + ny * bend };
  });
}

/** The ways out of a door: its plan point, a little way out of the room. */
function doorOut(p: Placed, d: Door): Pt {
  const { at, side } = doorInPlan(p, d);
  const [dx, dy] = SIDES[side]!;
  return { x: at.x + dx * 0.5, y: at.y + dy * 0.5 };
}

function ways(rooms: readonly Placed[], inArea: ReadonlySet<string>): Trail[] {
  const by = new Map(rooms.map((r) => [r.floor.place, r]));
  const out: Trail[] = [];
  for (const r of rooms) {
    for (const d of r.floor.doors) {
      const link = linkOf(r.floor.place, d.to);
      const a = doorOut(r, d);
      if (!inArea.has(d.to)) {
        // A walk out of the area: a stub of trail toward where it goes.
        if (link?.kind !== 'walk') continue;
        const t = spot(d.to);
        const f = spot(r.floor.place);
        const len = Math.hypot(t.x - f.x, t.y - f.y) || 1;
        const [sx, sy] = SIDES[d.side]!;
        // Out of the door, then bending toward the other place.
        const dir = { x: sx + (t.x - f.x) / len, y: sy + (t.y - f.y) / len };
        const dl = Math.hypot(dir.x, dir.y) || 1;
        out.push({ from: r.floor.place, kind: 'trail', points: wander(a, { x: a.x + (dir.x / dl) * STUB, y: a.y + (dir.y / dl) * STUB }, `${r.floor.place}>${d.to}`) });
        continue;
      }
      // Each way once, from the room listed first in the area.
      const other = by.get(d.to);
      if (!other || rooms.indexOf(other) < rooms.indexOf(r)) continue;
      const back = other.floor.doors.find((x) => x.to === r.floor.place);
      if (!back) continue;
      const b = doorOut(other, back);
      const kind: WayKind = link?.kind === 'ride' || link?.kind === 'lift' ? 'cable' : link?.kind === 'walk' && organic(r.floor) && organic(other.floor) ? 'trail' : 'step';
      out.push({ from: r.floor.place, to: d.to, kind, points: kind === 'trail' ? wander(a, b, `${r.floor.place}>${d.to}`) : [a, b] });
    }
  }
  return out;
}

const overlapsOf = (rooms: readonly Placed[]) => {
  const out: string[] = [];
  for (let i = 0; i < rooms.length; i++)
    for (let j = i + 1; j < rooms.length; j++)
      if (touch(rooms[i]!.outline, rooms[i]!.at, rooms[j]!.outline, rooms[j]!.at)) out.push(`${rooms[i]!.floor.place} and ${rooms[j]!.floor.place}`);
  return out;
};

/** The least length of a trail between two places outdoors, in metres. */
const TRAIL = 4;
/** Turns off the research map's bearing a room may take to find space, and what each costs, in metres of trail. */
const TURNS = [0, 15, -15, 30, -30, 45, -45].map((d) => ({ by: (d * Math.PI) / 180, cost: Math.abs(d) / 15 }));

export function planArea(areaId: string): AreaPlan {
  const area = AREAS.find((a) => a.id === areaId);
  if (!area) throw new Error(`no area ${areaId}`);
  const all = floors();
  const here = area.places.filter((p) => all.has(p)).map((p) => all.get(p)!);
  const inArea = new Set(here.map((f) => f.place));
  const linked = (a: string) => day.links.filter((l) => (l.from === a && inArea.has(l.to)) || (l.to === a && inArea.has(l.from))).map((l) => (l.from === a ? l.to : l.from));
  // The room with most ways to the others first, at its spot; each other room
  // out from the one that leads to it, on the bearing the research map has
  // between them, as near as it fits: GAP from every room, a trail's length
  // from the room it walks to.
  const wide = new Map<string, Outline>();
  const widen = (f: RoomFloor, by: number) => {
    const key = `${f.place}/${by}`;
    if (!wide.has(key)) wide.set(key, widened(outlineOf(f), by));
    return wide.get(key)!;
  };
  const root = [...here].sort((a, b) => linked(b.place).length - linked(a.place).length)[0]!;
  const placed = new Map<string, Placed>([[root.place, placeAt(root, spot(root.place))]]);
  const queue = [root.place];
  const centre = (p: Placed) => ({ x: p.at.x + (p.floor.bounds.x0 + p.floor.bounds.x1) / 2 / UNITS, y: p.at.y + (p.floor.bounds.z0 + p.floor.bounds.z1) / 2 / UNITS });
  const fits = (from: Placed, room: Placed, walk: boolean) =>
    [...placed.values()].every((q) => {
      const gap = q === from && walk ? TRAIL : GAP;
      const wq = widen(q.floor, gap / 2);
      const wr = widen(room.floor, gap / 2);
      return !touch(wq, q.at, wr, room.at);
    });
  const place = (from: Placed, floor: RoomFloor) => {
    const walk = linkOf(from.floor.place, floor.place)?.kind === 'walk';
    const a = spot(from.floor.place);
    const b = spot(floor.place);
    const bearing = Math.atan2(b.y - a.y, b.x - a.x);
    const c = centre(from);
    let best: Placed | undefined;
    let bestCost = Infinity;
    for (let d = 0; d <= 120 && d < bestCost; d += 0.5)
      for (const t of TURNS) {
        if (d + t.cost >= bestCost) continue;
        const room = placeAt(floor, { x: c.x + Math.cos(bearing + t.by) * d, y: c.y + Math.sin(bearing + t.by) * d });
        if (fits(from, room, walk)) {
          best = room;
          bestCost = d + t.cost;
        }
      }
    placed.set(floor.place, best ?? placeAt(floor, { x: c.x + (b.x - a.x), y: c.y + (b.y - a.y) }));
  };
  for (;;) {
    while (queue.length) {
      const from = placed.get(queue.shift()!)!;
      for (const to of linked(from.floor.place)) {
        if (placed.has(to)) continue;
        place(from, all.get(to)!);
        queue.push(to);
      }
    }
    // A room with no way to the others in its area: beside the one nearest it on the research map.
    const left = here.find((f) => !placed.has(f.place));
    if (!left) break;
    const s = spot(left.place);
    const near = [...placed.values()].sort((x, y) => Math.hypot(spot(x.floor.place).x - s.x, spot(x.floor.place).y - s.y) - Math.hypot(spot(y.floor.place).x - s.x, spot(y.floor.place).y - s.y))[0]!;
    place(near, left);
    queue.push(left.place);
  }
  const rooms = here.map((f) => placed.get(f.place)!);
  return { area: areaId, rooms, trails: ways(rooms, inArea), overlaps: overlapsOf(rooms) };
}

/** A plan's extent in metres: every outline and way. */
export function extent(plan: Pick<AreaPlan, 'rooms' | 'trails'>): { x0: number; y0: number; x1: number; y1: number } {
  const e = { x0: Infinity, y0: Infinity, x1: -Infinity, y1: -Infinity };
  const add = (x: number, y: number) => {
    e.x0 = Math.min(e.x0, x);
    e.y0 = Math.min(e.y0, y);
    e.x1 = Math.max(e.x1, x);
    e.y1 = Math.max(e.y1, y);
  };
  for (const r of plan.rooms) {
    const o = r.outline;
    for (let j = 0; j < o.rows; j++)
      for (let i = 0; i < o.cols; i++) if (o.cells[j * o.cols + i]) add(r.at.x + o.x0 + i * CELL, r.at.y + o.y0 + j * CELL), add(r.at.x + o.x0 + (i + 1) * CELL, r.at.y + o.y0 + (j + 1) * CELL);
  }
  for (const t of plan.trails) for (const p of t.points) add(p.x, p.y);
  return e;
}
