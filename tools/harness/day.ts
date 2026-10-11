// Rebecca's day played the way a player would, one function per stretch of
// it; each starts where the one before ends. docs/REBECCA_DAY.md is the plan,
// tools/rebecca/day/ the rooms. Zones are the ones the rooms' scripts set
// (game units, metres * 1700 in the new rooms).
import { check, fight, goTo, settle, useDoor, useItem } from './flows.ts';
import { Run, commonFlag, inRoom } from './scenario.ts';
import type { GameState } from './state.ts';

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
const KEY_FLAG = 242;
const CRANK_FLAG = 243;
const HEX_CRANK = 30;
const FIRST_AID_SPRAY = 65;
const CERBERUS = 2;

const YARD = {
  pine: { x: 24310, z: 19380, w: 4930, d: 1360 },
  winch: { x: 19210, z: 17170, w: 1700, d: 2380 },
  cabin: { x: 21080, z: 12325, w: 1870, d: 1020 },
  shed: { x: 9180, z: 12410, w: 1190, d: 1360 },
};
const CABIN = {
  door: { x: 5950, z: 9100, w: 1530, d: 1100 },
  radio: { x: 4335, z: 4675, w: 850, d: 935 },
  logbook: { x: 5440, z: 4675, w: 1020, d: 935 },
  spray: { x: 6120, z: 6630, w: 1700, d: 1700 },
  key: { x: 4930, z: 9095, w: 935, d: 1105 },
};
const SHED = {
  door: { x: 5100, z: 2890, w: 1020, d: 1360 },
  crank: { x: 2805, z: 3145, w: 1105, d: 1360 },
};
const BRIDGE = {
  sign: { x: 5950, z: 32640, w: 8500, d: 1360 },
};

/** Check a zone until `done` holds, a few tries; returns the last state. */
async function checkUntil(run: Run, zone: { x: number; z: number; w: number; d: number }, done: (s: GameState) => boolean): Promise<GameState> {
  let s = await run.link.state();
  for (let i = 0; i < 3 && !done(s); i++) s = await check(run.link, zone);
  return s;
}

/** The ridge: the opening monologue, then the path east down to the trail. */
export async function ridge(run: Run): Promise<void> {
  const { link } = run;
  const opening = run.expectMessage(0x80, 'the opening', 60_000);
  let s = await settle(link, (st) => inRoom(st, DAY.ridge));
  if (!(await opening())) run.fail('the opening monologue never showed');
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
  const logbook = run.expectMessage(0x82, 'the logbook', 60_000);
  s = await check(link, CABIN.logbook);
  if (await logbook()) run.log(s, 'read the logbook: the crank is in the shed');
  else run.fail('the logbook said nothing');
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
  if (s.items.some((it) => it.id === HEX_CRANK)) run.fail('the crank is still in her bag');
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
  s = await goTo(link, run.dataDirs, 10200, 19500, { radius: 500 });
  run.log(s, 'on the bridge');
  await run.picture('day-bridge-mid');
  s = await check(link, BRIDGE.sign);
  if (commonFlag(s, 206)) run.log(s, 'across the gorge: the valley trail sign');
  else run.fail('could not read the valley trail sign');
  await run.picture('day-bridge-1');
}

/** Act 1 from the ridge to the far side of the gorge. */
export async function act1(run: Run): Promise<void> {
  await ridge(run);
  await trail(run);
  await yard(run);
  await lookout(run);
  await dog(run);
  await shed(run);
  await winch(run);
  await bridge(run);
}
