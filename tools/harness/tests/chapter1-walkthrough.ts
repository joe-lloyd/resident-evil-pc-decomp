// The prologue and Chapter 1 played through: down the mountain trail, across the
// courtyard garden, in through the back of the mansion to the save room,
// fighting what is left on the way, until the meeting with Chris plays.
//
//   OVERLAY=<REB build folder> node tools/harness/tests/chapter1-walkthrough.ts
import { open } from '../lab.ts';
import { useFightBack } from '../flows.ts';
import { Run, chapter1 } from '../scenario.ts';

const overlay = process.env.OVERLAY;
if (!overlay) throw new Error('set OVERLAY to the REB build folder');
useFightBack();
const session = await open(Number(process.env.PORT ?? 7802), '--mode REB --boot rebecca');
const run = new Run(session.link, overlay);
try {
  await chapter1(run);
  run.finish();
} catch (err) {
  await run.crashed();
  throw err;
} finally {
  session.end();
}
