// Saving on her day the way a player does, then loading it from the shipped
// game's title screen. In the cabin she takes the ink ribbons by the
// typewriter, puts the First Aid Spray in the item box and saves at the
// typewriter. The save file must say it is her day, in the cabin, with the
// spray in the box. Then a new launch in the shipped game's mode loads it
// from the title, and she must be back in the cabin as Rebecca, one ribbon
// spent.
//
//   OVERLAY=<REB build> PORT=7820 RE1_LAB_GAME_DIR='D:\Games\RE1-ch1' node tools/harness/tests/reb-save.ts
//
// It deletes slot 1 of that game folder's SAVE first, and saves there.
import path from 'node:path';
import { mkdirSync, readFileSync } from 'node:fs';
import { fetch, open, remove } from '../lab.ts';
import { Key, type GameLink } from '../link.ts';
import { approach, check, settle, useRoomData } from '../flows.ts';
import { roomLabel, screen, type GameState } from '../state.ts';
import { snapshot } from '../snapshot.ts';

const CABIN = { stage: 2, room: 0x14 };
// The zones the cabin's script sets (tools/rebecca/day/lookout/room.c).
const RIBBONS = { x: 11305, z: 3400, w: 595, d: 1020 };
const TYPEWRITER = { x: 10455, z: 3400, w: 850, d: 1020 };
const BOX = { x: 10285, z: 5525, w: 1530, d: 1615 };
const INK_RIBBON = 47;
/** The typewriter's message: "You can save your progress with this.", then the ribbon question. */
const TYPEWRITER_MESSAGE = 223;
const FIRST_AID_SPRAY = 65;
const CHAR_REBECCA = 3;
/** Save file offsets (src/game/BioCard.h, SaveLoadScreen.cpp). */
const SAVE = { stage: 0x200, room: 0x201, character: 0x22b, mode: 0x233, box: 0x2c4, boxSlots: 48 } as const;
const SAVE_MODE_REB = 0x80;

const port = Number(process.env.PORT ?? 7820);
const gameDir = process.env.RE1_LAB_GAME_DIR ?? 'D:\\Games\\RE1-decomp';
const overlay = process.env.OVERLAY;
if (!overlay) throw new Error('set OVERLAY to the REB build folder');
const OUT = process.env.OUT ?? '/tmp/rae-tests';
mkdirSync(OUT, { recursive: true });
useRoomData([path.join(overlay, 'REB'), process.env.RE1_DATA ?? '/tmp/re1-pc']);

const failures: string[] = [];
const expect = (ok: boolean, what: string) => {
  if (!ok) {
    console.log(`  FAILED: ${what}`);
    failures.push(what);
  }
};
const log = (s: GameState, what: string) =>
  console.log(`${roomLabel(s)} ${screen(s)} msg ${s.messageId} choice ${s.messageChoice} msf ${s.msf.toString(16)} items ${JSON.stringify(s.items.map((i) => [i.id, i.qty]))}: ${what}`);
const picture = async (link: GameLink, name: string) => console.log(`picture: ${await snapshot(link, OUT, name)}`);
const qty = (s: GameState, id: number) => s.items.find((i) => i.id === id)?.qty ?? 0;

