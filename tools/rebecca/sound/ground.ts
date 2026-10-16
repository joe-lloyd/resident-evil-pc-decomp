// What her footsteps sound like on each kind of floor, and the room sound
// rows that give her rooms those steps.
//
// A footstep plays entity sound slot k (walking), k + 1 (running) or k + 2
// (falling), where k is the low byte of the footstep zone she stands in
// (src/game/SoundSystem.cpp, PlayEntitySnd and LookupFootstepZone). The room's
// row names the WAV in each slot. RE1's rows give its rooms their floors'
// steps there; hers are empty, so her overlay brings her own
// (sound/rooms.dat, src/game/RebSound.cpp).
//
// Each kind is RE1's own steps for that floor, from the player's own files,
// or our own made by code where RE1 has none (footsteps.ts):
// - earth: packed dirt, needles, grass: ours.
// - gravel: loose stones: ours.
// - boards: ft_wd, the mansion's wooden floors.
// - rock: ft_cave, the caves under the courtyard.
// - water: ft_swim, wading through the flooded rooms under the guardhouse.
// - concrete: ft_conc, the guardhouse basement and the lab.
// - metal: ft_pla, the steel plates of the lab and its lifts.
import { footstep, GROUND_STEPS, wav } from '../footsteps.ts';

export const GROUNDS = ['earth', 'gravel', 'boards', 'rock', 'water', 'concrete', 'metal'] as const;
export type Ground = (typeof GROUNDS)[number];

export const isGround = (s: string): s is Ground => (GROUNDS as readonly string[]).includes(s);

/** The three WAVs (without .wav) of a footstep set: walking, running, falling down. */
export interface StepSet {
  readonly walk: string;
  readonly run: string;
  readonly fall: string;
}

export const STEP_SETS: Record<Ground, StepSet> = {
  earth: { walk: 'Reb_ftEarthA', run: 'Reb_ftEarthB', fall: 'taore_ca' },
  gravel: { walk: 'Reb_ftGravA', run: 'Reb_ftGravB', fall: 'taore_ca' },
  boards: { walk: 'ft_wdA', run: 'ft_wdB', fall: 'taore_wd' },
  rock: { walk: 'ft_caveA', run: 'ft_caveB', fall: 'taore_ca' },
  water: { walk: 'ft_swimA', run: 'ft_swimB', fall: 'taore_wa' },
  concrete: { walk: 'ft_concA', run: 'ft_concB', fall: 'taore_st' },
  metal: { walk: 'ft_plaA', run: 'ft_plaB', fall: 'taore_pl' },
};

/** Our own steps, which the build ships under the names STEP_SETS gives them. */
export function groundStepFiles(): { name: string; bytes: Uint8Array }[] {
  return [
    { name: `${STEP_SETS.earth.walk}.wav`, bytes: wav(footstep(11, 1, GROUND_STEPS.earth.walk)) },
    { name: `${STEP_SETS.earth.run}.wav`, bytes: wav(footstep(12, 1, GROUND_STEPS.earth.run)) },
    { name: `${STEP_SETS.gravel.walk}.wav`, bytes: wav(footstep(13, 1, GROUND_STEPS.gravel.walk)) },
    { name: `${STEP_SETS.gravel.run}.wav`, bytes: wav(footstep(14, 1, GROUND_STEPS.gravel.run)) },
  ];
}

/**
 * The slots a room's footstep sets start at, the room's own floor first.
 * RE1's rooms keep theirs at the top of the row, under the enemies' cries
 * (0-9), the room's things (0x14-0x22) and the ladder (0x23).
 */
export const STEP_SLOTS = [0x2d, 0x2a, 0x27, 0x24] as const;

/** A room's floors: the kind underfoot by default, then parts of it that are something else, the first that holds her winning. */
export interface Floors {
  readonly ground: Ground;
  readonly parts: readonly { readonly kind: Ground; readonly x0: number; readonly z0: number; readonly x1: number; readonly z1: number }[];
}

/** The footstep set each kind a room has takes: its slot, the room's own ground first. Throws past four kinds. */
export function stepSlots(f: Floors): Map<Ground, number> {
  const kinds = [f.ground, ...f.parts.map((p) => p.kind)].filter((k, i, all) => all.indexOf(k) === i);
  if (kinds.length > STEP_SLOTS.length) throw new Error(`${kinds.length} kinds of floor (${kinds.join(', ')}); a room has room for ${STEP_SLOTS.length}`);
  return new Map(kinds.map((k, i) => [k, STEP_SLOTS[i]!]));
}

/** One room's own sounds: entity sound slot to WAV base name. */
export interface RoomSounds {
  readonly stage: number;
  readonly room: number;
  readonly slots: ReadonlyMap<number, string>;
}

/** The slots a room's floors fill. */
export function floorSounds(stage: number, room: number, f: Floors): RoomSounds {
  const slots = new Map<number, string>();
  for (const [kind, at] of stepSlots(f)) {
    const set = STEP_SETS[kind];
    slots.set(at, set.walk);
    slots.set(at + 1, set.run);
    slots.set(at + 2, set.fall);
  }
  return { stage, room, slots };
}

/** Longest WAV base name a slot holds, its NUL aside (RebSound.cpp kNameLen). */
const NAME_MAX = 14;

/** sound/rooms.dat, in the format src/game/RebSound.cpp reads. */
export function roomsFile(rooms: readonly RoomSounds[]): Uint8Array {
  if (rooms.length > 0xff) throw new Error(`${rooms.length} rooms; the file holds 255`);
  const size = 8 + rooms.reduce((n, r) => n + 4 + r.slots.size * 16, 0);
  const out = new Uint8Array(size);
  out.set([0x52, 0x42, 0x53, 0x31, rooms.length]); // "RBS1"
  let at = 8;
  for (const r of rooms) {
    if (r.stage > 6 || r.room > 31) throw new Error(`stage ${r.stage} room ${r.room} is past the table`);
    out.set([r.stage, r.room, r.slots.size], at);
    at += 4;
    for (const [slot, name] of [...r.slots].sort((a, b) => a[0] - b[0])) {
      if (slot > 47) throw new Error(`slot ${slot} is past the 48 a room has`);
      if (name.length > NAME_MAX || !/^[\x21-\x7e]*$/.test(name)) throw new Error(`${name}: not a WAV name of up to ${NAME_MAX} characters`);
      out[at] = slot;
      out.set(new TextEncoder().encode(name), at + 1);
      at += 16;
    }
  }
  return out;
}
