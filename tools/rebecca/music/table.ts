// Her mode's music table, from the cues (plan/music.ts): which WAVs each of
// her rooms plays, and which of them each room starts with. build.ts writes it
// into her overlay as sound/music.dat, which src/game/RebMusic.cpp reads, and
// sets each room's music state in her BIO_CARD.DAT. Chris's and Jill's games
// keep RE1's own table.
//
// A cue is one group, as in RE1: rooms with the same cue keep the music going
// through the door, and only the channels whose bits differ start or stop. A
// channel plays a file when it has one:
// - reuse: RE1's own file under sound/, from the player's own game;
// - new: our render, music/renders/<sketch>.wav, shipped as sound/Reb_<cue>.wav
//   for channel 0 and sound/Reb_<cue>_<n>.wav for channel n;
// - ambience, or a sketch not rendered yet: nothing.
// A room whose cue has no file at all is silent.
//
// A room's state byte (SoundSystem.cpp update_room_bgm): bits 0-2 pick the
// group from the room's row, bits 3-5 switch channels 0-2 on, 0xFF is
// silence. Room scripts change it with opcode 0x37 (musicSwitches below,
// day/scripts.ts writes them).
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
/** The bit that switches channel n on. */
export const channelBit = (n: number) => 8 << n;
/** Longest WAV base name the table holds, its NUL aside (RebMusic.cpp kFileLen). */
const NAME_MAX = 15;

export interface Slot {
  readonly slug: string;
  readonly stage: number;
  readonly room: number;
}

export interface GroupChannel {
  /** The WAV under sound/, without .wav. */
  readonly file: string;
  /** Our render to copy in as sound/<file>.wav; absent for RE1's own file. */
  readonly render?: string;
}

export interface Group {
  readonly cue: string;
  /** Channels 0-2; null for a channel with no file. */
  readonly channels: readonly (GroupChannel | null)[];
}

export interface RoomMusic extends Slot {
  readonly place: string;
  readonly cue: string;
  /** Index into the groups, or null for a silent room. */
  readonly group: number | null;
  /** The group a takeover plays here (plan/music.ts Takeover), as the row's second. */
  readonly takeover: number | null;
  /** The state byte it starts the day with. */
  readonly state: number;
}

export interface MusicTable {
  readonly groups: readonly Group[];
  readonly rooms: readonly RoomMusic[];
}

/** The file name a new cue's channel ships as. */
export const renderedName = (cue: string, channel = 0) => (channel === 0 ? `Reb_${cue}` : `Reb_${cue}_${channel}`);

/** Whether a cue's channel plays in a place once `happened` says which steps have happened. */
function channelOn(c: Cue, n: number, place: string, happened: boolean): boolean {
  const ch = c.channels[n]!;
  if (ch.in && !ch.in.includes(place)) return false;
  if (!ch.switched) return true;
  return 'on' in ch.switched ? happened : !happened;
}

/** The step a cue's channels switch at, if any (checkMusic allows one). */
export function cueStep(c: Cue): string | undefined {
  const ch = c.channels.find((x) => x.switched);
  return ch?.switched ? ('on' in ch.switched ? ch.switched.on : ch.switched.off) : undefined;
}

/**
 * The table for her rooms. `rendered` says whether a sketch's render exists.
 * Throws when a place the cues name has no room, or a room is in two places.
 */
export function musicTable(cues: readonly Cue[], places: readonly Place[], rooms: readonly Slot[], rendered: (sketch: string) => boolean): MusicTable {
  const groups: Group[] = [];
  const groupOf = new Map<string, number | null>();
  const group = (c: Cue): number | null => {
    if (groupOf.has(c.id)) return groupOf.get(c.id)!;
    const channels: (GroupChannel | null)[] =
      c.kind === 'reuse' && c.file ? [{ file: c.file }]
      : c.kind === 'new' ? c.channels.map((ch, n) => (ch.sketch && rendered(ch.sketch) ? { file: renderedName(c.id, n), render: ch.sketch } : null))
      : [];
    for (const ch of channels) if (ch && ch.file.length > NAME_MAX) throw new Error(`${c.id}: ${ch.file} is longer than ${NAME_MAX} characters`);
    const n = channels.some(Boolean) ? groups.push({ cue: c.id, channels }) - 1 : null;
    groupOf.set(c.id, n);
    return n;
  };
  const takeoverOf = new Map<string, Cue>();
  for (const c of cues) for (const p of c.takesOver?.places ?? []) takeoverOf.set(p, c);
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
      const g = group(c);
      const over = takeoverOf.get(id);
      const room = { slug, stage: slot.stage, room: slot.room, place: id, cue: c.id, group: g, takeover: over ? group(over) : null };
      out.push({ ...room, state: stateOf(c, room, groups, false) });
    }
  }
  for (const r of rooms) {
    if (!out.some((m) => m.slug === r.slug)) throw new Error(`${r.slug}: no cue plays there, so it would keep RE1's row for stage ${r.stage} room ${r.room}`);
  }
  return { groups, rooms: out };
}

