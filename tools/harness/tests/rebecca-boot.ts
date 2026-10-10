// A new game as Rebecca (--boot rebecca) must give her own character, health
// and starting items, and leave her in control in the room asked for.
import { open } from '../lab.ts';
import { inControl } from '../flows.ts';
import { roomLabel } from '../state.ts';

const CHAR_REBECCA = 3;
const ITEM_BERETTA = 0x02;
const ITEM_FIRST_AID_SPRAY = 0x41;
const ITEM_GREEN_HERB = 0x44;

const session = await open(Number(process.env.PORT ?? 7801), '--boot rebecca:0:0');
const failures: string[] = [];
const expect = (ok: boolean, what: string) => {
  if (!ok) failures.push(what);
};
try {
  const s = await session.link.waitFor((st) => st.stage === 0 && st.room === 0 && inControl(st), 'control in ROOM100', 120_000);
  console.log(`room ${roomLabel(s)} player ${s.player.id} hp ${s.player.hp}/${s.player.maxHp} items ${JSON.stringify(s.items)}`);
  expect(s.player.id === CHAR_REBECCA, `player id ${s.player.id}, expected ${CHAR_REBECCA}`);
  expect(s.charModel === CHAR_REBECCA, `character model ${s.charModel}, expected ${CHAR_REBECCA}`);
  expect(s.player.hp === 88 && s.player.maxHp === 88, `health ${s.player.hp}/${s.player.maxHp}, expected 88/88`);
  expect(s.items.length === 6, `${s.items.length} item slots, expected 6`);
  const held = s.items.filter((i) => i.id !== 0);
  expect(
    JSON.stringify(held) ===
      JSON.stringify([
        { id: ITEM_BERETTA, qty: 15 },
        { id: ITEM_FIRST_AID_SPRAY, qty: 1 },
        { id: ITEM_GREEN_HERB, qty: 1 },
      ]),
    `items ${JSON.stringify(held)}`,
  );

  // She has to be able to move: hold forward and check the position changes.
  await session.link.down(0x26);
  const moved = await session.link.waitFor(
    (st) => Math.abs(st.player.x - s.player.x) + Math.abs(st.player.z - s.player.z) > 200,
    'Rebecca to walk',
    10_000,
  ).catch(() => undefined);
  await session.link.release();
  expect(moved !== undefined, 'she did not move when walking forward');
  await session.link.shot('C:\\Users\\joell\\Tools\\wintool\\rebecca-boot.bmp');

  if (failures.length) {
    console.error(`FAIL\n  ${failures.join('\n  ')}`);
    process.exitCode = 1;
  } else {
    console.log('PASS');
  }
} finally {
  session.end();
}
