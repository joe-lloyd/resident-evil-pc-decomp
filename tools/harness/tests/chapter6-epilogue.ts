// Chapter 6 and the epilogue played through: back on the 1F left stairs, deal
// with the Hunter, climb to the heliport, meet Chris, and the game ends:
// MSF2_DEATH_VARIANT set, no death screen, and the ending runs back to the
// title.
//
//   OVERLAY=<REB build folder> node tools/harness/tests/chapter6-epilogue.ts
import path from 'node:path';
import { open } from '../lab.ts';
import { fight, settle, useDoor, useFightBack, useRoomData } from '../flows.ts';
import { roomLabel, type GameState } from '../state.ts';
import { snapshot } from '../snapshot.ts';

const overlay = process.env.OVERLAY;
if (!overlay) throw new Error('set OVERLAY to the REB build folder');
useRoomData([path.join(overlay, 'REB'), process.env.RE1_DATA ?? '/tmp/re1-pc']);
useFightBack();
const out = process.env.OUT ?? '/tmp/rae-tests';

const TITLE = 0x80 + 12;
const EPILOGUE = 0x80 + 7;
const STAIRS = { x: 4700, z: 2500, w: 2605, d: 1300 };
const DEATH_VARIANT = 0x80000000;

const session = await open(Number(process.env.PORT ?? 7802), '--mode REB --boot rebecca:5:1');
const link = session.link;
const failures: string[] = [];
const started = Date.now();
const log = (s: GameState, what: string) =>
  console.log(`[${Math.round((Date.now() - started) / 1000)}s] ${roomLabel(s)} hp ${s.player.hp}/${s.player.maxHp} ${what}`);
const inRoom = (s: GameState, stage: number, room: number) => s.stage === stage && s.room === room;

try {
  const title = link.waitFor((s) => s.messageId === TITLE, 'chapter title', 60_000);
  title.catch(() => undefined);
  let s = await settle(link, (st) => inRoom(st, 5, 0x01));
  if (!(await title.catch(() => undefined))) failures.push('the chapter title never showed');
  log(s, `on the stairs, enemies ${JSON.stringify(s.enemies.map((e) => [e.type, e.hp]))}`);
  const shots = await fight(link);
  log(await link.state(), `cleared the stairs with ${shots} shots`);

  const epilogue = link.waitFor((st) => st.messageId === EPILOGUE, 'the epilogue', 90_000);
  epilogue.catch(() => undefined);
  s = await useDoor(link, STAIRS);
  log(s, 'up the stairs');
  if (!inRoom(s, 2, 0x03)) failures.push(`expected the heliport (ROOM3030), got ${roomLabel(s)}`);
  if (await epilogue.catch(() => undefined)) {
    console.log(`picture: ${await snapshot(link, out, 'ch6-00-heliport')}`);
    log(s, 'met Chris on the heliport');
  } else failures.push('the epilogue never played');

  // Close the scene; the script then ends the game.
  const ending = link.waitFor((st) => (st.msf2 & DEATH_VARIANT) !== 0, 'the ending', 60_000);
  ending.catch(() => undefined);
  await settle(link).catch(() => undefined);
  const ended = await ending.catch(() => undefined);
  if (!ended) failures.push('the game never set the ending (MSF2_DEATH_VARIANT)');
  else {
    log(ended, `ending begins, hp ${ended.player.hp}`);
    const back = await link.waitFor((st) => st.title !== 0, 'the title after the ending', 600_000).catch(() => undefined);
    if (back) log(back, 'back at the title after the ending');
    else failures.push('the ending never returned to the title');
  }

  if (failures.length) {
    console.error(`FAIL\n  ${failures.join('\n  ')}`);
    process.exitCode = 1;
  } else {
    console.log('PASS');
  }
} catch (err) {
  const s = await link.state();
  console.log(`failed at ${roomLabel(s)} (${s.player.x}, ${s.player.z}); picture: ${await snapshot(link, out, 'ch6-failed')}`);
  throw err;
} finally {
  session.end();
}
