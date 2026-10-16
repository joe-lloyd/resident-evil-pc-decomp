// Her mode's music table, from the cues (plan/music.ts): which WAV each of her
// rooms plays. build.ts writes it into her overlay as sound/music.dat, which
// src/game/RebMusic.cpp reads, and sets each room's music state in her
// BIO_CARD.DAT. Chris's and Jill's games keep RE1's own table.
//
// A cue is one group, as in RE1: rooms with the same cue keep the music going
// through the door. A cue plays a file when it has one:
// - reuse: RE1's own file under sound/, from the player's own game;
// - new: our render, music/renders/<sketch>.wav, shipped as sound/Reb_<cue>.wav;
// - ambience, or a new cue not rendered yet: nothing, so its rooms stay silent.
//
// A place that is a room of the original game (the mansion's save room) is
// left out, so it keeps RE1's row.
import type { Cue } from '../plan/music.ts';
import type { Place } from '../plan/plan.ts';

/** RE1's per-room music state bytes in BIO_CARD.DAT (src/game/BioCard.h roomBgmState): 7 stages of 32 rooms. */
export const CARD_ROOM_BGM = 0x33c;
/** A room's state: group 0 of its row, channel 0 on (bit 3), loaded and started on entry (type 0). */
export const STATE_PLAY = 0x08;
/** A room's state for silence. */
export const STATE_SILENT = 0xff;
/** Longest WAV base name the table holds, its NUL aside (RebMusic.cpp kFileLen). */
const NAME_MAX = 15;

export interface Slot {
  readonly slug: string;
  readonly stage: number;
  readonly room: number;
}

export interface Group {
  readonly cue: string;
  /** The WAV under sound/, without .wav. */
  readonly file: string;
  /** Our render to copy in as sound/<file>.wav; absent for RE1's own file. */
  readonly render?: string;
}

export interface RoomMusic extends Slot {
  readonly place: string;
  readonly cue: string;
  /** Index into the groups, or null for a silent room. */
  readonly group: number | null;
}

export interface MusicTable {
  readonly groups: readonly Group[];
  readonly rooms: readonly RoomMusic[];
}

/** The file name a new cue's render ships as. */
export const renderedName = (cue: string) => `Reb_${cue}`;

/**
 * The table for her rooms. `rendered` says whether a sketch's render exists.
 * Throws when a place the cues name has no room, or a room is in two places.
 */
export function musicTable(cues: readonly Cue[], places: readonly Place[], rooms: readonly Slot[], rendered: (sketch: string) => boolean): MusicTable {
  const groups: Group[] = [];
  const groupOf = new Map<string, number | null>();
  const group = (c: Cue): number | null => {
    if (groupOf.has(c.id)) return groupOf.get(c.id)!;
    const g: Group | undefined =
      c.kind === 'reuse' && c.file ? { cue: c.id, file: c.file }
      : c.kind === 'new' && c.sketch && rendered(c.sketch) ? { cue: c.id, file: renderedName(c.id), render: c.sketch }
      : undefined;
    if (g && g.file.length > NAME_MAX) throw new Error(`${c.id}: ${g.file} is longer than ${NAME_MAX} characters`);
    const n = g ? groups.push(g) - 1 : null;
    groupOf.set(c.id, n);
    return n;
  };
  const out: RoomMusic[] = [];
  const seen = new Set<string>();
  for (const c of cues) {
    for (const id of c.places) {
      const place = places.find((p) => p.id === id);
      if (!place) throw new Error(`${c.id} plays in ${id}, which is not in the plan`);
      if (place.existing) continue;
      const slug = place.room ?? place.id;
      const slot = rooms.find((r) => r.slug === slug);
      if (!slot) throw new Error(`${id}: no room ${slug} in day/rooms.ts`);
      const key = `${slot.stage}:${slot.room}`;
      if (seen.has(key)) throw new Error(`${id}: stage ${slot.stage} room ${slot.room} is already another place's`);
      seen.add(key);
      out.push({ slug, stage: slot.stage, room: slot.room, place: id, cue: c.id, group: group(c) });
    }
  }
  for (const r of rooms) {
    if (!out.some((m) => m.slug === r.slug)) throw new Error(`${r.slug}: no cue plays there, so it would keep RE1's row for stage ${r.stage} room ${r.room}`);
  }
  return { groups, rooms: out };
}

/** sound/music.dat, in the format src/game/RebMusic.cpp reads. */
export function musicFile(t: MusicTable): Uint8Array {
  if (t.groups.length > 0xff - 57 || t.rooms.length > 0xff) throw new Error('too many groups or rooms for the table');
  const bytes = new Uint8Array(8 + t.groups.length * 52 + t.rooms.length * 6);
  bytes.set([0x52, 0x42, 0x4d, 0x31, t.groups.length, t.rooms.length]); // "RBM1"
  t.groups.forEach((g, i) => {
    const at = 8 + i * 52;
    // One channel: the cue's whole mix. Channels 1 and 2 stay empty.
    bytes.set(new TextEncoder().encode(g.file), at);
    bytes[at + 48] = 1; // loops
  });
  t.rooms.forEach((r, i) => {
    const at = 8 + t.groups.length * 52 + i * 6;
    bytes.set([r.stage, r.room, r.group ?? 0xff, 0xff, 0xff, 0xff], at);
  });
  return bytes;
}

/** Set each of her rooms' music state in a BIO_CARD.DAT: play its group, or silence. */
export function setRoomStates(card: Uint8Array, t: MusicTable): void {
  for (const r of t.rooms) card[CARD_ROOM_BGM + r.stage * 32 + r.room] = r.group === null ? STATE_SILENT : STATE_PLAY;
}
