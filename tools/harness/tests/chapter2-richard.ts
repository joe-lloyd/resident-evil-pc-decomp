// Chapter 2 played through: from the save room after the meeting with Chris,
// up the 1F left stairs to the 2F corridor where Richard lies poisoned
// (ROOM2010), back down for the serum on the save room shelf, and up again
// within three minutes to save him.
//
//   OVERLAY=<REB build folder> node tools/harness/tests/chapter2-richard.ts
// SERUM_FIRST=1 takes the serum before going up, so he is treated on sight.
import path from 'node:path';
import { open } from '../lab.ts';
import { faceTowards, fight, goTo, settle, useDoor, useFightBack, useRoomData } from '../flows.ts';
import { Key } from '../link.ts';
import { roomLabel, type GameState } from '../state.ts';
import { snapshot } from '../snapshot.ts';

const overlay = process.env.OVERLAY;
if (!overlay) throw new Error('set OVERLAY to the REB build folder');
const dataDirs = [path.join(overlay, 'REB'), process.env.RE1_DATA ?? '/tmp/re1-pc'];
useRoomData(dataDirs);
useFightBack();
const out = process.env.OUT ?? '/tmp/rae-tests';
const serumFirst = process.env.SERUM_FIRST === '1';

const SERUM = 66;
const FOUND = 0x80 + 4;
const TREATED = 0x80 + 5;
const DEAD = 0x80 + 6;
/** FG_COMMON (bank 1) flag 202: she saved Richard. Flags count from the top bit of each LE word. */
const savedFlag = (s: GameState) => {
  const b = s.banks[1];
  return ((new DataView(b.buffer, b.byteOffset, b.byteLength).getUint32((202 >> 5) * 4, true) >>> (31 - (202 & 31))) & 1) === 1;
};

type Door = { x: number; z: number; w: number; d: number };
type Leg = { stage: number; room: number; door: Door };
const up: Leg[] = [
  { stage: 0, room: 0x00, door: { x: 2700, z: 500, w: 1700, d: 1800 } },
  { stage: 0, room: 0x01, door: { x: 4700, z: 2500, w: 2605, d: 1300 } },
];
const down: Leg[] = [
  { stage: 1, room: 0x01, door: { x: 11345, z: 10300, w: 2605, d: 2500 } },
  { stage: 0, room: 0x01, door: { x: 7600, z: 7700, w: 2400, d: 1500 } },
];

const session = await open(Number(process.env.PORT ?? 7802), '--mode REB --boot rebecca:0:0');
const link = session.link;
const failures: string[] = [];
const started = Date.now();
const log = (s: GameState, what: string) =>
  console.log(`[${Math.round((Date.now() - started) / 1000)}s] ${roomLabel(s)} hp ${s.player.hp}/${s.player.maxHp} ${what}`);

async function walk(legs: Leg[]): Promise<GameState> {
  let s = await link.state();
  for (const leg of legs) {
    s = await settle(link, (st) => st.stage === leg.stage && st.room === leg.room);
    await fight(link);
    s = await useDoor(link, leg.door);
    log(s, 'through the door');
  }
  return settle(link);
}

/** Take the serum off the medicine shelf in the save room. */
async function takeSerum(): Promise<void> {
  await settle(link, (s) => s.stage === 0 && s.room === 0);
  await goTo(link, dataDirs, 6300, 7600, { radius: 300 });
  await faceTowards(link, 6300, 9000);
  for (let i = 0; i < 4; i++) {
    await link.tap(Key.action, 3);
    await link.frames(20);
    const s = await settle(link);
    if (s.items.some((it) => it.id === SERUM)) {
      log(s, 'took the serum');
      return;
    }
  }
  failures.push('could not take the serum from the shelf');
}

try {
  const first = await settle(link, (s) => s.stage === 0 && s.room === 0);
  log(first, 'in the save room after the meeting');
  if (serumFirst) await takeSerum();

  const found = link.waitFor((s) => s.messageId === FOUND, 'Richard found', 600_000);
  found.catch(() => undefined);
  await walk(up);
  const atRichard = await found.catch(() => undefined);
  if (!atRichard) failures.push('the scene with Richard never played');
  else console.log(`picture: ${await snapshot(link, out, 'ch2-00-richard')}`);

  if (!serumFirst) {
    await walk(down);
    await takeSerum();
    await walk(up);
  }
  const end = await link.waitFor((s) => s.messageId === TREATED || s.messageId === DEAD, 'Richard treated', 30_000).catch(() => undefined);
  await settle(link);
  const s = await link.state();
  console.log(`picture: ${await snapshot(link, out, 'ch2-99-richard-after')}`);
  if (!end) failures.push('neither the treatment nor his death played');
  else if (end.messageId === DEAD) failures.push('Richard died before the serum arrived');
  if (!savedFlag(s)) failures.push('FG_COMMON 202 (Richard saved) is not set');
  if (s.items.some((it) => it.id === SERUM)) failures.push('the serum is still in her bag');
  log(s, 'chapter 2 done');
  if (failures.length) {
    console.error(`FAIL\n  ${failures.join('\n  ')}`);
    process.exitCode = 1;
  } else {
    console.log('PASS');
  }
} finally {
  session.end();
}
