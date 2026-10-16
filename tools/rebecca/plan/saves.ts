// Where she can save: the rooms with a typewriter and an item box, as data.
//
// Placed the way RE1 places them, measured from the PC game's own room
// scripts (re1-saves.ts): 7 typewriter rooms in 107 rooms, one for every 15
// or so. A room there is 2.7 doors from a typewriter on average and 6 at the
// most, and 4 of the 7 are dead ends off a corridor or a hub: a side room she
// passes again and again, never a room on the way through. Her day is half
// the size, so it has five, plus the mansion's at the end, and none is
// farther than RE1's farthest.
//
// Each is a quiet room with no enemies that plays RE1's own save room music
// from the player's files (music.ts, cue "save"). The item box is RE1's own,
// its lid from the player's files, and all of them share one store, as in
// RE1: what she leaves in the cabin's is in the booth's too.
import { CUES } from './music.ts';
import type { Plan } from './plan.ts';

export interface SaveRoom {
  readonly place: string;
  /** What the typewriter and the box are in this room. */
  readonly props: string;
  /** Packs of three ink ribbons found here. */
  readonly ribbons: number;
  readonly why: string;
}

/** RE1's own spacing (re1-saves.ts over the PC room files): the farthest room from a typewriter, and the average. */
export const RE1 = { rooms: 107, saves: 7, maxDoors: 6, meanDoors: 2.74 } as const;

export const SAVES: readonly SaveRoom[] = [
  {
    place: 'cabin', ribbons: 1,
    props: "The ranger's typewriter on a table in the corner by the broken window, the ink ribbons beside it. The item box, shrunk to a footlocker, at the bunk's foot.",
    why: 'The first save, minutes in, off the hub she keeps coming back to. The shed, the woods, the road and the gorge are a door or two away.',
  },
  {
    place: 'office', ribbons: 1,
    props: "The foreman's typewriter on a stand by the door, the payroll half typed. The item box along the east wall, under the empty gun rack.",
    why: 'Off the camp yard, behind the key on the dead cook: the reward for getting into the camp. The mill, the pond and the flume are within four doors.',
  },
  {
    place: 'booth', ribbons: 0,
    props: "Hal's typewriter on a stand against the north wall, the day's log in it. The item box along the east wall, under the fuse box and the phone.",
    why: "Off the gondola station, where the east path, the line track's shortcut and the ride down all meet. The last save before the gondola, which only goes down.",
  },
  {
    place: 'mine-office', ribbons: 1,
    props: "The shift boss's typewriter on his desk, for the accident book. The item box along the east wall, past the powder boxes.",
    why: 'The one quiet room in the mine, off the tunnel. The pump, the gallery and the lift are two or three doors on.',
  },
  {
    place: 'lodge', ribbons: 1,
    props: "The gardener's typewriter for seed orders, on a table by the window. The item box against the south wall, between the fireplace and the bed.",
    why: "Across the creek, behind the door she prises open: the valley's only save, three doors before the kennels' pack.",
  },
];

/** At least this many of her rooms for each save room, so saves stay rare, as the owner asked. RE1 has 15. */
export const MIN_ROOMS_PER_SAVE = 10;

/**
 * Doors from each place to the nearest save room she can walk to. Every way
 * between rooms counts, locked or not, as in the RE1 count, in both
 * directions but for the rides: the flume and the gondola only go down.
 * The room the day ends in is left out: she sleeps there, and never leaves.
 */
export function doorsToSave(plan: Plan): Map<string, number> {
  const next = new Map<string, string[]>(plan.places.map((p) => [p.id, []]));
  for (const l of plan.links) {
    next.get(l.from)?.push(l.to);
    if (l.kind !== 'ride') next.get(l.to)?.push(l.from);
  }
  const saves = new Set(SAVES.map((s) => s.place));
  const end = plan.steps.find((s) => s.kind === 'goal')?.at;
  const dist = new Map<string, number>();
  for (const p of plan.places.filter((p) => p.id !== end)) {
    const seen = new Set([p.id]);
    let edge = [p.id];
    for (let d = 0; edge.length; d++) {
      if (edge.some((e) => saves.has(e))) {
        dist.set(p.id, d);
        break;
      }
      edge = edge.flatMap((e) => next.get(e) ?? []).filter((e) => !seen.has(e) && Boolean(seen.add(e)));
    }
  }
  return dist;
}

/** Everything wrong with the save rooms against the plan; empty when they fit. */
export function checkSaves(plan: Plan): string[] {
  const errors: string[] = [];
  const seen = new Set<string>();
  for (const s of SAVES) {
    const p = plan.places.find((x) => x.id === s.place);
    if (!p) errors.push(`save room ${s.place} is not in the plan`);
    else if (p.enemies) errors.push(`save room ${s.place} has enemies: ${p.enemies}`);
    if (!CUES.find((c) => c.id === 'save')?.places.includes(s.place)) errors.push(`save room ${s.place} doesn't play the save room music`);
    if (seen.has(s.place)) errors.push(`${s.place} is a save room twice`);
    seen.add(s.place);
  }
  if (plan.places.length / SAVES.length < MIN_ROOMS_PER_SAVE) {
    errors.push(`${SAVES.length} save rooms in ${plan.places.length} rooms is more than one for every ${MIN_ROOMS_PER_SAVE}`);
  }
  const dist = doorsToSave(plan);
  for (const [id, d] of dist) {
    if (d > RE1.maxDoors) errors.push(`${id} is ${d} doors from a save room; RE1's farthest room is ${RE1.maxDoors}`);
  }
  for (const p of plan.places) {
    if (!dist.has(p.id) && p.id !== plan.steps.find((s) => s.kind === 'goal')?.at) errors.push(`${p.id} can't reach a save room`);
  }
  const mean = [...dist.values()].reduce((a, b) => a + b, 0) / dist.size;
  if (mean > RE1.meanDoors) errors.push(`a room is ${mean.toFixed(2)} doors from a save room on average; RE1's are ${RE1.meanDoors}`);
  return errors;
}
