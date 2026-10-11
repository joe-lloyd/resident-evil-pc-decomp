// Chapter 5 played through: in the power room under the lab, turn the
// elevator power on, go on to the room where Wesker waits, live through the
// confrontation and leave by the far door for Chapter 6.
//
//   OVERLAY=<REB build folder> node tools/harness/tests/chapter5-lab.ts
import path from 'node:path';
import { open } from '../lab.ts';
import { check, settle, useDoor, useRoomData } from '../flows.ts';
import { roomLabel, type GameState } from '../state.ts';
import { snapshot } from '../snapshot.ts';

const overlay = process.env.OVERLAY;
if (!overlay) throw new Error('set OVERLAY to the REB build folder');
useRoomData([path.join(overlay, 'REB'), process.env.RE1_DATA ?? '/tmp/re1-pc']);
const out = process.env.OUT ?? '/tmp/rae-tests';

const TITLE = 0x80 + 8;
const POWER_ON = 0x80 + 6;
const WESKER = 0x80 + 22;
const SWITCH = { x: 17700, z: 8300, w: 2100, d: 1600 };
const POWER_DOOR = { x: 11300, z: 15800, w: 3000, d: 2900 };
const FAR_DOOR = { x: 13500, z: 8500, w: 1800, d: 2900 };

const session = await open(Number(process.env.PORT ?? 7802), '--mode REB --boot rebecca:4:17');
const link = session.link;
const failures: string[] = [];
const started = Date.now();
const log = (s: GameState, what: string) =>
  console.log(`[${Math.round((Date.now() - started) / 1000)}s] ${roomLabel(s)} hp ${s.player.hp}/${s.player.maxHp} ${what}`);
const inRoom = (s: GameState, stage: number, room: number) => s.stage === stage && s.room === room;

try {
  const title = link.waitFor((s) => s.messageId === TITLE, 'chapter title', 60_000);
  title.catch(() => undefined);
  let s = await settle(link, (st) => inRoom(st, 4, 0x11));
  if (!(await title.catch(() => undefined))) failures.push('the chapter title never showed');
  log(s, 'in the power room');

  const power = link.waitFor((st) => st.messageId === POWER_ON, 'the power switch', 60_000);
  power.catch(() => undefined);
  s = await check(link, SWITCH);
  if (await power.catch(() => undefined)) log(s, 'turned the power on');
  else failures.push(`the power switch never answered (last message ${s.messageId})`);

  const wesker = link.waitFor((st) => st.messageId === WESKER, 'Wesker', 60_000);
  wesker.catch(() => undefined);
  s = await useDoor(link, POWER_DOOR);
  log(s, 'through the door');
  if (!inRoom(s, 4, 0x14)) failures.push(`expected Wesker's room (ROOM5140), got ${roomLabel(s)}`);
  if (await wesker.catch(() => undefined)) {
    console.log(`picture: ${await snapshot(link, out, 'ch5-00-wesker')}`);
    log(s, 'faced Wesker');
  } else failures.push('the confrontation with Wesker never played');
  await settle(link);

  s = await useDoor(link, FAR_DOOR);
  log(s, 'through the door');
  if (!inRoom(s, 5, 0x01)) failures.push(`expected the 1F left stairs (ROOM6010), got ${roomLabel(s)}`);

  if (failures.length) {
    console.error(`FAIL\n  ${failures.join('\n  ')}`);
    process.exitCode = 1;
  } else {
    console.log('PASS');
  }
} catch (err) {
  const s = await link.state();
  console.log(`failed at ${roomLabel(s)} (${s.player.x}, ${s.player.z}); picture: ${await snapshot(link, out, 'ch5-failed')}`);
  throw err;
} finally {
  session.end();
}
