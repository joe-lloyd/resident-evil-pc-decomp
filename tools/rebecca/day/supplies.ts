// Ammunition, herbs and first aid sprays through her day's kit rooms: RE1's
// own items with RE1's own pickup models, copied from the rooms of the
// player's game that hold them. A first spread, before the day is balanced:
// a few clips for the Beretta, herbs where she would be hurt, a spray now
// and then. scripts.ts writes the pickups into the rooms' init scripts and
// rooms.ts gives each room the models it needs.
import { freeFloor, type Floor } from './foes.ts';
import { day } from '../plan/day.ts';
import { SAVES } from '../plan/saves.ts';

/** Item id, how many, its model (a room of the player's game and the slot in its item model table), and the byte RE1 gives each after 129. */
export const SUPPLY_KINDS = {
  clip: { id: 11, qty: 15, model: { from: 'Stage1/ROOM1020.RDT', index: 2 }, act: 0 },
  greenHerb: { id: 68, qty: 1, model: { from: 'Stage1/ROOM1090.RDT', index: 0 }, act: 1 },
  redHerb: { id: 67, qty: 1, model: { from: 'Stage1/ROOM10C0.RDT', index: 1 }, act: 1 },
  spray: { id: 65, qty: 1, model: { from: 'Stage3/ROOM3090.RDT', index: 0 }, act: 0 },
  // A pack of three, as RE1 lays them by its typewriters.
  ribbons: { id: 47, qty: 3, model: { from: 'Stage3/ROOM30E0.RDT', index: 2 }, act: 0 },
} as const;
export type Supply = keyof typeof SUPPLY_KINDS;

const SPREAD: Record<string, readonly Supply[]> = {
  booth: ['greenHerb'],
  bunkhouse: ['clip', 'redHerb'],
  mess: ['greenHerb'],
  office: ['spray'],
  workshop: ['clip'],
  depot: ['greenHerb'],
  sawmill: ['clip'],
  'tower-top': ['clip'],
  'quarry-office': ['greenHerb'],
  mast: ['greenHerb', 'clip', 'spray'],
  'lower-station': ['clip'],
  crash: ['clip', 'greenHerb'],
  creek: ['greenHerb'],
  lodge: ['spray', 'redHerb'],
  kennels: ['greenHerb'],
  cellar: ['clip'],
  wine: ['spray'],
};

/**
 * The spread, and the ink ribbons each save room has (plan/saves.ts). The
 * cabin's are in its hand-written script, by its typewriter.
 */
export const SUPPLIES: Record<string, readonly Supply[]> = { ...SPREAD };
for (const s of SAVES) {
  const slug = day.places.find((p) => p.id === s.place)?.room ?? s.place;
  if (slug === 'lookout' || !s.ribbons) continue;
  SUPPLIES[slug] = [...(SUPPLIES[slug] ?? []), ...Array<Supply>(s.ribbons).fill('ribbons')];
}

/**
 * Room-item flags (FG_ITEM) for the supplies, in order: 180-229. Her other
 * rooms use 230-247 (240 the cabin's ink ribbons) and the save room 22; the rest of RE1's flags belong to
 * mansion rooms she never sees, and a new game sets them all.
 */
export const ITEM_FLAGS = Array.from({ length: 50 }, (_, i) => 180 + i);

/** The item models a room needs for its supplies, in the slot order the pickups use. */
export function supplyModels(slug: string): { from: string; index: number }[] {
  return [...new Set(SUPPLIES[slug] ?? [])].map((k) => SUPPLY_KINDS[k].model);
}

const ZONE = 1200;
const APART = 1700;

/**
 * Where each supply lies: free floor against a wall or the floor's edge,
 * as far from her arrivals as that allows, and apart from the others and
 * from any zone in `avoid`.
 */
export function spots(floor: Floor, count: number, avoid: readonly Floor['bounds'][] = []): { x: number; z: number }[] {
  const b = floor.bounds;
  const clear = (p: { x: number; z: number }) =>
    avoid.every((r) => Math.max(r.x0 - p.x, p.x - r.x1, r.z0 - p.z, p.z - r.z1) >= ZONE / 2 + 200);
  const free = freeFloor(floor).filter(clear);
  const edge = (p: { x: number; z: number }) =>
    Math.min(p.x - b.x0, b.x1 - p.x, p.z - b.z0, b.z1 - p.z, ...floor.walls.map((w) => Math.hypot(Math.max(w.x0 - p.x, 0, p.x - w.x1), Math.max(w.z0 - p.z, 0, p.z - w.z1))));
  const arrivals = floor.doors.map((d) => d.arrive);
  const chosen: { x: number; z: number }[] = [];
  for (let k = 0; k < count; k++) {
    const ok = free.filter((p) => chosen.every((c) => Math.hypot(c.x - p.x, c.z - p.z) >= APART));
    const near = Math.min(...ok.map(edge));
    const best = ok
      .filter((p) => edge(p) <= near + 340)
      .sort((p, q) => Math.min(...arrivals.map((a) => Math.hypot(a.x - q.x, a.z - q.z))) - Math.min(...arrivals.map((a) => Math.hypot(a.x - p.x, a.z - p.z))))[0];
    if (!best) break;
    chosen.push(best);
  }
  return chosen;
}

const word = (n: number) => `${n & 0xff}, ${(n >> 8) & 0xff}`;

/** The room's pickups, each kept once taken by its own flag; `flags` is consumed. aot ids count up from `id`. */
export function supplyLines(slug: string, floor: Floor, flags: number[], id: number): string[] {
  const kinds = SUPPLIES[slug] ?? [];
  const models = supplyModels(slug);
  const at = spots(floor, kinds.length);
  if (at.length < kinds.length) throw new Error(`${slug}: room for ${at.length} of ${kinds.length} supplies`);
  return kinds.flatMap((kind, i) => {
    const k = SUPPLY_KINDS[kind];
    const p = at[i]!;
    const flag = flags.shift();
    if (flag === undefined) throw new Error(`${slug}: no item flag left`);
    const slot = models.indexOf(k.model);
    const zone = `${p.x - ZONE / 2}, ${p.z - ZONE / 2}, ${ZONE}, ${ZONE}`;
    return [
      `if (ck(FG_ITEM, ${flag}, 0)) {  // ${kind}`,
      `    item_aot_set(${id++}, ${zone}, ${k.id}, ${k.qty}, ${slot}, 255, ${word(p.x)}, 0, 0, ${word(p.z)}, 0, 0, ${flag}, 129, ${k.act}, 0);`,
      '}',
    ];
  });
}
