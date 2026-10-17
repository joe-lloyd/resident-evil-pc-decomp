// Rebecca's day played the way a player would, one function per stretch of
// it; each starts where the one before ends. docs/REBECCA_DAY.md is the plan,
// tools/rebecca/day/ the rooms. Zones are the ones the rooms' scripts set
// (game units, metres * 1700 in the new rooms).
import { check, fight, goTo, settle, useFightBack, useItem } from './flows.ts';
import type { GameLink } from './link.ts';
import { Run, commonFlag, inRoom } from './scenario.ts';
import type { GameState } from './state.ts';
import { CUT_FLAGS } from '../rebecca/day/cutscenes.ts';

export const DAY = {
  trail: { stage: 2, room: 0x12 },
  ridge: { stage: 2, room: 0x13 },
  lookout: { stage: 2, room: 0x14 },
  yard: { stage: 2, room: 0x15 },
  shed: { stage: 2, room: 0x16 },
  bridge: { stage: 2, room: 0x17 },
} as const;

/** Room item flag `n` (bank 7, set while the item is still there) is clear: she took it. */
const taken = (s: GameState, n: number) => {
  const b = s.banks[7];
  return ((new DataView(b.buffer, b.byteOffset, b.byteLength).getUint32((n >> 5) * 4, true) >>> (31 - (n & 31))) & 1) === 0;
};
const SPRAY_FLAG = 241;
/** The logbook's room-item flag: files/documents.ts, ITEM_FLAG_BASE plus its place in BOOKS. */
const LOGBOOK_FLAG = 230;
const KEY_FLAG = 242;
const CRANK_FLAG = 243;
const HEX_CRANK = 30;
const FIRST_AID_SPRAY = 65;
const CERBERUS = 2;
const ADDER = 10;
/** Crows only peck, and the Beretta takes minutes over them: she runs past. Standing to shoot, the trail's two killed her. */
export const CROW = 5;

const YARD = {
  pine: { x: 24310, z: 19380, w: 4930, d: 1360 },
  winch: { x: 19210, z: 17170, w: 1700, d: 2380 },
  cabin: { x: 21080, z: 12325, w: 1870, d: 1020 },
  shed: { x: 9180, z: 12410, w: 1190, d: 1360 },
};
const CABIN = {
  door: { x: 5950, z: 9100, w: 1530, d: 1100 },
  radio: { x: 4335, z: 4675, w: 850, d: 935 },
  logbook: { x: 5880, z: 4675, w: 800, d: 935 },
  spray: { x: 6120, z: 6630, w: 1700, d: 1700 },
  key: { x: 4930, z: 9095, w: 935, d: 1105 },
};
const SHED = {
  door: { x: 5100, z: 2890, w: 1020, d: 1360 },
  crank: { x: 2805, z: 3145, w: 1105, d: 1360 },
};
const BRIDGE = {
  sign: { x: 5950, z: 27880, w: 8500, d: 1020 },
};

/** Check a zone until `done` holds, a few tries; returns the last state. */
async function checkUntil(run: Run, zone: { x: number; z: number; w: number; d: number }, done: (s: GameState) => boolean): Promise<GameState> {
  let s = await run.link.state();
  for (let i = 0; i < 3 && !done(s); i++) s = await check(run.link, zone);
  return s;
}

/** FG_COMMON flag of the opening scene on the ridge (rebecca/day/cutscenes.ts). */
const OPENING = CUT_FLAGS.get('cut-opening')!;

/** The ridge: the opening scene, then the path east down to the trail. */
export async function ridge(run: Run): Promise<void> {
  const { link } = run;
  let s = await settle(link, (st) => inRoom(st, DAY.ridge));
  if (!commonFlag(s, OPENING)) run.fail('the opening scene never played');
  run.log(s, 'on the ridge');
  await run.picture('day-ridge');
  s = await goTo(link, run.dataDirs, 12800, 5300, { radius: 400 });
  s = await settle(link, (st) => inRoom(st, DAY.trail));
  run.log(s, 'down the path to the trail');
}