// ---- Her day: the cabin.
const slot1 = `${gameDir}\\SAVE\\savedat1.dat`;
remove(slot1);
let session = await open(port, `--mode REB --boot rebecca:${CABIN.stage}:${CABIN.room}`);
try {
  let link = session.link;
  let s = await settle(link, (st) => st.stage === CABIN.stage && st.room === CABIN.room);
  if (qty(s, FIRST_AID_SPRAY) === 0) await link.give(FIRST_AID_SPRAY, 1);
  log(s, 'in the cabin');
  s = await approach(link, RIBBONS);
  await picture(link, 'reb-save-ribbons-on-the-table');
  for (let i = 0; i < 3 && qty(s, INK_RIBBON) === 0; i++) s = await check(link, RIBBONS);
  expect(qty(s, INK_RIBBON) === 3, `took ${qty(s, INK_RIBBON)} ink ribbons by the typewriter, expected 3`);
  log(s, 'took the ribbons');

  // The item box: its lid swings open, then the box screen, her bag on the right and the box's list on
  // the left. Pick the spray in her bag (slot 2, the second row), then the
  // box's empty row above its first item, and swap them.
  s = await approach(link, BOX);
  await picture(link, 'reb-save-box-shut');
  await link.tap(Key.action, 3);
  await link.frames(10);
  await picture(link, 'reb-save-box-lid'); // RE1's own lid swinging open
  s = await link.waitFor((st) => screen(st) === 'menu', 'the box screen', 20_000);
  await link.frames(30);
  await picture(link, 'reb-save-box');
  for (const key of [Key.down, Key.action, Key.up, Key.action]) {
    await link.tap(key, 3);
    await link.frames(20);
  }
  await picture(link, 'reb-save-box-spray');
  s = await settle(link);
  log(s, 'closed the box');
  expect(qty(s, FIRST_AID_SPRAY) === 0, 'the First Aid Spray is still in her bag after the box');

  // The typewriter: "You can save your progress with this.", then the ink
  // ribbon question, YES, and the save screen.
  s = await approach(link, TYPEWRITER);
  await link.tap(Key.action, 3);
  s = await link.waitFor((st) => st.messageId === TYPEWRITER_MESSAGE, 'the typewriter', 20_000);
  // Each page types itself out before the action key turns it: press every
  // two seconds, through the first page and YES, until the save screen.
  for (let i = 0; i < 6 && screen(s) !== 'other'; i++) {
    await link.frames(60);
    if (i === 1) await picture(link, 'reb-save-ribbon');
    await link.tap(Key.action, 3);
    s = await link.frames(20);
  }
  expect(screen(s) === 'other', 'the save screen never opened');
  await link.frames(30);
  await picture(link, 'reb-save-screen');
  await link.tap(Key.action, 3); // slot 1, empty: it saves at once, types the row out and returns
  await link.frames(60);
  await picture(link, 'reb-save-saved');
  s = await settle(link, (st) => st.stage === CABIN.stage && st.room === CABIN.room);
  log(s, 'back in the cabin');
  expect(qty(s, INK_RIBBON) === 2, `${qty(s, INK_RIBBON)} ink ribbons after saving, expected 2`);
  session.end();

  const file = path.join(OUT, 'reb-save-savedat1.dat');
  fetch(slot1, file);
  const save = readFileSync(file);
  const box = Array.from({ length: SAVE.boxSlots }, (_, i) => save[SAVE.box + i * 2]!);
  console.log(`save: stage ${save[SAVE.stage]} room 0x${save[SAVE.room]!.toString(16)} character ${save[SAVE.character]} mode 0x${save[SAVE.mode]!.toString(16)} box ${box.filter(Boolean).join(',')}`);
  expect((save[SAVE.mode]! & SAVE_MODE_REB) !== 0, 'the save does not say it is her day');
  expect(save[SAVE.stage] === CABIN.stage && save[SAVE.room] === CABIN.room, 'the save is not in the cabin');
  expect(save[SAVE.character] === CHAR_REBECCA, `the save is character ${save[SAVE.character]}, expected Rebecca`);
  expect(box.includes(FIRST_AID_SPRAY), 'the First Aid Spray is not in the box');

  // ---- The shipped game: LOAD GAME from the title.
  session = await open(port, '--mode OG');
  link = session.link;
  while (!(await link.frames(20)).title) await link.tap(Key.enter, 3);
  // The title fades in and takes no keys until it has. With a save on disk
  // its cursor starts on LOAD GAME (check_save_files_exist).
  await link.frames(150);
  await picture(link, 'reb-load-title');
  await link.tap(Key.action, 3); // LOAD GAME
  // The load screen fades in too: press for slot 1 until the game loads.
  for (let i = 0; i < 10 && !(s = await link.frames(60)).play; i++) {
    if (i === 2) await picture(link, 'reb-load-screen');
    await link.tap(Key.action, 3);
  }
  s = await settle(link, (st) => st.stage === CABIN.stage && st.room === CABIN.room, 120_000);
  log(s, 'loaded');
  await picture(link, 'reb-loaded');
  expect(s.player.id === CHAR_REBECCA, `loaded as player ${s.player.id}, expected Rebecca`);
  expect(qty(s, INK_RIBBON) === 2, `${qty(s, INK_RIBBON)} ink ribbons after loading, expected 2`);
} finally {
  session.end();
}
if (failures.length) {
  console.error(`FAIL\n  ${failures.join('\n  ')}`);
  process.exit(1);
}
console.log('PASS');
