// Rebecca's mountain trail (stage 2, room 0x12), walked the way a player does.
//
//   node tools/harness/deploy.ts <branch>
//   RAE_CLI=<explorer>/scripts/cli.mjs node tools/rebecca/build.ts /tmp/re1-pc /tmp/rae-reb
//   (deployOverlay('/tmp/rae-reb/REB') from lab.ts copies the overlay over)
//   node tools/harness/tests/mountain-trail.ts
//
// Checks, in order: she stands near the top of the trail under camera 0; the
// west and east edges hold her inside X 2000-5000; walking down the trail cuts
// from camera 0 to camera 1 as she crosses Z 8000; the door at the bottom
// takes her to stage 2 room 0x14, the ranger's lookout. A picture is taken under
// each camera for a person to look at.
import path from 'node:path';
import { open } from '../lab.ts';
import { Key, type GameLink } from '../link.ts';
import { goTo, settle, useRoomData } from '../flows.ts';
import { roomLabel, type GameState } from '../state.ts';
import { snapshot } from '../snapshot.ts';

const TRAIL = { x0: 2000, x1: 5000, split: 8000 };
const FACING_PLUS_Z = 0xc00; // measured: the engine's angle 0xC00 points down +Z, 0x400 up the trail
const FACING_PLUS_X = 0x000;
const FACING_MINUS_X = 0x800;
/** The state line is read every few frames, and walking covers under 100 units a frame. */
const POLL_FRAMES = 3;
const OUT = process.env.OUT ?? '/tmp/rae-tests';

const failures: string[] = [];
const expect = (ok: boolean, what: string) => {
  if (!ok) failures.push(what);
};

const angleDiff = (from: number, to: number) => ((((to - from) & 0xfff) + 0x800) & 0xfff) - 0x800;

const session = await open(Number(process.env.PORT ?? 7801), '--mode REB --boot rebecca:2:18');
const link: GameLink = session.link;
/** Every state read while she walks, to check the edges against the whole run. */
const trace: GameState[] = [];

async function poll(): Promise<GameState> {
  const s = await link.frames(POLL_FRAMES);
  trace.push(s);
  return s;
}

/** Turn in place until she faces `target`, using whichever key the angle says is shorter. */
async function face(target: number): Promise<GameState> {
  let s = await link.state();
  // Which way does LEFT turn? Measure it rather than assume it.
  await link.down(Key.left);
  const before = s.player.angle;
  s = await link.frames(6);
  await link.release();
  const leftIs = Math.sign(angleDiff(before, s.player.angle));
  expect(leftIs !== 0, 'holding left did not turn her');
  for (let i = 0; i < 80; i++) {
    s = await link.state();
    const diff = angleDiff(s.player.angle, target);
    if (Math.abs(diff) <= 0x60) break;
    const key = Math.sign(diff) === leftIs ? Key.left : Key.right;
    await link.tap(key, Math.abs(diff) > 0x200 ? 6 : 2);
    await link.frames(1);
  }
  s = await link.state();
  console.log(`  facing 0x${(s.player.angle & 0xfff).toString(16)} (wanted 0x${target.toString(16)}), left turns ${leftIs > 0 ? 'up' : 'down'}`);
  return s;
}

/** Hold forward until `done` passes or `maxFrames` pass; returns the last state. */
async function walkUntil(done: (s: GameState) => boolean, maxFrames: number): Promise<GameState> {
  await link.down(Key.up);
  let s = await link.state();
  try {
    for (let frames = 0; frames < maxFrames && !done(s); frames += POLL_FRAMES) s = await poll();
  } finally {
    await link.release();
  }
  return link.state();
}

