// Play Rebecca's day, or part of it, the way a player would (day.ts).
//
//   OVERLAY=<REB build folder> node tools/harness/tests/day.ts [<first> [<last>]]
//
// With no stretch named it plays the whole day from a new game: the
// end-to-end run. With one it plays just that stretch, starting from its
// checkpoint (the game booted into the stretch's room with the flags and
// items a player would have there); with two, every stretch from the first
// to the last. `node tools/harness/tests/day.ts --list` names the stretches.
// RECORD=<name> records the game window to <name>.mp4 in the game folder and
// fetches it to $OUT; the log's [Ns] stamps are seconds into the video.
import path from 'node:path';
import { fetch, open, startRecording, stopRecording } from '../lab.ts';
import { useFightBack } from '../flows.ts';
import { CROW, bootFor, play, stretchNames } from '../day.ts';
import { Run } from '../scenario.ts';

const args = process.argv.slice(2);
if (args[0] === '--list') {
  console.log(stretchNames.join('\n'));
  process.exit(0);
}
const first = args[0] ?? stretchNames[0]!;
const last = args[1] ?? (args[0] ? first : stretchNames.at(-1)!);
const overlay = process.env.OVERLAY;
if (!overlay) throw new Error('set OVERLAY to the REB build folder');
useFightBack(9000, [CROW]);
const session = await open(Number(process.env.PORT ?? 7802), bootFor(first));
const record = process.env.RECORD;
const remoteVideo = record ? `${process.env.RE1_LAB_GAME_DIR ?? 'D:\\Games\\RE1-decomp'}\\${record}.mp4` : undefined;
if (remoteVideo) startRecording(remoteVideo, session.port);
const run = new Run(session.link, overlay);
try {
  await play(run, first, last);
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
