// Give Rebecca the knife, shotgun and Magnum, equip each with her Beretta
// from the menu, aim and fire, and save screenshots. The weapon art itself is
// built by tools/rebecca/arms.ts; this shows it in the game.
//
//   PORT=7811 node tools/harness/tests/weapons.ts [<outdir>]
//
// Needs the engine and the REB overlay deployed. Boots her into the ranger's
// cabin (stage 2, room 0x14). Exits 1 if a weapon will not equip.
import { open } from '../lab.ts';
import { Key } from '../link.ts';
import { settle } from '../flows.ts';
import { snapshot } from '../snapshot.ts';

const outDir = process.argv[2] ?? '/tmp/rebecca-weapons-game';
const ITEM = { knife: 0x01, beretta: 0x02, shotgun: 0x03, magnum: 0x05 } as const;

// The menu shows her slots two to a row and opens with the cursor on the
// first. Each weapon's slot is read from her case after the gives: what she
// starts with (day/gear.ts) decides where they land.
const weapons = [
  { name: 'knife', item: ITEM.knife },
  { name: 'beretta', item: ITEM.beretta },
  { name: 'shotgun', item: ITEM.shotgun },
  { name: 'magnum', item: ITEM.magnum },
] as const;

const session = await open(Number(process.env.PORT ?? 7811), '--mode REB --boot rebecca:2:20');
const link = session.link;
const failed: string[] = [];
try {
  await link.waitFor((s) => s.play, 'gameplay', 120_000);
  await settle(link);
  for (const [id, qty] of [[ITEM.knife, 1], [ITEM.shotgun, 7], [ITEM.magnum, 6]] as const) {
    if (!(await link.state()).items.some((it) => it.id === id)) await link.give(id, qty);
  }
  await link.frames(10);
  for (const w of weapons) {
    const slot = (await link.state()).items.findIndex((it) => it.id === w.item);
    if (slot < 0) {
      failed.push(`${w.name}: not in her case`);
      continue;
    }
    await link.tap(Key.menu, 3);
    await link.frames(50);
    for (let i = 0; i < slot >> 1; i++) {
      await link.tap(Key.down, 2);
      await link.frames(8);
    }
    if (slot & 1) {
      await link.tap(Key.right, 2);
      await link.frames(8);
    }
    // Confirm opens the weapon's menu, whose first choice equips it.
    await link.tap(Key.action, 3);
    await link.frames(25);
    await link.tap(Key.action, 3);
    await link.frames(40);
    for (let i = 0; i < 6; i++) {
      if ((await link.frames(20)).menuState === 0) break;
      await link.tap(Key.run, 3);
    }
    const s = await settle(link);
    const inHand = s.items[s.player.weapon - 1]?.id;
    if (inHand !== w.item) failed.push(`${w.name}: item ${inHand} in hand`);
    await snapshot(link, outDir, `${w.name}-1-stand`);
    await link.down(Key.aim);
    await link.frames(30);
    await snapshot(link, outDir, `${w.name}-2-aim`);
    await link.tap(Key.action, 2);
    await link.frames(4);
    await snapshot(link, outDir, `${w.name}-3-fire`);
    await link.release();
    await link.frames(40);
    console.log(`${inHand === w.item ? 'ok  ' : 'FAIL'}  ${w.name}`);
  }
} finally {
  session.end();
}
console.log(failed.length ? `failed: ${failed.join('; ')}` : 'every weapon equips, aims and fires');
process.exit(failed.length ? 1 : 0);
