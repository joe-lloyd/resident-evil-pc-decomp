// Chapter 3 played through: in the bar, find the sheet music on the shelf,
// play "Moonlight Sonata" on the piano, and take the Gold Emblem that turns up.
//
//   OVERLAY=<REB build folder> node tools/harness/tests/chapter3-moonlight.ts
import path from 'node:path';
import { open } from '../lab.ts';
import { check, settle, useRoomData } from '../flows.ts';
import { roomLabel, type GameState } from '../state.ts';
import { snapshot } from '../snapshot.ts';

const overlay = process.env.OVERLAY;
if (!overlay) throw new Error('set OVERLAY to the REB build folder');
useRoomData([path.join(overlay, 'REB'), process.env.RE1_DATA ?? '/tmp/re1-pc']);
const out = process.env.OUT ?? '/tmp/rae-tests';

const GOLD_EMBLEM = 32;
const TITLE = 0x80 + 29;
const PLAYED = 0x80 + 31;
const SHEET = 0x80 + 32;
const NOTES = { x: 16900, z: 10000, w: 1000, d: 2500 };
const PIANO = { x: 10200, z: 7300, w: 600, d: 1500 };

const session = await open(Number(process.env.PORT ?? 7802), '--mode REB --boot rebecca:0:15');
const link = session.link;
const failures: string[] = [];
const started = Date.now();
const log = (s: GameState, what: string) =>
  console.log(`[${Math.round((Date.now() - started) / 1000)}s] ${roomLabel(s)} hp ${s.player.hp}/${s.player.maxHp} ${what}`);
const has = (s: GameState, id: number) => s.items.some((it) => it.id === id);

try {
  const title = link.waitFor((s) => s.messageId === TITLE, 'chapter title', 60_000);
  title.catch(() => undefined);
  const first = await settle(link, (s) => s.stage === 0 && s.room === 0x0f);
  if (!(await title.catch(() => undefined))) failures.push('the chapter title never showed');
  log(first, 'in the bar');

  const found = link.waitFor((st) => st.messageId === SHEET, 'the sheet music', 60_000);
  found.catch(() => undefined);
  let s = await check(link, NOTES);
  if (await found.catch(() => undefined)) log(s, 'found the sheet music');
  else failures.push('the sheet music was not found');

  const played = link.waitFor((st) => st.messageId === PLAYED, 'the piano', 60_000);
  played.catch(() => undefined);
  s = await check(link, PIANO);
  if (await played.catch(() => undefined)) {
    log(s, 'played the piano');
    console.log(`picture: ${await snapshot(link, out, 'ch3-00-piano')}`);
  } else failures.push('playing the piano never happened');

  for (let i = 0; i < 3 && !has(s, GOLD_EMBLEM); i++) s = await check(link, PIANO);
  if (has(s, GOLD_EMBLEM)) log(s, 'took the Gold Emblem');
  else failures.push('the Gold Emblem was not on the piano');

  if (failures.length) {
    console.error(`FAIL\n  ${failures.join('\n  ')}`);
    process.exitCode = 1;
  } else {
    console.log('PASS');
  }
} finally {
  session.end();
}
