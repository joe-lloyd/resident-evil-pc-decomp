// Where she can save: the rooms with a typewriter and an item box, as data.
// RE1 has seven typewriter rooms and six item boxes in its 110 or so rooms
// (counted from the PS1 disc's room scripts: SCE_TYPEWRITER and SCE_ITEMBOX).
// Her day is shorter and its spokes are one-way trips out from the yard, so
// it has one per area and ink ribbons ration the saves.
//
// Each save room is a quiet room with no enemies, on the way into an area,
// and plays her save-room theme (music.ts, cue "safe"). The item boxes are
// one shared box, as in RE1, so what she leaves in the cabin's footlocker is
// in the cottage's crate too. That matters in the mine: she loses everything
// she carries there, but not what is in the box.
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

/** No room is more doors than this from a save room, counting every way between rooms, locked or not. */
export const MAX_DOORS = 5;

export const SAVES: readonly SaveRoom[] = [
  {
    place: 'cabin', ribbons: 1,
    props: "The ranger's typewriter on the desk by the radio. His footlocker at the bunk's foot is the item box.",
    why: 'The first save, in the hub she keeps coming back to. The yard, the shed and the gorge are a door or two away.',
  },
  {
    place: 'office', ribbons: 1,
    props: "The foreman's typewriter, the payroll half typed. A tin trunk under the window is the box.",
    why: 'The camp is eleven rooms of loggers. The office key is on the cook in the mess, next door across the yard.',
  },
  {
    place: 'generator', ribbons: 0,
    props: "The line crew's typewriter on the log desk. Their tool locker is the box. The lights come on when the generator runs.",
    why: 'The middle of the west spoke: the washout, the switch house and the tower are all within four doors.',
  },
  {
    place: 'cottage', ribbons: 1,
    props: "Hal's typewriter on the kitchen table, his radio still on. The box is a blanket chest.",
    why: 'Before the quarry and the mine. Whatever she leaves in the box is waiting for her after the mine takes her gear.',
  },
  {
    place: 'weather', ribbons: 0,
    props: "The observer's typewriter by the barograph. An equipment case is the box.",
    why: 'Where the lift brings her up after the chase, unarmed, with only what the box holds.',
  },
  {
    place: 'lower-station', ribbons: 1,
    props: "The keeper's typewriter beside the cold kettle. A parcel crate is the box.",
    why: 'The first room indoors after the ride down. The valley path, the helicopter and the creek are close.',
  },
  {
    place: 'garden-shed', ribbons: 0,
    props: "The gardener's old typewriter for seed orders on the potting bench. A seed chest is the box.",
    why: 'The last save before the mansion: the kennels and the cellar are two doors away.',
  },
];

/** Doors from each place to its nearest save room, over every link in either direction. */
export function doorsToSave(plan: Plan): Map<string, number> {
  const next = new Map<string, string[]>(plan.places.map((p) => [p.id, []]));
  for (const l of plan.links) {
    next.get(l.from)?.push(l.to);
    next.get(l.to)?.push(l.from);
  }
  const dist = new Map<string, number>();
  let edge = SAVES.map((s) => s.place).filter((p) => next.has(p));
  for (const p of edge) dist.set(p, 0);
  for (let d = 1; edge.length; d++) {
    edge = edge.flatMap((p) => next.get(p)!).filter((p) => !dist.has(p));
    for (const p of edge) dist.set(p, d);
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
    if (!CUES.find((c) => c.id === 'safe')?.places.includes(s.place)) errors.push(`save room ${s.place} doesn't play her save-room theme`);
    if (seen.has(s.place)) errors.push(`${s.place} is a save room twice`);
    seen.add(s.place);
  }
  const dist = doorsToSave(plan);
  for (const p of plan.places) {
    const d = dist.get(p.id);
    if (d === undefined) errors.push(`${p.id} can't reach a save room`);
    else if (d > MAX_DOORS) errors.push(`${p.id} is ${d} doors from a save room; the most is ${MAX_DOORS}`);
  }
  return errors;
}