/** The mountain trail, top to bottom, through its foot to the ranger station's yard. */
export async function trail(run: Run): Promise<void> {
  const s = await run.door({ x: 1500, z: 15200, w: 4000, d: 2000 }, DAY.yard, 'down to the ranger station');
  run.log(s, 'at the ranger station');
}

/** The yard on arrival: her first thought, the pine across the trail, the winch with no crank, into the cabin. */
export async function yard(run: Run): Promise<void> {
  const { link } = run;
  let s = await settle(link, (st) => inRoom(st, DAY.yard));
  if (!commonFlag(s, 202)) run.fail('her first thought at the station never showed');
  await run.picture('day-yard-0');
  const pine = run.expectMessage(0x81, 'the pine across the trail', 60_000);
  s = await check(link, YARD.pine);
  if (await pine()) run.log(s, 'the pine blocks the trail down');
  else run.fail('checking the fallen pine said nothing');
  await run.picture('day-yard-pine');
  const winch = run.expectMessage(0x82, 'the winch', 60_000);
  s = await check(link, YARD.winch);
  if (await winch()) run.log(s, 'the winch has no crank');
  else run.fail('checking the winch said nothing');
  s = await run.door(YARD.cabin, DAY.lookout, 'into the ranger\'s cabin');
}

/** Inside the cabin: the radio, the logbook, the First Aid Spray, the shed key, and out. */
export async function lookout(run: Run): Promise<void> {
  const { link } = run;
  let s = await settle(link, (st) => inRoom(st, DAY.lookout));
  if (!commonFlag(s, 201)) run.fail('her first thought in the cabin never showed');
  await run.picture('day-lookout-0');
  const radio = run.expectMessage(0x81, 'the radio', 60_000);
  s = await check(link, CABIN.radio);
  if (await radio()) run.log(s, 'listened to the radio');
  else run.fail('the radio said nothing');
  // The logbook is a file she takes (files/documents.ts); tests/files.ts reads its pages.
  s = await checkUntil(run, CABIN.logbook, (st) => taken(st, LOGBOOK_FLAG));
  if (taken(s, LOGBOOK_FLAG)) run.log(s, 'took the logbook: the crank is in the shed');
  else run.fail('could not take the logbook from the desk');
  s = await checkUntil(run, CABIN.spray, (st) => taken(st, SPRAY_FLAG));
  if (taken(s, SPRAY_FLAG)) run.log(s, 'took the First Aid Spray');
  else run.fail('could not take the First Aid Spray from the table');
  s = await checkUntil(run, CABIN.key, (st) => taken(st, KEY_FLAG));
  if (taken(s, KEY_FLAG)) run.log(s, 'took the shed key');
  else run.fail('could not take the shed key from its hook');
  await run.picture('day-lookout-1');
  await run.door(CABIN.door, DAY.yard, 'out to the yard');
}

/** Back in the yard with the key: the dog comes out of the trees. */
export async function dog(run: Run): Promise<void> {
  const { link } = run;
  let s = await settle(link, (st) => inRoom(st, DAY.yard));
  s = await link.waitFor((st) => st.enemies.some((e) => e.type === CERBERUS && e.hp > 0), 'the dog', 20_000).catch(() => s);
  if (!s.enemies.some((e) => e.type === CERBERUS)) {
    run.fail('no dog came out of the trees');
    return;
  }
  await run.picture('day-yard-dog');
  const shots = await fight(link);
  s = await settle(link);
  run.log(s, `killed the dog (${shots} shots)`);
  await heal(run);
}

/** The shed: the key opens the padlock; the crank on the bench; out again. */
export async function shed(run: Run): Promise<void> {
  const { link } = run;
  let s = await run.door(YARD.shed, DAY.shed, 'unlocked the shed and went in');
  s = await settle(link, (st) => inRoom(st, DAY.shed));
  if (!commonFlag(s, 203)) run.fail('her first thought in the shed never showed');
  await run.picture('day-shed');
  s = await checkUntil(run, SHED.crank, (st) => taken(st, CRANK_FLAG));
  if (taken(s, CRANK_FLAG) && s.items.some((it) => it.id === HEX_CRANK)) run.log(s, 'took the winch crank');
  else run.fail('could not take the crank from the bench');
  await run.door(SHED.door, DAY.yard, 'out of the shed');
}

