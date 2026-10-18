// A playthrough's state, saved where it stands and loaded into a fresh game:
// the script flags that record what she has done, her bag, the item box, the
// room and where she stands in it. A long run saves one after every job, so a
// later run can start there instead of from the ridge (tests/playthrough.ts
// --quarter).
import { readFileSync, writeFileSync } from 'node:fs';
import type { GameLink } from './link.ts';
import { Bank, type GameState } from './state.ts';
import { settle } from './flows.ts';

export interface Checkpoint {
  /** The goals done, by the playthrough's ids. */
  readonly reached: readonly string[];
  readonly stage: number;
  readonly room: number;
  readonly at: { readonly x: number; readonly z: number; readonly angle: number };
  /** The banks that hold the day's progress, as hex: what she has done, opened, killed and taken. */
  readonly banks: Readonly<Record<number, string>>;
  readonly items: readonly (readonly [id: number, qty: number])[];
  readonly box: readonly (readonly [id: number, qty: number])[];
  /** Her weapon in hand, the bag slot counted from 1; 0 for none. */
  readonly weapon: number;
  /** Made up from the plan rather than saved from a game: proves less. */
  readonly built?: boolean;
}

/** The banks a checkpoint carries; the rest are the engine's working state for the frame or the room. */
export const SAVED_BANKS = [Bank.common, Bank.locks, Bank.enemies, Bank.roomItems] as const;

const hex = (b: Uint8Array) => Buffer.from(b).toString('hex');

export function take(s: GameState, reached: Iterable<string>): Checkpoint {
  return {
    reached: [...reached],
    stage: s.stage,
    room: s.room,
    at: { x: s.player.x, z: s.player.z, angle: s.player.angle },
    banks: Object.fromEntries(SAVED_BANKS.map((b) => [b, hex(s.banks[b]!)])),
    items: s.items.map((i) => [i.id, i.qty] as const),
    box: s.box.map((i) => [i.id, i.qty] as const),
    weapon: s.player.weapon,
  };
}

export const save = (file: string, cp: Checkpoint) => writeFileSync(file, JSON.stringify(cp, null, 1));
export const load = (file: string): Checkpoint => JSON.parse(readFileSync(file, 'utf8')) as Checkpoint;

/** Read flag `n` of a bank's hex, laid out as the state line's (32-bit LE words, top bit first). */
export function bit(bankHex: string, n: number): boolean {
  const b = Buffer.from(bankHex, 'hex');
  const at = (n >> 5) * 4;
  return ((b.readUInt32LE(at) >>> (31 - (n & 31))) & 1) === 1;
}

/**
 * Make the running game what the checkpoint says: the flags that differ, her
 * bag and the box slot by slot, then the room entered afresh so its scripts
 * set it up for those flags, and her on her spot.
 */
export async function restore(link: GameLink, cp: Checkpoint): Promise<GameState> {
  let s = await settle(link);
  for (const b of SAVED_BANKS) {
    const want = cp.banks[b];
    if (!want) continue;
    const words = Buffer.from(want, 'hex').length / 4;
    const have = hex(s.banks[b]!);
    for (let n = 0; n < words * 32; n++) {
      const on = bit(want, n);
      if (on !== bit(have, n)) await link.setFlag(b, n, on);
    }
  }
  for (const [i, [id, qty]] of cp.items.entries()) await link.slot(i, id, qty);
  s = await link.state();
  for (const [i, [id, qty]] of cp.box.entries()) {
    const now = s.box[i];
    if (!now || now.id !== id || now.qty !== qty) await link.boxSlot(i, id, qty);
  }
  await link.room(cp.stage, cp.room);
  await settle(link, (st) => st.stage === cp.stage && st.room === cp.room);
  await link.place(cp.at.x, cp.at.z, cp.at.angle);
  await link.equip(cp.weapon);
  return settle(link, (st) => st.stage === cp.stage && st.room === cp.room);
}
