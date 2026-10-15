// Lay out each area of her map as a floor plan: every room at its real size,
// turned and placed so that its doors meet its neighbours' (a building's door
// against the yard door that leads into it, the two flush), and the walks
// between outdoor rooms drawn as trails a few metres long. One room of the
// area, the one with most ways to the others, is placed first, as it is in
// its scene; the rest follow it out along the doors.
import { AREAS } from '../plan/maps.ts';
import { day } from '../plan/day.ts';
import { floors, SIDES, UNITS, type Door, type Rect, type RoomFloor, type Side } from './floors.ts';

/** A point in the plan, in metres: x across, y down the page. */
export type Pt = { readonly x: number; readonly y: number };

export interface Placed {
  readonly floor: RoomFloor;
  /** Quarter turns clockwise from the room's own axes. */
  readonly turn: Side;
  /** Where the room's origin lands. */
  readonly at: Pt;
}

export interface Trail {
  readonly from: string;
  readonly to: string;
  readonly a: Pt;
  readonly b: Pt;
}

export interface AreaPlan {
  readonly area: string;
  /** In the area's order (maps.ts), which is the order of its rooms' palette blocks. */
  readonly rooms: readonly Placed[];
  readonly trails: readonly Trail[];
  /** Rooms that overlap another's floor: the layout's faults, empty when it is clean. */
  readonly overlaps: readonly string[];
}

/** A room point (game units) in the plan (metres). */
export function toPlan(p: Placed, x: number, z: number): Pt {
  let u = x / UNITS;
  let v = z / UNITS;
  for (let i = 0; i < p.turn; i++) [u, v] = [-v, u];
  return { x: u + p.at.x, y: v + p.at.y };
}

/** A plan point back in the room's own game units. */
export function fromPlan(p: Placed, pt: Pt): { x: number; z: number } {
  let u = pt.x - p.at.x;
  let v = pt.y - p.at.y;
  for (let i = 0; i < p.turn; i++) [u, v] = [v, -u];
  return { x: u * UNITS, z: v * UNITS };
}

/** A room rectangle's corners in the plan, as a box. */
export function planBox(p: Placed, r: Rect): { x0: number; y0: number; x1: number; y1: number } {
  const a = toPlan(p, r.x0, r.z0);
  const b = toPlan(p, r.x1, r.z1);
  return { x0: Math.min(a.x, b.x), y0: Math.min(a.y, b.y), x1: Math.max(a.x, b.x), y1: Math.max(a.y, b.y) };
}

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

/** Where a door is in the plan, and the way it faces there. */
export function doorInPlan(p: Placed, d: Door): { at: Pt; side: Side } {
  const f = doorFace(d);
  return { at: toPlan(p, f.x, f.z), side: ((d.side + p.turn) % 4) as Side };
}

const linkKind = (a: string, b: string) => day.links.find((l) => (l.from === a && l.to === b) || (l.from === b && l.to === a))?.kind;

/** How far apart two rooms a walk joins are drawn, in metres. */
const TRAIL = 3;

function overlap(a: Placed, b: Placed): number {
  const x = planBox(a, a.floor.bounds);
  const y = planBox(b, b.floor.bounds);
  const w = Math.min(x.x1, y.x1) - Math.max(x.x0, y.x0);
  const h = Math.min(x.y1, y.y1) - Math.max(x.y0, y.y0);
  return w > 0.3 && h > 0.3 ? w * h : 0;
}

/**
 * Overlap that counts as a fault: a building inside a yard stands on the
 * yard's footprint of it, which is a hole in the yard's floor.
 */
function fault(a: Placed, b: Placed): boolean {
  if (overlap(a, b) === 0) return false;
  const inHole = (inner: Placed, outer: Placed) => {
    const box = planBox(inner, inner.floor.bounds);
    const area = (box.x1 - box.x0) * (box.y1 - box.y0);
    return outer.floor.solids.some((s) => {
      const h = planBox(outer, s);
      const w = Math.min(box.x1, h.x1) - Math.max(box.x0, h.x0);
      const d = Math.min(box.y1, h.y1) - Math.max(box.y0, h.y0);
      return w > 0 && d > 0 && w * d >= area * 0.6;
    });
  };
  return !inHole(a, b) && !inHole(b, a);
}

