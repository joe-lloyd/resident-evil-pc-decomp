// Her kit through the day, checked in the game. The gallery scare keeps
// every slot. At the narrow crawl turn she leaves all gear except her
// Beretta and its loaded rounds. Key items stay and a repeat removes nothing.
// Run with the Windows lab and the current overlay: node tools/harness/tests/gear.ts
import { open } from '../lab.ts';
import { settle } from '../flows.ts';
import type { GameState } from '../state.ts';
import { dayRooms } from '../../rebecca/day/rooms.ts';
import { GEAR } from '../../rebecca/day/gear.ts';
import { KEY_ITEMS } from '../../rebecca/items/items.ts';
import { CUT_FLAGS } from '../../rebecca/day/cutscenes.ts';
import { Bank } from '../state.ts';

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

const session = await open(Number(process.env.PORT ?? 7801), '--mode REB --boot rebecca:2:18');
const link = session.link;
try {
  await link.waitFor((s) => s.play, 'gameplay', 120_000);
  // Her opening narration holds room jumps until it closes.
  let s = await settle(link, () => true, 20_000);

  expect([BERETTA, CLIP, KNIFE].every((id) => ids(s).includes(id)), `she starts with her Beretta, a clip and her knife (has ${ids(s).join(', ')})`);
  expect(s.player.weapon !== 0, 'she starts with a gun in her hands');

  // Exact slot contents include repeated healing and a key item.
  const kit = [{ id: BERETTA, qty: 7 }, { id: CLIP, qty: 15 }, { id: KNIFE, qty: 0 },
    { id: SPRAY, qty: 1 }, { id: SPRAY, qty: 1 }, { id: COG, qty: 1 }];
  await link.unequip();
  for (const [i, it] of kit.entries()) await link.slot(i, it.id, it.qty);
  const gallery = room('gallery');
  await link.room(gallery.stage, gallery.room);
  s = await settle(link, (st) => st.stage === gallery.stage && st.room === gallery.room, 30_000);
  expect(JSON.stringify(s.items.map(({ id, qty }) => ({ id, qty }))) === JSON.stringify(kit), 'the gallery keeps every item and loaded round');

  // Try every removable id in every slot, including duplicate stacks.
  const crawl = room('crawl');
  for (const id of GEAR) {
    await link.room(crawl.stage, crawl.room);
    await settle(link, (st) => st.stage === crawl.stage && st.room === crawl.room, 30_000);
    await link.place(3740, 8840);
    await link.unequip();
    const keys = KEY_ITEMS.slice(0, 1).map((k) => k.id);
    await link.slot(0, BERETTA, 7);
    await link.slot(1, keys[0]!, 1);
    for (let i = 2; i < 6; i++) await link.slot(i, id, 3);
    await link.setFlag(Bank.common, CUT_FLAGS.get('cut-leave-gear')!, false);
    await link.place(12240, 6800);
    s = await settle(link, (st) => st.stage === crawl.stage && st.room === crawl.room, 40_000);
    expect(!ids(s).includes(id), `the crawl removes every copy of item ${id}`);
    expect(s.items.some((it) => it.id === BERETTA && it.qty === 7), 'the pistol keeps its seven loaded rounds');
    expect(ids(s).includes(keys[0]!), 'the key item stays');
  }
  await link.give(GREEN_HERB, 1);
  await link.place(12240, 6800);
  await link.frames(60);
  s = await link.state();
  expect(ids(s).includes(GREEN_HERB), 'crossing the turn again takes nothing');

} finally {
  session.end();
}
console.log(failures.length ? `${failures.length} failed` : 'her weapons follow the plan');
process.exit(failures.length ? 1 : 0);
