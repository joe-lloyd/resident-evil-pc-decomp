// Act 1 of Rebecca's day, as far as it is built: from a new game on the
// ridge, down the trail, into the ranger's lookout and its pick-ups.
//
//   OVERLAY=<REB build folder> node tools/harness/tests/day-act1.ts
// RECORD=<name> records the game window (see full-playthrough.ts).
import path from 'node:path';
import { fetch, open, startRecording, stopRecording } from '../lab.ts';
import { lookout, ridge, trail } from '../day.ts';
import { Run } from '../scenario.ts';

const overlay = process.env.OVERLAY;
if (!overlay) throw new Error('set OVERLAY to the REB build folder');
const session = await open(Number(process.env.PORT ?? 7802), '--mode REB --boot rebecca');
const record = process.env.RECORD;
const remoteVideo = record ? `${process.env.RE1_LAB_GAME_DIR ?? 'D:\\Games\\RE1-decomp'}\\${record}.mp4` : undefined;
if (remoteVideo) startRecording(remoteVideo);
const run = new Run(session.link, overlay);
try {
  await ridge(run);
  await trail(run);
  await lookout(run);
  run.finish();
} catch (err) {
  await run.crashed();
  throw err;
} finally {
  if (remoteVideo) {
    const local = path.join(run.out, `${record}.mp4`);
    fetch(stopRecording(remoteVideo), local);
    console.log(`video: ${local}`);
  }
  session.end();
}
