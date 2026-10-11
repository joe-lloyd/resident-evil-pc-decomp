// Rebecca's day from the title screen, the way a player starts it: the
// shipped game's NEW GAME shows the character select, which deals her card
// with Chris's and Jill's when her day is installed. Turning the deck to hers
// and choosing her must switch
// to her mode, show her opening narration and start her on the ridge (stage 2
// room 0x13, which only her overlay has), near the edge, facing out over the
// valley.
import { open } from '../lab.ts';
import { Key } from '../link.ts';
import { settle } from '../flows.ts';
import { roomLabel } from '../state.ts';
import { snapshot } from '../snapshot.ts';

const CHAR_REBECCA = 3;
const NARRATION = 0x7f;
const OUT = process.env.OUT ?? '/tmp/rae-tests';

const session = await open(Number(process.env.PORT ?? 7801), '--mode OG');
const failures: string[] = [];
const expect = (ok: boolean, what: string) => {
  if (!ok) failures.push(what);
};
const link = session.link;
try {
  // Intro text, then the title screen.
  while (!(await link.frames(20)).title) await link.tap(Key.enter, 3);
  await link.frames(30);
  await link.tap(Key.action, 3); // NEW GAME, the title's first choice
  // The deck: Chris in front, Jill and Rebecca behind. Each RIGHT turns the
  // deck and brings the middle card forward.
  const SELECT_WAITING = 1;
  const front = (who: number) => (st: { selectState: number; selectFront: number }) => st.selectState === SELECT_WAITING && st.selectFront === who;
  const names = ['Chris', 'Jill', 'Rebecca'];
  let sel = await link.waitFor((st) => st.selectState === SELECT_WAITING, 'the character select', 60_000);
  expect(sel.selectFront === 0, `${names[sel.selectFront] ?? sel.selectFront} is in front, expected Chris`);
  console.log(`picture: ${await snapshot(link, OUT, 'reb-new-game-select')}`);
  for (const who of [1, 2]) {
    await link.tap(Key.right, 3);
    sel = await link.waitFor(front(who), `${names[who]} turned to the front`, 10_000).catch(() => sel);
    expect(sel.selectFront === who, `after a turn ${names[sel.selectFront] ?? sel.selectFront} is in front, expected ${names[who]}`);
  }
  console.log(`picture: ${await snapshot(link, OUT, 'reb-new-game-rebecca-card')}`);
  await link.tap(Key.action, 3); // choose her

  const narration = await link.waitFor((s) => s.messageId === NARRATION, 'her opening narration', 60_000).catch(() => undefined);
  expect(narration !== undefined, 'no opening narration (message 0x7f)');

  const s = await settle(link, (st) => st.stage === 2 && st.room === 0x13);
  console.log(`room ${roomLabel(s)} camera ${s.camera} player ${s.player.id} at (${s.player.x}, ${s.player.z}) facing 0x${(s.player.angle & 0xfff).toString(16)}`);
  expect(s.player.id === CHAR_REBECCA, `player ${s.player.id}, expected Rebecca`);
  expect(s.camera === 0, `camera ${s.camera}, expected 0`);
  expect(Math.abs(s.player.x - 7000) <= 100 && Math.abs(s.player.z - 8800) <= 100, `started at (${s.player.x}, ${s.player.z}), expected near (7000, 8800)`);
  console.log(`picture: ${await snapshot(link, OUT, 'reb-new-game')}`);

  if (failures.length) {
    console.error(`FAIL\n  ${failures.join('\n  ')}`);
    process.exitCode = 1;
  } else {
    console.log('PASS');
  }
} finally {
  session.end();
}
