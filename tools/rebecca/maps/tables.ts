// What the engine needs to know of her maps, from the plan (plan/maps.ts):
// which area and palette block each of her rooms is, the bit that records
// she has been in it, which map item shows each area, and which overview
// stage lists it. engine.ts writes these into src/game/RebMaps.cpp.
import { dayRooms } from '../day/rooms.ts';
import { AREAS, MAP_ITEMS, STAGES } from '../plan/maps.ts';
import { slugOfPlace } from './floors.ts';

/** g_RoomFlags bits from here up are the maps owned and the files read (src/game/BioCard.h). */
export const ROOM_FLAG_MAP_BASE = 0x7c;

export interface MapRoom {
  readonly place: string;
  /** Stage from 0, and room id. */
  readonly stage: number;
  readonly room: number;
  /** Index into AREAS, and the room's palette block in that area's map. */
  readonly area: number;
  readonly slot: number;
  /**
   * The g_RoomFlags bit for "she has been here". RE1's bits are by stage and
   * room id (g_StageRoomFlagOffset), which her ids above the stages' own
   * would run past, into the maps and files; hers are one per place.
   */
  readonly bit: number;
}

/** The mansion's save room is RE1's own: ROOM100. */
const GAME_ROOMS: Record<string, { stage: number; room: number }> = { save: { stage: 0, room: 0 } };

export function mapRooms(): MapRoom[] {
  const out: MapRoom[] = [];
  AREAS.forEach((a, area) =>
    a.places.forEach((place, slot) => {
      const spec = GAME_ROOMS[place] ?? dayRooms.find((r) => r.slug === slugOfPlace(place));
      if (!spec) throw new Error(`${place}: no room for it in day/rooms.ts`);
      out.push({ place, stage: spec.stage, room: spec.room, area, slot, bit: out.length });
    }),
  );
  if (out.length > ROOM_FLAG_MAP_BASE) throw new Error(`${out.length} rooms, but g_RoomFlags has ${ROOM_FLAG_MAP_BASE} bits before the maps`);
  return out;
}

/** The map item index (item 0x4E + index) that shows each area, or undefined for none. */
export function mapIndexOf(areaId: string): number | undefined {
  const i = MAP_ITEMS.findIndex((m) => m.areas.includes(areaId));
  return i < 0 ? undefined : i;
}

export function stageOf(areaId: string): number {
  return STAGES.findIndex((s) => s.areas.includes(areaId));
}
