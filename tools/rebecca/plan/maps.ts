// Rebecca's maps: how her day divides into the areas the map screen shows,
// and the map she picks up for each. RE1's screen has room for eleven area
// maps (item_m2/map01..0b.tim) and six map items (0x4E..0x53), and her day
// fits both: ten areas of her own and the mansion's save room.
//
// Without its map an area shows only the rooms she has been in. Picking up
// the map shows the rest, dim until she visits them (map_display_load_textures).
import type { Plan } from './plan.ts';

export interface Area {
  readonly id: string;
  /** The name on the map screen. */
  readonly name: string;
  /** The plan's places on this map. */
  readonly places: readonly string[];
}

export interface MapItem {
  readonly id: string;
  /** The item's name in her inventory. */
  readonly name: string;
  /** The plan step that picks it up. */
  readonly step: string;
  /** The areas it shows in full. */
  readonly areas: readonly string[];
}

/** RE1's map screen slots. */
export const AREA_SLOTS = 11;
export const MAP_ITEM_SLOTS = 6;
/** RE1's first map item; her maps are it and the ones after, in MAP_ITEMS order. */
export const FIRST_MAP_ITEM = 0x4e;
/** The overview's stages (RE1's map0d, map0c, map00, map0e), and the areas each lists. */
export const STAGE_SLOTS = 4;
export const AREAS_PER_STAGE = 4;

export interface Stage {
  /** Its name under the overview. */
  readonly name: string;
  /** Its areas, in the order up and down step through them. */
  readonly areas: readonly string[];
}

/**
 * The overview of the mountain unlocks in four stages, as RE1's does (the
 * mansion; the courtyard; the guardhouse; the lab): each shows its places on
 * the mountain once she has been in one of its areas, and the stages before.
 */
export const STAGES: readonly Stage[] = [
  { name: 'Ranger Station', areas: ['station', 'summit'] },
  { name: 'The Mountain', areas: ['camp', 'road', 'quarry', 'mine'] },
  { name: 'The Valley', areas: ['skyway', 'valley'] },
  { name: 'Spencer Estate', areas: ['grounds', 'cellar', 'mansion'] },
];

export const AREAS: readonly Area[] = [
  { id: 'station', name: 'Ranger Station', places: ['ridge', 'trail', 'yard', 'cabin', 'shed', 'woods', 'den', 'bridge', 'platform', 'booth'] },
  { id: 'camp', name: 'Logging Camp 4', places: ['logging-road', 'camp-gate', 'camp-yard', 'bunkhouse', 'office', 'mess', 'depot', 'workshop', 'sawmill', 'pond', 'flume'] },
  { id: 'road', name: 'Forestry Road', places: ['road', 'washout', 'generator', 'tower-foot', 'tower-stairs', 'tower-top', 'switch', 'line-track'] },
  { id: 'quarry', name: 'Quarry', places: ['east-path', 'cottage', 'quarry', 'quarry-office'] },
  { id: 'mine', name: 'Silver Mine', places: ['mine-entrance', 'tunnel', 'mine-office', 'junction', 'gallery', 'mine-lift'] },
  { id: 'summit', name: 'Summit', places: ['summit-trail', 'weather', 'mast'] },
  { id: 'skyway', name: 'Skyway Line', places: ['car', 'pylon'] },
  { id: 'valley', name: 'Valley', places: ['valley-path', 'lower-yard', 'lower-station', 'crash', 'creek', 'lodge'] },
  { id: 'grounds', name: 'Estate Grounds', places: ['estate-wall', 'kennels', 'back-garden', 'garden-shed'] },
  { id: 'cellar', name: 'Cellar', places: ['cellar', 'wine', 'crawl'] },
  { id: 'mansion', name: 'Mansion 1F', places: ['save'] },
];

export const MAP_ITEMS: readonly MapItem[] = [
  { id: 'map-trail', name: 'Trail Map', step: 'map-trail', areas: ['station', 'summit'] },
  { id: 'map-camp', name: 'Camp Plan', step: 'map-camp', areas: ['camp'] },
  { id: 'map-forestry', name: 'Road Map', step: 'map-forestry', areas: ['road', 'quarry'] },
  { id: 'map-mine', name: 'Mine Survey', step: 'map-mine', areas: ['mine'] },
  { id: 'map-valley', name: 'Skyway Map', step: 'map-valley', areas: ['skyway', 'valley'] },
  { id: 'map-estate', name: 'Grounds Plan', step: 'map-estate', areas: ['grounds', 'cellar'] },
];

/** Everything wrong with the maps against the plan; empty when they fit. */
export function checkMaps(plan: Plan): string[] {
  const errors: string[] = [];
  if (AREAS.length > AREA_SLOTS) errors.push(`${AREAS.length} areas, but the map screen has ${AREA_SLOTS}`);
  if (MAP_ITEMS.length > MAP_ITEM_SLOTS) errors.push(`${MAP_ITEMS.length} map items, but the game has ${MAP_ITEM_SLOTS}`);
  const areaOf = new Map<string, string>();
  for (const a of AREAS) {
    for (const p of a.places) {
      if (areaOf.has(p)) errors.push(`${p} is on two maps: ${areaOf.get(p)} and ${a.id}`);
      areaOf.set(p, a.id);
      if (!plan.places.some((x) => x.id === p)) errors.push(`${a.id} lists ${p}, which the plan doesn't have`);
    }
  }
  for (const p of plan.places) if (!areaOf.has(p.id)) errors.push(`${p.id} is on no map`);
  if (STAGES.length > STAGE_SLOTS) errors.push(`${STAGES.length} overview stages, but the map screen has ${STAGE_SLOTS}`);
  for (const st of STAGES) if (st.areas.length > AREAS_PER_STAGE) errors.push(`${st.name} has ${st.areas.length} areas, but a stage lists ${AREAS_PER_STAGE}`);
  for (const a of AREAS) {
    const n = STAGES.filter((st) => st.areas.includes(a.id)).length;
    if (n !== 1) errors.push(`${a.id} is in ${n} overview stages, not one`);
  }
  const shown = new Map<string, string>();
  for (const m of MAP_ITEMS) {
    const step = plan.steps.find((s) => s.id === m.step);
    if (!step || step.kind !== 'find') errors.push(`${m.id}: the plan has no find step ${m.step}`);
    for (const a of m.areas) {
      if (!AREAS.some((x) => x.id === a)) errors.push(`${m.id} shows ${a}, which is no area`);
      if (shown.has(a)) errors.push(`${a} is shown by two maps: ${shown.get(a)} and ${m.id}`);
      shown.set(a, m.id);
    }
  }
  return errors;
}
