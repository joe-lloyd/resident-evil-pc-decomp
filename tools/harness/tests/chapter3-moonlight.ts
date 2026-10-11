// Chapter 3 played through: in the bar, find the sheet music, play the piano,
// take the Gold Emblem and go on to the guardhouse.
//
//   OVERLAY=<REB build folder> node tools/harness/tests/chapter3-moonlight.ts
import { open } from '../lab.ts';
import { useFightBack } from '../flows.ts';
import { Run, chapter3 } from '../scenario.ts';

const overlay = process.env.OVERLAY;
if (!overlay) throw new Error('set OVERLAY to the REB build folder');
// No fighting back: nothing here needs it.
const session = await open(Number(process.env.PORT ?? 7802), '--mode REB --boot rebecca:0:15');
const run = new Run(session.link, overlay);
try {
  await chapter3(run);
  run.finish();
} catch (err) {
  await run.crashed();
  throw err;
} finally {
  session.end();
}