/** The crank on the winch: the pine is dragged off the trail, and the way down opens. */
export async function winch(run: Run): Promise<void> {
  const { link } = run;
  let s = await settle(link, (st) => inRoom(st, DAY.yard));
  const zone = YARD.winch;
  s = await goTo(link, run.dataDirs, zone.x + zone.w / 2, zone.z + zone.d / 2, { radius: 300 });
  const cranked = run.expectMessage(0x88, 'the pine dragging clear', 60_000);
  s = await useItem(link, HEX_CRANK);
  if (await cranked()) run.log(s, 'cranked the winch');
  else run.fail('using the crank at the winch did nothing');
  s = await link.state();
  if (!commonFlag(s, 205)) run.fail('the pine is not marked as moved');
  // She keeps the crank: the pond's sluice takes it too (yard/room.c).
  if (!s.items.some((it) => it.id === HEX_CRANK)) run.fail('the winch took her crank, and the pond needs it');
  await run.picture('day-yard-pine-moved');
  s = await run.door(YARD.pine, DAY.bridge, 'down the trail past the pine');
}

/** Hurt badly: use the First Aid Spray if she carries one, as a player would. */
async function heal(run: Run): Promise<void> {
  const s = await run.link.state();
  if (s.player.hp >= 45 || !s.items.some((it) => it.id === FIRST_AID_SPRAY)) return;
  const after = await useItem(run.link, FIRST_AID_SPRAY);
  run.log(after, `used the First Aid Spray (${s.player.hp} to ${after.player.hp})`);
}

/** The ravine bridge: through the adders' grass (shooting what comes at her), across, to the valley trail sign. */
export async function bridge(run: Run): Promise<void> {
  const { link } = run;
  let s = await settle(link, (st) => inRoom(st, DAY.bridge));
  if (!commonFlag(s, 204)) run.fail('her first thought at the gorge never showed');
  await run.picture('day-bridge-0');
  await heal(run);
  // Adders lie low in the grass and only strike close: walk past them.
  useFightBack(9000, [ADDER, CROW]);
  s = await goTo(link, run.dataDirs, 10200, 18700, { radius: 500 });
  run.log(s, 'on the bridge');
  await run.picture('day-bridge-mid');
  s = await check(link, BRIDGE.sign);
  if (commonFlag(s, 206)) run.log(s, 'across the gorge: the valley trail sign');
  else run.fail('could not read the valley trail sign');
  await run.picture('day-bridge-1');
}

// ---------------------------------------------------------------------------
// Stretches and checkpoints: start a test where the stretch under test starts
// ---------------------------------------------------------------------------

type FlagSet = readonly [bank: number, index: number, on: boolean];

/** Where a stretch starts, and what a player who got there carries and has done. */
export interface Checkpoint {
  readonly room: { stage: number; room: number };
  readonly at: { x: number; z: number; angle: number };
  readonly flags: readonly FlagSet[];
  readonly items: readonly (readonly [id: number, qty: number])[];
}

// Flag banks: 1 FG_COMMON, 2 FG_LOCK, 3 FG_ENEMY (set = dead), 7 FG_ITEM (clear = taken).
const SEEN_RIDGE: FlagSet = [1, OPENING, true];
const SEEN_YARD: FlagSet = [1, 202, true];
const SEEN_CABIN: FlagSet = [1, 201, true];
const SEEN_SHED: FlagSet = [1, 203, true];
const TOOK_SPRAY: FlagSet = [7, SPRAY_FLAG, false];
const TOOK_KEY: FlagSet = [7, KEY_FLAG, false];
const DOG_DEAD: FlagSet = [3, 200, true];
const SHED_OPEN: FlagSet = [2, 60, true];
const TOOK_CRANK: FlagSet = [7, CRANK_FLAG, false];
const PINE_MOVED: FlagSet = [1, 205, true];
const SMALL_KEY = 61;
const UP_TO_THE_CABIN = [SEEN_RIDGE, SEEN_YARD, SEEN_CABIN, TOOK_SPRAY, TOOK_KEY];
const UP_TO_THE_SHED = [...UP_TO_THE_CABIN, DOG_DEAD, SHED_OPEN, SEEN_SHED, TOOK_CRANK];

