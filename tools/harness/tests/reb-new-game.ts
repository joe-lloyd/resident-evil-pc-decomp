// Rebecca's scenario from the title screen, the way a player starts it:
// NEW GAME in REB mode must show her opening narration and start her on the
// ridge (stage 2 room 0x13), near the edge, facing out over the valley. That
// proves the overlay, the card's start room and spot, and the new room itself.
import { open } from '../lab.ts';
import { Key } from '../link.ts';
import { settle } from '../flows.ts';
import { roomLabel } from '../state.ts';
import { snapshot } from '../snapshot.ts';

const CHAR_REBECCA = 3;
const NARRATION = 0x7f;

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

  const s = await settle(link, (st) => st.stage === 2 && st.room === 0x13);
  console.log(`room ${roomLabel(s)} camera ${s.camera} player ${s.player.id} at (${s.player.x}, ${s.player.z}) facing 0x${(s.player.angle & 0xfff).toString(16)}`);
  expect(s.player.id === CHAR_REBECCA, `player ${s.player.id}, expected Rebecca`);
  expect(s.camera === 0, `camera ${s.camera}, expected 0`);
  expect(Math.abs(s.player.x - 7000) <= 100 && Math.abs(s.player.z - 8800) <= 100, `started at (${s.player.x}, ${s.player.z}), expected near (7000, 8800)`);
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
