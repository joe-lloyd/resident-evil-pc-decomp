// Chapter 1's last beat: Rebecca walks from the 1F left stairs into the save
// room, where Chris is waiting. The meeting (room message 46, id 0x80 + 46)
// must play on her first entry, Chris must be there, and checking him must
// give his line (message 47).
import { open } from '../lab.ts';
import { Key } from '../link.ts';
import { faceTowards, settle, useDoor, walkTo } from '../flows.ts';
import { roomLabel } from '../state.ts';
import { snapshot } from '../snapshot.ts';

const MEETING = 0x80 + 46;
const CHRIS_LINE = 0x80 + 47;
const CHRIS = 32;
const out = process.env.OUT ?? '/tmp/rae-tests';

const session = await open(Number(process.env.PORT ?? 7802), '--mode REB --boot rebecca:0:1');
const link = session.link;
const failures: string[] = [];
const expect = (ok: boolean, what: string) => {
  if (!ok) failures.push(what);
};
try {
  const stairs = await settle(link, (s) => s.stage === 0 && s.room === 1);
  expect(stairs.enemies.every((e) => e.hp <= 0) || stairs.enemies.length === 0, `left stairs should be empty, found ${stairs.enemies.length} enemies`);

  // Door 0 of ROOM1010 leads to the save room.
  const meetingSeen = link.waitFor((s) => s.messageId === MEETING, 'the meeting message', 90_000);
  meetingSeen.catch(() => undefined);
  await useDoor(link, { x: 7600, z: 7700, w: 2400, d: 1500 });
  const met = await meetingSeen.catch(() => undefined);
  expect(met !== undefined, 'the meeting (message 46) never showed');
  if (met) console.log(`picture: ${await snapshot(link, out, 'ch1-meeting')}`);

  const room = await settle(link, (s) => s.stage === 0 && s.room === 0);
  console.log(`room ${roomLabel(room)} enemies [${room.enemies.map((e) => e.type).join(', ')}]`);
  const chris = room.enemies.find((e) => e.type === CHRIS);
  expect(chris !== undefined, 'Chris is not in the save room');

  if (chris) {
    // Stand in front of him, face him and check.
    await walkTo(link, chris.x, chris.z + 900, { radius: 350 }).catch((err) => {
      console.log(`walk failed: ${String(err)}`);
      return link.state();
    });
    const facing = await faceTowards(link, chris.x, chris.z);
    console.log(`checking Chris from (${facing.player.x}, ${facing.player.z}) angle ${facing.player.angle}; Chris at (${chris.x}, ${chris.z})`);
    await link.tap(Key.action, 3);
    const line = await link.waitFor((s) => s.messageId === CHRIS_LINE, "Chris's line", 10_000).catch(() => undefined);
    expect(line !== undefined, "checking Chris did not give his line (message 47)");
    if (line) console.log(`picture: ${await snapshot(link, out, 'ch1-chris-line')}`);
  }

  if (failures.length) {
    console.error(`FAIL\n  ${failures.join('\n  ')}`);
    process.exitCode = 1;
  } else {
    console.log('PASS');
  }
} finally {
  session.end();
}
