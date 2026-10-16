// Her weapons through the day (rebecca/day/gear.ts), in the game:
//   - a new game starts her with her Beretta in hand, a spare clip and her knife;
//   - the first time she wades into the flooded gallery the mine takes her
//     weapons, rounds and healing, two of a kind as well as one, and the gun
//     leaves her hands, but not her key items;
//   - at the crash she picks up Kevin's Beretta.
//
//   node tools/harness/tests/gear.ts
//
// Needs the engine and the overlay deployed (see mountain-trail.ts), in the
// Rebecca game folder: RE1_LAB_GAME_DIR='D:\Games\RE1-files' PORT=7811.
import { readFileSync } from 'node:fs';
import path from 'node:path';
import { open } from '../lab.ts';
import { Key } from '../link.ts';
import { faceTowards, headingTo, settle } from '../flows.ts';
import type { GameState } from '../state.ts';
import { dayRooms } from '../../rebecca/day/rooms.ts';
import { day, nearest, read, walkable } from './floor.ts';

const BERETTA = 0x02;
const CLIP = 0x0b;
const KNIFE = 0x01;
const SPRAY = 0x41;
const GREEN_HERB = 0x44;
const COG = 0x29; // the drive cog, one of her key items

const failures: string[] = [];
const expect = (ok: boolean, what: string) => {
  console.log(`${ok ? 'ok  ' : 'FAIL'}  ${what}`);
  if (!ok) failures.push(what);
};
const ids = (s: GameState) => s.items.map((it) => it.id).filter((id) => id !== 0);
const room = (slug: string) => dayRooms.find((r) => r.slug === slug)!;

/** Where a room's script lays down item `id`: its pickup model's position (item_aot_set's bytes 9-14). */
function lying(slug: string, id: number): { x: number; z: number } {
  const c = readFileSync(path.join(day, slug, 'room.c'), 'utf8');
  for (const m of c.matchAll(/item_aot_set\(([^)]*)\)/g)) {
    const a = m[1]!.replace(/\/\*.*?\*\//g, '').split(',').map((t) => Number(t.trim()));
    const word = (lo: number, hi: number) => ((a[lo]! | (a[hi]! << 8)) << 16) >> 16;
    if (a[5] === id) return { x: word(9, 10), z: word(13, 14) };
  }
  throw new Error(`${slug} lays down no item ${id}`);
}

const session = await open(Number(process.env.PORT ?? 7801), '--mode REB --boot rebecca:2:18');
const link = session.link;
try {
  await link.waitFor((s) => s.play, 'gameplay', 120_000);
  // Her opening narration holds room jumps until it closes.
  let s = await settle(link, () => true, 20_000);

  expect([BERETTA, CLIP, KNIFE].every((id) => ids(s).includes(id)), `she starts with her Beretta, a clip and her knife (has ${ids(s).join(', ')})`);
  expect(s.player.weapon !== 0, 'she starts with a gun in her hands');

  // Two sprays, in two slots: the mine takes both (remove_item takes one slot
  // at a time). With her knife, Beretta and clip that fills her six slots.
  for (const id of [SPRAY, SPRAY, COG]) await link.give(id, 1);
  const gallery = room('gallery');
  await link.room(gallery.stage, gallery.room);
  s = await settle(link, (st) => st.stage === gallery.stage && st.room === gallery.room, 30_000);
  expect(ids(s).join(',') === String(COG), `the gallery leaves her only her key item (has ${ids(s).join(', ')})`);
  expect(s.player.weapon === 0, 'and nothing in her hands');

  // Coming back does not take anything again.
  await link.give(GREEN_HERB, 1);
  await link.room(gallery.stage, gallery.room);
  s = await settle(link, (st) => st.stage === gallery.stage && st.room === gallery.room, 30_000);
  expect(ids(s).includes(GREEN_HERB), 'the second time in, the gallery takes nothing');

  const crash = room('crash');
  await link.room(crash.stage, crash.room);
  await settle(link, (st) => st.stage === crash.stage && st.room === crash.room, 30_000);
  const gun = lying('crash', BERETTA);
  // Stand a step from it, so the point she reaches with action falls on it.
  const cells = walkable(read('crash')!, []);
  const at = nearest(cells, gun.x, gun.z, ([x, z]) => Math.hypot(x - gun.x, z - gun.z) > 350 && Math.hypot(x - gun.x, z - gun.z) < 700) ?? [gun.x - 500, gun.z];
  await link.place(at[0], at[1], headingTo(at[0], at[1], gun.x, gun.z));
  await link.frames(6);
  await faceTowards(link, gun.x, gun.z);
  await link.tap(Key.action, 3);
  await link.frames(30);
  s = await settle(link, (st) => st.stage === crash.stage && st.room === crash.room, 30_000);
  expect(ids(s).includes(BERETTA), `Kevin's Beretta at the crash (has ${ids(s).join(', ')})`);
} finally {
  session.end();
}
console.log(failures.length ? `${failures.length} failed` : 'her weapons follow the plan');
process.exit(failures.length ? 1 : 0);
