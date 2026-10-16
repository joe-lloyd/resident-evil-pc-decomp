// Her key items with models of their own (rebecca/items/models.py), in the
// game, as pictures for a person to look at:
//   - each lying in its room (the TMD tmd.ts writes into the room), seen
//     from a few steps away under whichever camera shows her there;
//   - her case with them all in it (their icons, items/sheet.ts);
//   - each checked in her case, the model she turns over (ITEM_M2).
// Fails if an item is in no room's script, or nothing is drawn in the model
// window when it is checked. That the right item was checked shows in the
// picture: its name is under the window.
//
//   node tools/harness/tests/items.ts
//
// Needs the engine and the overlay deployed (see mountain-trail.ts), in the
// Rebecca game folder: RE1_LAB_GAME_DIR='D:\Games\RE1-files' PORT=7811.
import { readFileSync } from 'node:fs';
import path from 'node:path';
import { open } from '../lab.ts';
import { Key, type GameLink } from '../link.ts';
import { faceTowards, headingTo, settle } from '../flows.ts';
import { Bank } from '../state.ts';
import { snapshot } from '../snapshot.ts';
import { readPng } from '../image.ts';
import { dayRooms } from '../../rebecca/day/rooms.ts';
import { EVENT_FLAGS, EVENTS, GIVE_FLAGS } from '../../rebecca/day/events.ts';
import { KEY_ITEMS } from '../../rebecca/items/items.ts';
import { day, nearest, read, walkable } from './floor.ts';

const OUT = process.env.OUT ?? '/tmp/rae-tests/items';
const own = KEY_ITEMS.filter((k) => 'own' in k.model);

/** Where a room's script lays an item down: its pickup model's position (item_aot_set's bytes 9-14). */
function lying(id: number): { slug: string; x: number; y: number; z: number } | undefined {
  for (const r of dayRooms) {
    let c: string;
    try {
      c = readFileSync(path.join(day, r.slug, 'room.c'), 'utf8');
    } catch {
      continue;
    }
    for (const m of c.matchAll(/item_aot_set\(([^)]*)\)/g)) {
      const a = m[1]!.replace(/\/\*.*?\*\//g, '').split(',').map((t) => Number(t.trim()));
      if (a[5] !== id) continue;
      const word = (lo: number, hi: number) => ((a[lo]! | (a[hi]! << 8)) << 16) >> 16;
      return { slug: r.slug, x: word(9, 10), y: word(11, 12), z: word(13, 14) };
    }
  }
  return undefined;
}

const failures: string[] = [];
const boot = '--mode REB --boot rebecca:2:18';
const port = Number(process.env.PORT ?? 7801);

/** Start a game and wait out her opening narration, which holds room jumps until it closes. */
async function start() {
  const session = await open(port, boot);
  await session.link.waitFor((s) => s.play, 'gameplay', 120_000);
  await settle(session.link, () => true, 20_000).catch(() => undefined);
  return session;
}

/** Take a picture of each item lying in its room. */
async function lyingPictures(link: GameLink) {
  for (const k of own) {
    const at = lying(k.id);
    if (!at) {
      failures.push(`${k.step}: no room lays it down`);
      continue;
    }
    const room = dayRooms.find((r) => r.slug === at.slug)!;
    // What an event leaves is there once the event has happened.
    const gift = EVENTS.find((e) => e.gives === k.step);
    if (gift) {
      await link.setFlag(Bank.common, EVENT_FLAGS.get(gift.step)!, true);
      await link.setFlag(Bank.roomItems, GIVE_FLAGS.get(k.step)!, false);
    }
    await link.room(room.stage, room.room);
    await settle(link, () => true, 20_000).catch(() => undefined);
    const json = read(at.slug);
    const cells = json ? walkable(json, []) : [];
    const stand = nearest(cells, at.x, at.z, ([x, z]) => Math.hypot(x - at.x, z - at.z) > 1400) ?? [at.x - 1500, at.z];
    await link.place(stand[0], stand[1], headingTo(stand[0], stand[1], at.x, at.z));
    await link.frames(10);
    await faceTowards(link, at.x, at.z);
    await link.frames(20);
    console.log(`${k.step} lying in ${at.slug}: ${await snapshot(link, OUT, `${k.step}-lying`)}`);
  }
}

/** Put `batch` in her case, picture the case, then check each one and picture the model. */
async function checkPictures(link: GameLink, batch: typeof own, n: number) {
  for (const k of batch) await link.give(k.id, 1);
  for (const k of batch) {
    const slot = (await link.state()).items.findIndex((it) => it.id === k.id);
    await link.tap(Key.menu, 3);
    await link.waitFor((st) => st.menuState === 1, 'the status screen', 15_000);
    // Presses while the screen is still sliding in are dropped, and leave the cursor a slot short.
    await link.frames(70);
    if (k === batch[0]) console.log(`her case: ${await snapshot(link, OUT, `case-${n}`)}`);
    for (let row = 0; row < slot >> 1; row++) {
      await link.tap(Key.down, 3);
      await link.frames(14);
    }
    if (slot & 1) {
      await link.tap(Key.right, 3);
      await link.frames(14);
    }
    await link.tap(Key.action, 3); // the item's menu: USE, CHECK, COMBINE
    await link.frames(15);
    await link.tap(Key.down, 3);
    await link.frames(8);
    await link.tap(Key.action, 3); // CHECK
    // The model zooms and turns in before it settles facing her.
    await link.frames(150);
    const shot = await snapshot(link, OUT, `${k.step}-checked`);
    // The model window is black until a model is drawn in it.
    const img = readPng(shot);
    let lit = 0;
    for (let y = 60; y < 190; y++) for (let x = 70; x < 280; x++) if (Math.max(...img.rgb.subarray((y * img.width + x) * 3, (y * img.width + x) * 3 + 3)) > 40) lit++;
    if (lit < 200) failures.push(`${k.step}: nothing drawn in the model window`);
    console.log(`${k.step} checked: ${shot}`);
    for (let i = 0; i < 4; i++) {
      await link.tap(Key.run, 3); // back out
      await link.frames(20);
    }
    await settle(link, () => true, 20_000).catch(() => undefined);
  }
}

let session = await start();
try {
  await lyingPictures(session.link);
  // Her case holds six; a fresh game for each handful that fits beside what she starts with.
  const queue = [...own];
  for (let n = 0; queue.length; n++) {
    if (n) {
      session.end();
      // The game holds a lock on its folder until it has quit.
      await new Promise((r) => setTimeout(r, 8000));
      session = await start();
    }
    const free = 6 - (await session.link.state()).items.filter((it) => it.id !== 0).length;
    if (free < 1) throw new Error('her case is full at the start');
    await checkPictures(session.link, queue.splice(0, free), n);
  }
} finally {
  session.end();
}
for (const f of failures) console.log(`FAIL  ${f}`);
console.log(failures.length ? `${failures.length} failed` : 'every item has its pictures');
process.exit(failures.length ? 1 : 0);
