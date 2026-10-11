// Chapter 4 played through: in the guardhouse, mix V-JOLT in the drug
// storehouse, pour it on Plant 42's roots, take the Helmet Key from beside the
// dead plant and go on to the lab.
//
//   OVERLAY=<REB build folder> node tools/harness/tests/chapter4-guardhouse.ts
import path from 'node:path';
import { open } from '../lab.ts';
import { check, settle, useDoor, useRoomData } from '../flows.ts';
import { roomLabel, type GameState } from '../state.ts';
import { snapshot } from '../snapshot.ts';

const overlay = process.env.OVERLAY;
if (!overlay) throw new Error('set OVERLAY to the REB build folder');
useRoomData([path.join(overlay, 'REB'), process.env.RE1_DATA ?? '/tmp/re1-pc']);
const out = process.env.OUT ?? '/tmp/rae-tests';

const VJOLT = 27;
const HELMET_KEY = 54;
const TITLE = 0x80 + 16;
const POURED = 0x80 + 18;
const HUB = { stage: 3, room: 0x08 };
const STOREHOUSE_DOOR = { x: 5500, z: 9400, w: 3000, d: 1800 };
const TABLE = { x: 5100, z: 6000, w: 4400, d: 1100 };
const STOREHOUSE_EXIT = { x: 9600, z: 2300, w: 1800, d: 1700 };
const ROOTS = { x: 24200, z: 2400, w: 2600, d: 3400 };
const PLANT_DOOR = { x: 27800, z: 2100, w: 3000, d: 4000 };
const HELMET = { x: 9800, z: 17700, w: 2200, d: 1800 };
const PLANT_EXIT = { x: 1100, z: 8000, w: 1500, d: 3900 };

const session = await open(Number(process.env.PORT ?? 7802), '--mode REB --boot rebecca:3:8');
const link = session.link;
const failures: string[] = [];
const started = Date.now();
const log = (s: GameState, what: string) =>
  console.log(`[${Math.round((Date.now() - started) / 1000)}s] ${roomLabel(s)} hp ${s.player.hp}/${s.player.maxHp} ${what}`);
const has = (s: GameState, id: number) => s.items.some((it) => it.id === id);
const inRoom = (s: GameState, stage: number, room: number) => s.stage === stage && s.room === room;

try {
  const title = link.waitFor((s) => s.messageId === TITLE, 'chapter title', 60_000);
  title.catch(() => undefined);
  let s = await settle(link, (st) => inRoom(st, HUB.stage, HUB.room));
  if (!(await title.catch(() => undefined))) failures.push('the chapter title never showed');
  log(s, 'in the guardhouse passage');

  s = await useDoor(link, STOREHOUSE_DOOR);
  log(s, 'in the drug storehouse');
  s = await check(link, TABLE);
  for (let i = 0; i < 3 && !has(s, VJOLT); i++) s = await check(link, TABLE);
  if (has(s, VJOLT)) log(s, 'mixed and took the V-JOLT');
  else failures.push('no V-JOLT from the mixing table');
  console.log(`picture: ${await snapshot(link, out, 'ch4-00-storehouse')}`);

  s = await useDoor(link, STOREHOUSE_EXIT);
  const poured = link.waitFor((st) => st.messageId === POURED, 'the roots', 60_000);
  poured.catch(() => undefined);
  s = await check(link, ROOTS);
  if (await poured.catch(() => undefined)) log(s, 'poured the V-JOLT on the roots');
  else failures.push(`the roots never took the V-JOLT (last message ${s.messageId}, at ${s.player.x}, ${s.player.z})`);

  s = await useDoor(link, PLANT_DOOR);
  log(s, `in Plant 42's room, enemies ${JSON.stringify(s.enemies.map((e) => [e.type, e.hp]))}`);
  console.log(`picture: ${await snapshot(link, out, 'ch4-01-plant42')}`);
  for (let i = 0; i < 3 && !has(s, HELMET_KEY); i++) s = await check(link, HELMET);
  if (has(s, HELMET_KEY)) log(s, 'took the Helmet Key');
  else failures.push('could not take the Helmet Key');

  s = await useDoor(link, PLANT_EXIT);
  log(s, 'through the door');
  if (!inRoom(s, 4, 0x11)) failures.push(`expected the lab (ROOM5110), got ${roomLabel(s)}`);

  if (failures.length) {
    console.error(`FAIL\n  ${failures.join('\n  ')}`);
    process.exitCode = 1;
  } else {
    console.log('PASS');
  }
} catch (err) {
  const s = await link.state();
  console.log(`failed at ${roomLabel(s)} (${s.player.x}, ${s.player.z}) angle ${s.player.angle}; picture: ${await snapshot(link, out, 'ch4-failed')}`);
  throw err;
} finally {
  session.end();
}
