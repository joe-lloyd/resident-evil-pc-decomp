// Rebecca's scenario from the title screen, the way a player starts it:
// NEW GAME in REB mode must show her opening narration, start her in the
// scenario's start room, and run that room's REB script (a lab-coat zombie in
// ROOM102 for now), proving the overlay, the assembler and appended scripts.
import { open } from '../lab.ts';
import { Key } from '../link.ts';
import { settle } from '../flows.ts';
import { roomLabel } from '../state.ts';
import { snapshot } from '../snapshot.ts';

const CHAR_REBECCA = 3;
const NARRATION = 0x7f;
const ZOMBIE_WHITE_COAT = 0x00;

const session = await open(Number(process.env.PORT ?? 7801), '--mode REB');
const failures: string[] = [];
const expect = (ok: boolean, what: string) => {
  if (!ok) failures.push(what);
};
const link = session.link;
try {
  // Intro text, then the title screen.
  while (!(await link.frames(20)).title) await link.tap(Key.enter, 3);
  await link.frames(30);
  await link.tap(Key.action, 3); // PRESS START BUTTON
  await link.frames(45);
  await link.tap(Key.action, 3); // NEW GAME

  const narration = await link.waitFor((s) => s.messageId === NARRATION, 'her opening narration', 60_000).catch(() => undefined);
  expect(narration !== undefined, 'no opening narration (message 0x7f)');

  const s = await settle(link, (st) => st.stage === 0 && st.room === 2);
  console.log(`room ${roomLabel(s)} player ${s.player.id} hp ${s.player.hp}/${s.player.maxHp} enemies [${s.enemies.map((e) => e.type.toString(16)).join(', ')}]`);
  expect(s.player.id === CHAR_REBECCA, `player ${s.player.id}, expected Rebecca`);
  expect(s.enemies.some((e) => e.type === ZOMBIE_WHITE_COAT), 'the REB script for ROOM102 did not place its zombie');
  console.log(`picture: ${await snapshot(link, process.env.OUT ?? '/tmp/rae-tests', 'reb-new-game')}`);

  if (failures.length) {
    console.error(`FAIL\n  ${failures.join('\n  ')}`);
    process.exitCode = 1;
  } else {
    console.log('PASS');
  }
} finally {
  session.end();
}
