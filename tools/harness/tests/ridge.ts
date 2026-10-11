// The ridge, the first room of Rebecca's day: a new game opens there with the
// dawn monologue; camera 0 looks out over the edge, camera 1 back at the rock
// face; she can stand behind the west boulder (a mask); the path east leads
// down to the mountain trail.
//
//   OVERLAY=<REB build folder> node tools/harness/tests/ridge.ts
import { open } from '../lab.ts';
import { goTo, faceTowards, settle, useRoomData } from '../flows.ts';
import { Run, inRoom } from '../scenario.ts';

const overlay = process.env.OVERLAY;
if (!overlay) throw new Error('set OVERLAY to the REB build folder');
const RIDGE = { stage: 2, room: 0x13 };
const TRAIL = { stage: 2, room: 0x12 };
const OPENING = 0x80 + 0;

const session = await open(Number(process.env.PORT ?? 7802), '--mode REB --boot rebecca');
const run = new Run(session.link, overlay);
const { link } = run;
try {
  const opening = run.expectMessage(OPENING, 'the opening', 60_000);
  await link.waitFor((s) => inRoom(s, RIDGE) && s.play, 'the ridge', 60_000).catch(() => undefined);
  await link.frames(40);
  await run.picture('ridge-00-opening');
  if (!(await opening())) run.fail('the opening monologue never showed');
  let s = await settle(link, (st) => inRoom(st, RIDGE));
  run.log(s, `on the ridge, camera ${s.camera}`);
  if (s.camera !== 0) run.fail(`expected camera 0 at the start, got ${s.camera}`);
  await run.picture('ridge-01-camera0');

  s = await goTo(link, run.dataDirs, 3900, 9400, { radius: 250 });
  await faceTowards(link, 4000, 3000);
  s = await link.frames(15);
  run.log(s, `behind the west boulder, camera ${s.camera}`);
  if (s.camera !== 0) run.log(s, '(still camera 0)');
  await run.picture('ridge-02-behind-boulder');

  s = await goTo(link, run.dataDirs, 8000, 4800, { radius: 300 });
  s = await link.frames(15);
  run.log(s, `by the rock face, camera ${s.camera}`);
  if (s.camera !== 1) run.fail(`expected camera 1 by the rock face, got ${s.camera}`);
  await run.picture('ridge-03-camera1');

  s = await goTo(link, run.dataDirs, 12800, 5300, { radius: 400 });
  s = await settle(link, (st) => inRoom(st, TRAIL)).catch(() => link.state());
  run.log(s, 'took the path east');
  if (!inRoom(s, TRAIL)) run.fail(`expected the mountain trail, got stage ${s.stage} room ${s.room.toString(16)}`);
  run.finish();
} catch (err) {
  await run.crashed();
  throw err;
} finally {
  session.end();
}
