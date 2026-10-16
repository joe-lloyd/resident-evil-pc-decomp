// The enemies of her day's kit rooms, as the plan names them
// (plan/day.ts, each place's `enemies`), placed by the room's own floor:
// spread out, clear of walls, gaps and doors, and as far as the room allows
// from where she comes in, facing that way. scripts.ts writes them into the
// rooms' init scripts. The hand-written rooms (the yard, the bridge, the
// trail) place their own. The gondola car's crows are at its windows,
// outside it: the ride's cutscene, not the room.
//
// Each enemy has a kill flag of its own (enemy operand 3, g_EnemiesFlags), so
// once dead it stays dead: 186-254, which no shipped room uses, less 200 (the
// yard's Cerberus) and 253-254 (the trail's crows). The operands are the commonest ones RE1's own rooms give
// each kind (`rae script` over every RDT).

export type Rect = { x0: number; z0: number; x1: number; z1: number };
export interface Floor {
  readonly bounds: Rect;
  readonly walls: readonly (Rect & { shape: 'box' | 'circle' })[];
  readonly voids?: readonly Rect[];
  /** Door zones, and where she arrives through each. */
  readonly doors: readonly { zone: Rect; arrive: { x: number; z: number } }[];
}

/** Entity id (cmd_enemy_set operand 1), behaviour byte, and collision records, as RE1 places each kind. */
const KINDS = {
  zombie: { id: 17, behavior: 0, sca: 2 },
  cerberus: { id: 2, behavior: 1, sca: 2 },
  crow: { id: 5, behavior: 0, sca: 2 },
  adder: { id: 10, behavior: 1, sca: 1 },
  spinner: { id: 3, behavior: 2, sca: 2 },
} as const;
export type Kind = keyof typeof KINDS;

/** What each kit room holds, from the plan. */
export const FOES: Record<string, readonly (readonly [Kind, number])[]> = {
  platform: [['crow', 2]],
  woods: [['cerberus', 2]],
  den: [['cerberus', 1]],
  'logging-road': [['zombie', 1]],
  'camp-yard': [['zombie', 3]],
  bunkhouse: [['zombie', 1]],
  mess: [['zombie', 2]],
  depot: [['adder', 2]],
  sawmill: [['zombie', 2]],
  pond: [['zombie', 1]],
  road: [['crow', 3]],
  washout: [['adder', 2]],
  'tower-stairs': [['crow', 2]],
  'tower-top': [['crow', 2]],
  'line-track': [['adder', 2]],
  'east-path': [['crow', 2]],
  quarry: [['cerberus', 1]],
  tunnel: [['spinner', 1]],
  junction: [['spinner', 2]],
  gallery: [['zombie', 1]],
  'summit-trail': [['crow', 3]],
  pylon: [['crow', 2]],
  'valley-path': [['cerberus', 1]],
  creek: [['adder', 2]],
  'estate-wall': [['crow', 2]],
  kennels: [['cerberus', 3]],
  'back-garden': [['zombie', 1]],
  cellar: [['zombie', 1]],
};

/** Kill flags for the kit rooms' enemies, in order: 186-252 less 200; the trail's crows have 253 and 254. */
export const KILL_FLAGS = Array.from({ length: 252 - 186 + 1 }, (_, i) => 186 + i).filter((f) => f !== 200);

const STEP = 340; // a fifth of a metre
const EDGE = 700; // from the floor's edge
const WALL = 600; // from a wall or a gap
const DOOR = 1200; // from a door's zone
const SPREAD = 2000; // between two enemies

const outside = (x: number, z: number, r: Rect, pad: number) => x < r.x0 - pad || x > r.x1 + pad || z < r.z0 - pad || z > r.z1 + pad;
const toRect = (x: number, z: number, r: Rect) => Math.hypot(Math.max(r.x0 - x, 0, x - r.x1), Math.max(r.z0 - z, 0, z - r.z1));

/** Points of floor a fifth of a metre apart that something can stand on: inside the edge, clear of walls, gaps and doors. */
export function freeFloor(floor: Floor): { x: number; z: number }[] {
  const b = floor.bounds;
  const free: { x: number; z: number }[] = [];
  for (let x = b.x0 + EDGE; x <= b.x1 - EDGE; x += STEP)
    for (let z = b.z0 + EDGE; z <= b.z1 - EDGE; z += STEP) {
      if (!floor.walls.every((w) => outside(x, z, w, WALL))) continue;
      if (!(floor.voids ?? []).every((v) => outside(x, z, v, WALL))) continue;
      if (floor.doors.some((d) => toRect(x, z, d.zone) < DOOR)) continue;
      free.push({ x, z });
    }
  return free;
}

/** Where `count` enemies stand: free floor, the first farthest from her arrivals, each next farthest from those and the others. */
export function place(floor: Floor, count: number): { x: number; z: number }[] {
  const free = freeFloor(floor);
  const arrivals = floor.doors.map((d) => d.arrive);
  const chosen: { x: number; z: number }[] = [];
  for (let k = 0; k < count; k++) {
    let best: { x: number; z: number } | undefined;
    let bestScore = -1;
    for (const p of free) {
      if (chosen.some((c) => Math.hypot(c.x - p.x, c.z - p.z) < SPREAD)) continue;
      const score = Math.min(...arrivals.map((a) => Math.hypot(a.x - p.x, a.z - p.z)), ...chosen.map((c) => Math.hypot(c.x - p.x, c.z - p.z)));
      if (score > bestScore) [best, bestScore] = [p, score];
    }
    if (!best) break;
    chosen.push(best);
  }
  return chosen;
}

/** The angle that faces from one point toward another: 0 faces +X, 0x400 -Z, 0xC00 +Z. */
export const facing = (from: { x: number; z: number }, to: { x: number; z: number }) =>
  ((Math.round((Math.atan2(-(to.z - from.z), to.x - from.x) / (2 * Math.PI)) * 4096) % 4096) + 4096) % 4096;

/** The room's enemy() lines; `flags` supplies kill flags and is consumed. Slots count up from `slot`. */
export function foeLines(slug: string, floor: Floor, flags: number[], slot = 0): string[] {
  const lines: string[] = [];
  for (const [kind, count] of FOES[slug] ?? []) {
    const k = KINDS[kind];
    const spots = place(floor, count);
    if (spots.length < count) throw new Error(`${slug}: room for ${spots.length} of ${count} ${kind}s`);
    for (const p of spots) {
      const flag = flags.shift();
      if (flag === undefined) throw new Error(`${slug}: no kill flag left`);
      const near = floor.doors.map((d) => d.arrive).sort((a, c) => Math.hypot(a.x - p.x, a.z - p.z) - Math.hypot(c.x - p.x, c.z - p.z))[0];
      const angle = near ? facing(p, near) : 0;
      lines.push(`enemy(${k.id}, ${k.behavior}, ${flag}, 1, ${k.sca}, 0, 0, ${angle}, 0, 0, ${p.x}, 0, ${p.z}, ${slot++}, 0, 0, 0);  // a ${kind}`);
    }
  }
  return lines;
}