/** A room's state byte for its own cue: group 0 of its row and the channels on, or silence. */
function stateOf(c: Cue, r: Pick<RoomMusic, 'place' | 'group'>, groups: readonly Group[], happened: boolean): number {
  if (r.group === null) return STATE_SILENT;
  const files = groups[r.group]!.channels;
  let state = 0;
  for (let n = 0; n < files.length; n++) if (files[n] && channelOn(c, n, r.place, happened)) state |= channelBit(n);
  return state;
}

/** One opcode 0x37: a room's state byte. */
export interface StateWrite {
  readonly slug: string;
  readonly stage: number;
  readonly room: number;
  readonly state: number;
}

/** What the room script that does a step (day/events.ts) does to the music. */
export interface StepSwitch {
  readonly step: string;
  /** Every room of the cue whose state the step changes. */
  readonly writes: readonly StateWrite[];
  /** The channels to start or stop at once, by room: the step's room plays them if it is one of these. */
  readonly now: readonly { readonly slug: string; readonly channel: number; readonly on: boolean }[];
}

/** A takeover's scripts (plan/music.ts Takeover): what starts it, and what puts the rooms back. */
export interface TakeoverSwitch {
  readonly cue: string;
  readonly start: readonly StateWrite[];
  /** The rooms whose entry ends it. */
  readonly ends: readonly string[];
  /** The rooms' own states again, before and after their cue's step, if it has one. */
  readonly back: { readonly step?: string; readonly before: readonly StateWrite[]; readonly after: readonly StateWrite[] };
}

/** The scripts' side of the table: what each step and each takeover writes. */
export function musicSwitches(cues: readonly Cue[], t: MusicTable): { steps: StepSwitch[]; takeovers: TakeoverSwitch[] } {
  const cueOf = (id: string) => cues.find((c) => c.id === id)!;
  const steps: StepSwitch[] = [];
  for (const c of cues) {
    const step = cueStep(c);
    const rooms = t.rooms.filter((r) => r.cue === c.id && r.group !== null);
    if (!step || rooms.length === 0) continue;
    const writes: StateWrite[] = [];
    const now: StepSwitch['now'][number][] = [];
    for (const r of rooms) {
      const after = stateOf(c, r, t.groups, true);
      if (after === r.state) continue;
      writes.push({ slug: r.slug, stage: r.stage, room: r.room, state: after });
      for (let n = 0; n < 3; n++) {
        const bit = channelBit(n);
        if ((after & bit) !== (r.state & bit)) now.push({ slug: r.slug, channel: n, on: (after & bit) !== 0 });
      }
    }
    if (writes.length) steps.push({ step, writes, now });
  }
  const takeovers: TakeoverSwitch[] = [];
  for (const c of cues) {
    if (!c.takesOver) continue;
    const rooms = t.rooms.filter((r) => c.takesOver!.places.includes(r.place) && r.takeover !== null);
    if (rooms.length === 0) continue;
    const g = t.groups[rooms[0]!.takeover!]!;
    // Group 1 of the row, every channel the takeover's cue has a file for.
    const state = 1 | g.channels.reduce((s, ch, n) => (ch ? s | channelBit(n) : s), 0);
    const own = cueOf(rooms[0]!.cue);
    const write = (happened: boolean) => rooms.map((r) => ({ slug: r.slug, stage: r.stage, room: r.room, state: stateOf(own, r, t.groups, happened) }));
    takeovers.push({
      cue: c.id,
      start: rooms.map((r) => ({ slug: r.slug, stage: r.stage, room: r.room, state })),
      ends: c.takesOver.until.map((p) => t.rooms.find((r) => r.place === p)?.slug ?? p),
      back: { step: cueStep(own), before: write(false), after: write(true) },
    });
  }
  return { steps, takeovers };
}

/** sound/music.dat, in the format src/game/RebMusic.cpp reads. */
export function musicFile(t: MusicTable): Uint8Array {
  if (t.groups.length > 0xff - 57 || t.rooms.length > 0xff) throw new Error('too many groups or rooms for the table');
  const bytes = new Uint8Array(8 + t.groups.length * 52 + t.rooms.length * 6);
  bytes.set([0x52, 0x42, 0x4d, 0x31, t.groups.length, t.rooms.length]); // "RBM1"
  t.groups.forEach((g, i) => {
    const at = 8 + i * 52;
    g.channels.forEach((ch, n) => {
      if (!ch) return;
      bytes.set(new TextEncoder().encode(ch.file), at + n * 16);
      bytes[at + 48 + n] = 1; // loops
    });
  });
  t.rooms.forEach((r, i) => {
    const at = 8 + t.groups.length * 52 + i * 6;
    bytes.set([r.stage, r.room, r.group ?? 0xff, r.takeover ?? 0xff, 0xff, 0xff], at);
  });
  return bytes;
}

/** Set each of her rooms' music state in a BIO_CARD.DAT: the channels it starts with, or silence. */
export function setRoomStates(card: Uint8Array, t: MusicTable): void {
  for (const r of t.rooms) card[CARD_ROOM_BGM + r.stage * 32 + r.room] = r.state;
}