try {
  let s = await settle(link, (st) => st.stage === 2 && st.room === 0x12);
  // A dev boot stands her by a door into the room, which may be the lookout's
  // at the foot; walk to the top, where she arrives from the ridge.
  useRoomData([path.join(process.env.OVERLAY ?? '/tmp/rae-reb', 'REB'), process.env.RE1_DATA ?? '/tmp/re1-pc']);
  s = await goTo(link, [path.join(process.env.OVERLAY ?? '/tmp/rae-reb', 'REB'), process.env.RE1_DATA ?? '/tmp/re1-pc'], 3500, 1300, { radius: 200 });
  s = await face(FACING_PLUS_Z);
  console.log(`at the top: (${s.player.x}, ${s.player.z}) camera ${s.camera}`);
  expect(s.camera === 0, `at the top under camera ${s.camera}, expected 0`);
  console.log(`picture: ${await snapshot(link, OUT, 'mountain-trail-start-cam0')}`);

  // The edges: face each side and walk into it.
  for (const [name, angle] of [['west', FACING_MINUS_X], ['east', FACING_PLUS_X]] as const) {
    await face(angle);
    s = await walkUntil(() => false, 150);
    console.log(`${name} edge: X ${s.player.x} after walking into it`);
    if (name === 'west') expect(s.player.x < TRAIL.x0 + 500, `walking west she stopped at X ${s.player.x}, which is not at the edge`);
    else expect(s.player.x > TRAIL.x1 - 500, `walking east she stopped at X ${s.player.x}, which is not at the edge`);
  }
  const xs = trace.map((t) => t.player.x);
  const [minX, maxX] = [Math.min(...xs), Math.max(...xs)];
  console.log(`X stayed within ${minX}..${maxX} over ${trace.length} readings`);
  expect(minX >= TRAIL.x0 && maxX <= TRAIL.x1, `X ${minX}..${maxX} left the trail ${TRAIL.x0}..${TRAIL.x1}`);

  // Down the trail: the cut from camera 0 to camera 1 at Z 8000.
  await face(FACING_PLUS_Z);
  trace.length = 0;
  s = await walkUntil((st) => st.camera === 1 || st.room !== 0x12, 900);
  const crossing = trace.filter((t) => t.camera === 0).at(-1);
  console.log(`cut: camera ${s.camera} at Z ${s.player.z}; last reading under camera 0 at Z ${crossing?.player.z}`);
  expect(s.camera === 1, `no cut to camera 1 (camera ${s.camera}, Z ${s.player.z})`);
  // The cut happens in the frame she crosses: the last reading under camera 0 is
  // short of Z 8000 and the first reading under camera 1 is past it.
  expect(crossing !== undefined && crossing.player.z < TRAIL.split, `last reading under camera 0 was at Z ${crossing?.player.z}, expected under ${TRAIL.split}`);
  const cutReading = trace.find((t) => t.camera === 1);
  expect(cutReading !== undefined && cutReading.player.z >= TRAIL.split, `first reading under camera 1 was at Z ${cutReading?.player.z}, expected ${TRAIL.split} or more`);
  console.log(`picture: ${await snapshot(link, OUT, 'mountain-trail-cam1-top')}`);

  // Partway down the lower half, then to the door.
  s = await walkUntil((st) => st.player.z >= 12500 || st.room !== 0x12, 600);
  expect(s.camera === 1, `camera ${s.camera} at Z ${s.player.z}, expected 1`);
  console.log(`picture: ${await snapshot(link, OUT, 'mountain-trail-cam1-door')}`);

  s = await walkUntil((st) => st.room !== 0x12 || st.stage !== 2, 450);
  s = await settle(link, (st) => st.stage === 2 && st.room === 0x14, 30_000).catch(() => s);
  expect(s.stage === 2 && s.room === 0x14, `the door led to stage ${s.stage} room ${s.room}, expected the lookout, stage 2 room 0x14`);
  if (s.stage === 2 && s.room === 0x14) {
    expect(Math.abs(s.player.x - 6000) <= 600 && Math.abs(s.player.z - 7300) <= 600, `arrived at (${s.player.x}, ${s.player.z}), expected inside the lookout's door (6000, 7300)`);
    console.log(`picture: ${await snapshot(link, OUT, 'mountain-trail-lookout')}`);
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
