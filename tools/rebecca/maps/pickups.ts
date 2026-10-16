// Her six maps as things to pick up, where the plan finds them (plan/day.ts's
// map steps): RE1's own map items 0x4E-0x53, which the engine takes as maps
// (pickup_key_event raises the map's bit, ROOM_FLAG_MAP_BASE + index), lying
// on the floor in RE1's own folded-map model, each kept once taken by an
// FG_ITEM flag of its own. scripts.ts writes them into the kit rooms; the
// cabin's is in its hand-written room.c.
import { spots } from '../day/supplies.ts';
import { freeFloor } from '../day/foes.ts';
import type { Floor } from '../day/foes.ts';
import type { PickupModel } from '../items/items.ts';
import { day } from '../plan/day.ts';
import { AREAS, FIRST_MAP_ITEM, MAP_ITEMS } from '../plan/maps.ts';

/** RE1's map of the mansion's first floor, item model 0 of ROOM107: the model every map of hers uses. */
export const MAP_MODEL: PickupModel = { from: 'Stage1/ROOM1070.RDT', index: 0 };

/**
 * FG_ITEM flags for the maps, one each in MAP_ITEMS order: 248-253, past
 * every other pickup of her day (day/supplies.ts lists who has the rest).
 */
export const MAP_FLAGS = Array.from({ length: MAP_ITEMS.length }, (_, i) => 248 + i);

/** What she says on taking each map, by its id in MAP_ITEMS. */
const FOUND: Record<string, string> = {
  'map-trail': "The ranger's trail map. The station, the gorge and the summit.",
  'map-camp': 'A site plan of Camp 4, off the notice board.',
  'map-forestry': 'A Forest Service road map. The road, the tower, the line, the quarry.',
  'map-mine': 'A survey of the mine. The levels, the pump and the lift.',
  'map-valley': "The Skyway's route map. The line, the valley, the creek.",
  'map-estate': 'A plan of the estate grounds. The wall, the kennels, the garden, the cellar.',
};

/** The map that lies in a room, by the room's slug. */
export function mapIn(slug: string): { id: number; flag: number; name: string; found: string } | undefined {
  const i = MAP_ITEMS.findIndex((m) => {
    const step = day.steps.find((s) => s.id === m.step);
    return step && (day.places.find((p) => p.id === step.at)?.room ?? step.at) === slug;
  });
  if (i < 0) return undefined;
  const m = MAP_ITEMS[i]!;
  const found = FOUND[m.id];
  if (!found) throw new Error(`${m.id}: no line for taking it`);
  return { id: FIRST_MAP_ITEM + i, flag: MAP_FLAGS[i]!, name: m.name, found };
}

/** The item models a kit room needs for its map: none, or RE1's map. */
export const mapModels = (slug: string): PickupModel[] => (mapIn(slug) ? [MAP_MODEL] : []);

const ZONE = 1800;
const SMALL = 1200;
const word = (n: number) => `${n & 0xff}, ${(n >> 8) & 0xff}`;

/**
 * A kit room's map pickup, if it has one: on free floor by a wall, clear of
 * the room's other zones (`avoid`), its model in item model slot `slot`.
 * The aot id is `id`.
 */
export function mapLines(slug: string, floor: Floor, avoid: readonly Floor['bounds'][], id: number, slot: number): string[] {
  const m = mapIn(slug);
  if (!m) return [];
  // In a small room full of things, a smaller zone on the free floor least
  // covered by the others: they come first in the table, so it works on the
  // rest of its floor.
  const own = (q: { x: number; z: number }, size: number) => {
    let free = 0;
    let all = 0;
    for (let x = q.x - size / 2 + 50; x < q.x + size / 2; x += 100)
      for (let z = q.z - size / 2 + 50; z < q.z + size / 2; z += 100) {
        all++;
        if (!avoid.some((r) => x >= r.x0 && x < r.x1 && z >= r.z0 && z < r.z1)) free++;
      }
    return free / all;
  };
  const clear = spots(floor, 1, avoid)[0];
  const tight = freeFloor(floor).sort((a, b) => own(b, SMALL) - own(a, SMALL))[0];
  const [p, size] = clear ? [clear, ZONE] : tight && own(tight, SMALL) >= 0.25 ? [tight, SMALL] : [undefined, 0];
  if (!p) throw new Error(`${slug}: no free floor for the ${m.name}`);
  return [
    `if (ck(FG_ITEM, ${m.flag}, 0)) {  // the ${m.name.toLowerCase()} (maps/pickups.ts)`,
    `    item_aot_set(${id}, ${p.x - size / 2}, ${p.z - size / 2}, ${size}, ${size}, ${m.id}, 1, ${slot}, 255, ${word(p.x)}, 0, 0, ${word(p.z)}, 0, 0, ${m.flag}, 129, 0, 0);`,
    '}',
  ];
}


/** Her maps as items: the id, the name in capitals as RE1's are, and what she reads examining it. */
export function mapItems(): { id: number; step: string; name: string; description: string }[] {
  return MAP_ITEMS.map((m, i) => ({
    id: FIRST_MAP_ITEM + i,
    step: m.step,
    name: m.name.toUpperCase(),
    description: wrap(`A map of ${m.areas.map((a) => AREAS.find((x) => x.id === a)!.name).join(' and ')}.`),
  }));
}

/** Lines of 26 characters at most, as the item descriptions are. */
function wrap(text: string): string {
  const lines: string[] = [];
  for (const word of text.split(' ')) {
    const last = lines.at(-1);
    if (last !== undefined && (last + ' ' + word).length <= 26) lines[lines.length - 1] = `${last} ${word}`;
    else lines.push(word);
  }
  return lines.join('\n');
}
