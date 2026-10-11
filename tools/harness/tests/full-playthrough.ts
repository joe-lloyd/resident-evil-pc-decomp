// Rebecca's scenario from a new game through every chapter there is, in
// order, the way a player would play it.
//
//   OVERLAY=<REB build folder> node tools/harness/tests/full-playthrough.ts
// RECORD=<name> records the game window to <name>.mp4 in the game folder and
// fetches it to $OUT; the log's [Ns] stamps are seconds into the video.
import path from 'node:path';
import { fetch, open, startRecording, stopRecording } from '../lab.ts';
import { useFightBack } from '../flows.ts';
import { Run, chapter1 } from '../scenario.ts';

const overlay = process.env.OVERLAY;
if (!overlay) throw new Error('set OVERLAY to the REB build folder');
useFightBack();
// A plain REB dev boot starts where a new game does: the mountain trail.
const session = await open(Number(process.env.PORT ?? 7802), '--mode REB --boot rebecca');
const record = process.env.RECORD;
const remoteVideo = record ? `${process.env.RE1_LAB_GAME_DIR ?? 'D:\\Games\\RE1-decomp'}\\${record}.mp4` : undefined;
if (remoteVideo) startRecording(remoteVideo);
const run = new Run(session.link, overlay);
try {
  await chapter1(run);
  run.finish();
} catch (err) {
  await run.crashed();
  throw err;
} finally {
  if (remoteVideo) {
    const final = stopRecording(remoteVideo);
    const local = path.join(run.out, `${record}.mp4`);
    fetch(final, local);
    console.log(`video: ${local}`);
  }
  session.end();
}