/** The day's stretches in order: each one's function and where it starts (none: a new game). */
export const STRETCHES: Record<string, { play: (run: Run) => Promise<void>; from?: Checkpoint }> = {
  ridge: { play: ridge },
  trail: { play: trail, from: { room: DAY.trail, at: { x: 3500, z: 1200, angle: 0xc00 }, flags: [SEEN_RIDGE], items: [] } },
  yard: { play: yard, from: { room: DAY.yard, at: { x: 5610, z: 4930, angle: 0xe00 }, flags: [SEEN_RIDGE], items: [] } },
  lookout: { play: lookout, from: { room: DAY.lookout, at: { x: 6715, z: 9180, angle: 0x400 }, flags: [SEEN_RIDGE, SEEN_YARD], items: [] } },
  dog: {
    play: dog,
    from: { room: DAY.yard, at: { x: 22015, z: 13515, angle: 0xc00 }, flags: UP_TO_THE_CABIN, items: [[FIRST_AID_SPRAY, 1], [SMALL_KEY, 1]] },
  },
  shed: {
    play: shed,
    from: { room: DAY.yard, at: { x: 12000, z: 13000, angle: 0x800 }, flags: [...UP_TO_THE_CABIN, DOG_DEAD], items: [[FIRST_AID_SPRAY, 1], [SMALL_KEY, 1]] },
  },
  winch: {
    play: winch,
    from: { room: DAY.yard, at: { x: 10880, z: 13090, angle: 0 }, flags: UP_TO_THE_SHED, items: [[FIRST_AID_SPRAY, 1], [SMALL_KEY, 1], [HEX_CRANK, 1]] },
  },
  bridge: {
    play: bridge,
    from: { room: DAY.bridge, at: { x: 10200, z: 6120, angle: 0xc00 }, flags: [...UP_TO_THE_SHED, PINE_MOVED], items: [[FIRST_AID_SPRAY, 1], [SMALL_KEY, 1]] },
  },
};

export const stretchNames = Object.keys(STRETCHES);

/** The game's launch arguments for a test starting at `stretch`: a new game, or straight into its room. */
export function bootFor(stretch: string): string {
  const from = STRETCHES[stretch]?.from;
  return from ? `--mode REB --boot rebecca:${from.room.stage}:${from.room.room}` : '--mode REB --boot rebecca';
}

/**
 * Make the game what it would be at `cp` after playing up to it: the flags,
 * her bag, then the room entered again so its scripts set it up for those
 * flags, and her on the spot.
 */
export async function reach(link: GameLink, cp: Checkpoint): Promise<GameState> {
  await settle(link);
  for (const [bank, index, on] of cp.flags) await link.setFlag(bank, index, on);
  const s = await link.state();
  for (const [id, qty] of cp.items) if (!s.items.some((it) => it.id === id)) await link.give(id, qty);
  await link.room(cp.room.stage, cp.room.room);
  await settle(link, (st) => inRoom(st, cp.room));
  await link.place(cp.at.x, cp.at.z, cp.at.angle);
  return settle(link, (st) => inRoom(st, cp.room));
}

/** Play the stretches from `first` to `last`, in order, starting at `first`'s checkpoint. */
export async function play(run: Run, first: string, last: string): Promise<void> {
  const i0 = stretchNames.indexOf(first);
  const i1 = stretchNames.indexOf(last);
  if (i0 < 0 || i1 < i0) throw new Error(`no stretches from ${first} to ${last}; the stretches are ${stretchNames.join(', ')}`);
  const from = STRETCHES[first]!.from;
  if (from) run.log(await reach(run.link, from), `checkpoint: the start of ${first}`);
  for (const name of stretchNames.slice(i0, i1 + 1)) await STRETCHES[name]!.play(run);
}
