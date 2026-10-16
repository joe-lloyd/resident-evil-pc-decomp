// Every save room of her day works: in each, the item box's lid swings open
// onto the box screen and the typewriter offers to save. The zones are the ones each
// scene records (day/<slug>/renders/room.json, `saves`), which day/scripts.ts
// writes into the room's script. reb-save.ts plays a whole save and load in
// the cabin; this checks the rest.
//
//   OVERLAY=<REB build> PORT=7820 RE1_LAB_GAME_DIR='D:\Games\RE1-ch1' node tools/harness/tests/reb-save-rooms.ts [slug...]
import path from 'node:path';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { open } from '../lab.ts';
import { Key } from '../link.ts';
import { approach, settle, useRoomData } from '../flows.ts';
import { roomLabel, screen } from '../state.ts';
import { snapshot } from '../snapshot.ts';
import { dayRooms } from '../../rebecca/day/rooms.ts';

const INK_RIBBON = 47;
/** "You can save your progress with this.", then the ribbon question. */
const TYPEWRITER_MESSAGE = 223;
const ROOMS = ['office', 'booth', 'mine-office', 'lodge'];

type Rect = { x0: number; z0: number; x1: number; z1: number };
const zone = (r: Rect) => ({ x: r.x0, z: r.z0, w: r.x1 - r.x0, d: r.z1 - r.z0 });
const here = path.dirname(fileURLToPath(import.meta.url));

const overlay = process.env.OVERLAY;
if (!overlay) throw new Error('set OVERLAY to the REB build folder');
const OUT = process.env.OUT ?? '/tmp/rae-tests';
const port = Number(process.env.PORT ?? 7820);
useRoomData([path.join(overlay, 'REB'), process.env.RE1_DATA ?? '/tmp/re1-pc']);

const failures: string[] = [];
for (const slug of process.argv.slice(2).length ? process.argv.slice(2) : ROOMS) {
  const room = dayRooms.find((r) => r.slug === slug);
  if (!room) throw new Error(`no room ${slug}`);
  const json = JSON.parse(readFileSync(path.join(here, '..', '..', 'rebecca', 'day', slug, 'renders', 'room.json'), 'utf8')) as { saves?: { typewriter: Rect; box: Rect } };
  if (!json.saves) {
    failures.push(`${slug}: its scene records no typewriter or box`);
    continue;
  }
  const inRoom = (s: { stage: number; room: number }) => s.stage === room.stage && s.room === room.room;
  const session = await open(port, `--mode REB --boot rebecca:${room.stage}:${room.room}`);
  try {
    const link = session.link;
    let s = await settle(link, inRoom);
    await link.give(INK_RIBBON, 1);

    s = await approach(link, zone(json.saves.box));
    console.log(`picture: ${await snapshot(link, OUT, `reb-save-${slug}-box-shut`)}`);
    await link.tap(Key.action, 3);
    await link.frames(10);
    console.log(`picture: ${await snapshot(link, OUT, `reb-save-${slug}-box-lid`)}`);
    const box = await link.waitFor((st) => screen(st) === 'menu', 'the box screen', 15_000).catch(() => undefined);
    if (!box) failures.push(`${slug}: the chest did not open the item box`);
    s = await settle(link, inRoom);

    s = await approach(link, zone(json.saves.typewriter));
    console.log(`at the typewriter: (${s.player.x}, ${s.player.z}) facing ${s.player.angle & 0xfff}`);
    await link.tap(Key.action, 3);
    const typed = await link.waitFor((st) => st.messageId === TYPEWRITER_MESSAGE, 'the typewriter', 15_000).catch(() => undefined);
    await link.frames(40);
    console.log(`picture: ${await snapshot(link, OUT, `reb-save-${slug}-typewriter`)}`);
    if (!typed) failures.push(`${slug}: the typewriter did not offer to save`);
    console.log(`${slug} (${roomLabel(s)}): box ${box ? 'opened' : 'NO'}, typewriter ${typed ? 'offered to save' : 'NO'}`);
  } finally {
    session.end();
  }
}
if (failures.length) {
  console.error(`FAIL\n  ${failures.join('\n  ')}`);
  process.exit(1);
}
console.log('PASS');
