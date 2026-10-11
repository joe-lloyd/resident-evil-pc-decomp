// Rebecca's day played the way a player would, one function per stretch of
// it; each starts where the one before ends. docs/REBECCA_DAY.md is the plan,
// tools/rebecca/day/ the rooms.
import { check, goTo, settle, useDoor } from './flows.ts';
import { Run, commonFlag, inRoom } from './scenario.ts';
import type { GameState } from './state.ts';

export const DAY = {
  trail: { stage: 2, room: 0x12 },
  ridge: { stage: 2, room: 0x13 },
  lookout: { stage: 2, room: 0x14 },
} as const;

const has = (s: GameState, id: number) => s.items.some((it) => it.id === id);
const FIRST_AID_SPRAY = 0x41;
const SMALL_KEY = 0x3d;

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

/** The mountain trail, top to bottom, through its door to the lookout. */
export async function trail(run: Run): Promise<void> {
  const s = await run.door({ x: 1500, z: 15200, w: 4000, d: 2000 }, DAY.lookout, 'into the ranger\'s lookout');
  run.log(s, 'at the lookout');
}

/** Inside the lookout: the radio, the First Aid Spray, the ranger's key, and out. */
export async function lookout(run: Run): Promise<void> {
  const { link } = run;
  let s = await settle(link, (st) => inRoom(st, DAY.lookout));
  // The script sets FG_COMMON 201 as it shows her first thought.
  if (!commonFlag(s, 201)) run.fail('her first thought in the lookout never showed');
  await run.picture('day-lookout-0');
  const radio = run.expectMessage(0x81, 'the radio', 60_000);
  s = await check(link, { x: 3600, z: 3000, w: 1100, d: 1100 });
  if (await radio()) run.log(s, 'listened to the radio');
  else run.fail('the radio said nothing');
  for (let i = 0; i < 3 && !has(s, FIRST_AID_SPRAY); i++) s = await check(link, { x: 5600, z: 5500, w: 1400, d: 1300 });
  if (has(s, FIRST_AID_SPRAY)) run.log(s, 'took the First Aid Spray');
  else run.fail('could not take the First Aid Spray from the table');
  for (let i = 0; i < 3 && !has(s, SMALL_KEY); i++) s = await check(link, { x: 4900, z: 3000, w: 900, d: 1200 });
  if (has(s, SMALL_KEY)) run.log(s, 'took the ranger\'s key');
  else run.fail('could not take the ranger\'s key from the desk');
  await run.picture('day-lookout-1');
  s = await useDoor(link, { x: 5400, z: 7600, w: 1200, d: 900 });
  run.log(s, 'out of the lookout');
}