export function planArea(areaId: string): AreaPlan {
  const area = AREAS.find((a) => a.id === areaId);
  if (!area) throw new Error(`no area ${areaId}`);
  const all = floors();
  const here = area.places.filter((p) => all.has(p));
  const inArea = new Set(here);
  const ways = (p: string) => all.get(p)!.doors.filter((d) => inArea.has(d.to)).length;
  const root = [...here].sort((a, b) => ways(b) - ways(a))[0]!;
  const placed = new Map<string, Placed>([[root, { floor: all.get(root)!, turn: 0, at: { x: 0, y: 0 } }]]);
  const trails: Trail[] = [];
  /** Rooms flush against their way in, which may stand in it: a building in a yard. */
  const within = new Set<string>();
  const queue = [root];
  while (queue.length) {
    const from = placed.get(queue.shift()!)!;
    for (const d of from.floor.doors) {
      if (!inArea.has(d.to) || placed.has(d.to)) continue;
      const floor = all.get(d.to)!;
      const back = floor.doors.find((b) => b.to === from.floor.place);
      if (!back) continue;
      const out = doorInPlan(from, d);
      const walk = linkKind(from.floor.place, d.to) === 'walk';
      // Flush against the door, or a walk away from it. A room that would
      // stand on another goes further out, or off to another side of the
      // door (a tower's top floor beside its stairs), joined by a trail.
      let best: { room: Placed; gap: number } | undefined;
      search: for (let gap = walk ? TRAIL : 0; gap <= 40; gap += 2) {
        for (const side of [out.side, (out.side + 1) % 4, (out.side + 3) % 4] as Side[]) {
          if (gap === 0 && side !== out.side) continue;
          const turn = ((side + 2 - back.side + 8) % 4) as Side;
          const face = doorInPlan({ floor, turn, at: { x: 0, y: 0 } }, back).at;
          const [dx, dy] = SIDES[side]!;
          const room: Placed = { floor, turn, at: { x: out.at.x + dx * gap - face.x, y: out.at.y + dy * gap - face.y } };
          best ??= { room, gap };
          if (![...placed.values()].some((o) => (o !== from || gap > 0) && fault(o, room))) {
            best = { room, gap };
            break search;
          }
        }
      }
      placed.set(d.to, best!.room);
      if (best!.gap > 0) trails.push({ from: from.floor.place, to: d.to, a: out.at, b: doorInPlan(best!.room, back).at });
      else within.add(`${from.floor.place}|${d.to}`);
      queue.push(d.to);
    }
  }
  const rooms = here.filter((p) => placed.has(p)).map((p) => placed.get(p)!);
  const overlaps: string[] = [];
  for (let i = 0; i < rooms.length; i++)
    for (let j = i + 1; j < rooms.length; j++) if (!within.has(`${rooms[i]!.floor.place}|${rooms[j]!.floor.place}`) && !within.has(`${rooms[j]!.floor.place}|${rooms[i]!.floor.place}`) && fault(rooms[i]!, rooms[j]!)) overlaps.push(`${rooms[i]!.floor.place} and ${rooms[j]!.floor.place}`);
  const unplaced = here.filter((p) => !placed.has(p));
  if (unplaced.length) overlaps.push(`not joined to the rest: ${unplaced.join(', ')}`);
  // The map is wider than tall: turn a plan that is taller than it is wide.
  const plan = { area: areaId, rooms, trails, overlaps };
  const e = extent(plan);
  return (e.y1 - e.y0) / (e.x1 - e.x0) > ASPECT ? quarterTurn(plan) : plan;
}

/** The shown part of a map, height over width (128 x 100). */
const ASPECT = 100 / 128;

/** A plan's extent in metres. */
export function extent(plan: Pick<AreaPlan, 'rooms' | 'trails'>): { x0: number; y0: number; x1: number; y1: number } {
  const pts: Pt[] = [];
  for (const r of plan.rooms) {
    const b = r.floor.bounds;
    pts.push(toPlan(r, b.x0, b.z0), toPlan(r, b.x1, b.z1));
  }
  for (const t of plan.trails) pts.push(t.a, t.b);
  return {
    x0: Math.min(...pts.map((p) => p.x)),
    y0: Math.min(...pts.map((p) => p.y)),
    x1: Math.max(...pts.map((p) => p.x)),
    y1: Math.max(...pts.map((p) => p.y)),
  };
}

/** The whole plan a quarter turn clockwise. */
function quarterTurn(plan: AreaPlan): AreaPlan {
  const turn = (p: Pt): Pt => ({ x: -p.y, y: p.x });
  return {
    ...plan,
    rooms: plan.rooms.map((r) => ({ floor: r.floor, turn: ((r.turn + 1) % 4) as Side, at: turn(r.at) })),
    trails: plan.trails.map((t) => ({ ...t, a: turn(t.a), b: turn(t.b) })),
  };
}
