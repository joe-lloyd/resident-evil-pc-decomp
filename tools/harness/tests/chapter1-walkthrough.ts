// The prologue and Chapter 1 played through, the way a player would: down the
// mountain trail, across the courtyard garden and in through the back of the
// mansion to the save room, fighting what is left
// on the way, until the meeting with Chris plays.
//
//   OVERLAY=<REB build folder> node tools/harness/tests/chapter1-walkthrough.ts
// OVERLAY is the folder tools/rebecca/build.ts wrote (it holds REB/), so the
// path planner sees the same room files as the game.
import path from 'node:path';
import { open } from '../lab.ts';
import { fight, settle, useDoor, useFightBack, useRoomData } from '../flows.ts';
import { roomLabel, type GameState } from '../state.ts';
import { snapshot } from '../snapshot.ts';

const overlay = process.env.OVERLAY;
if (!overlay) throw new Error('set OVERLAY to the REB build folder');
useRoomData([path.join(overlay, 'REB'), process.env.RE1_DATA ?? '/tmp/re1-pc']);
useFightBack();
const out = process.env.OUT ?? '/tmp/rae-tests';
const MEETING = 0x80 + 46;

type Door = { x: number; z: number; w: number; d: number };
const route: { name: string; stage: number; room: number; fight: boolean; door: Door }[] = [
  { name: 'mountain trail', stage: 2, room: 0x12, fight: false, door: { x: 1500, z: 15200, w: 4000, d: 2000 } },
  { name: 'courtyard garden', stage: 2, room: 0x00, fight: false, door: { x: 22300, z: 3200, w: 4700, d: 4100 } },
  { name: 'storeroom', stage: 0, room: 0x1b, fight: false, door: { x: 0, z: 5200, w: 2600, d: 2400 } },
  { name: 'roofed passage', stage: 0, room: 0x1a, fight: true, door: { x: 4700, z: 2700, w: 1800, d: 2300 } },
  { name: 'back passage', stage: 0, room: 0x0a, fight: true, door: { x: 10600, z: 5200, w: 2000, d: 1700 } },
  { name: '1F left stairs', stage: 0, room: 0x01, fight: false, door: { x: 7600, z: 7700, w: 2400, d: 1500 } },
];

// A plain REB dev boot starts where a new game does: the mountain trail.
const session = await open(Number(process.env.PORT ?? 7802), '--mode REB --boot rebecca');
const link = session.link;
const failures: string[] = [];
const started = Date.now();
const log = (s: GameState, what: string) =>
  console.log(`[${Math.round((Date.now() - started) / 1000)}s] ${roomLabel(s)} hp ${s.player.hp}/${s.player.maxHp} ${what}`);
try {
  for (const [i, step] of route.entries()) {
    const here = await settle(link, (s) => s.stage === step.stage && s.room === step.room);
    log(here, `in the ${step.name}`);
    await snapshot(link, out, `ch1-${String(i).padStart(2, '0')}-${step.name.replace(/\W+/g, '-')}`);
    if (step.fight) {
      const shots = await fight(link);
      log(await link.state(), `cleared the ${step.name} with ${shots} shots`);
    }
    const meeting = i === route.length - 1 ? link.waitFor((s) => s.messageId === MEETING, 'the meeting', 120_000) : undefined;
    meeting?.catch(() => undefined);
    const next = await useDoor(link, step.door).catch(async (err) => {
      const s = await link.state();
      console.log(`door failed at (${s.player.x}, ${s.player.z}) angle ${s.player.angle} msf ${s.msf.toString(16)} msg ${s.messageChoice.toString(16)}/${s.messageId}`);
      console.log(`picture: ${await snapshot(link, out, 'ch1-door-failed')}`);
      throw err;
    });
    log(next, 'through the door');
    if (next.player.hp <= 0) failures.push(`died in the ${step.name}`);
    if (meeting) {
      const met = await meeting.catch(() => undefined);
      if (!met) failures.push('the meeting with Chris never played');
      else console.log(`picture: ${await snapshot(link, out, 'ch1-99-meeting')}`);
    }
  }
  const end = await settle(link, (s) => s.stage === 0 && s.room === 0);
  log(end, 'chapter 1 complete');
  if (failures.length) {
    console.error(`FAIL\n  ${failures.join('\n  ')}`);
    process.exitCode = 1;
  } else {
    console.log('PASS');
  }
} finally {
  session.end();
}
