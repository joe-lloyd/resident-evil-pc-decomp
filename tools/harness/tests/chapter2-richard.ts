// Chapter 2 played through: from the save room after the meeting, up the 1F
// left stairs to Richard, back down for the serum, up again in time, and on
// to the bar.
// SERUM_FIRST=1 takes the serum before going up, so he is treated on sight.
// LATE=1 waits out the clock in the save room, so he dies.
//
//   OVERLAY=<REB build folder> node tools/harness/tests/chapter2-richard.ts
import { open } from '../lab.ts';
import { useFightBack } from '../flows.ts';
import { Run, chapter2 } from '../scenario.ts';

const overlay = process.env.OVERLAY;
if (!overlay) throw new Error('set OVERLAY to the REB build folder');
useFightBack();
const session = await open(Number(process.env.PORT ?? 7802), '--mode REB --boot rebecca:0:0');
const run = new Run(session.link, overlay);
try {
  await chapter2(run, { serumFirst: process.env.SERUM_FIRST === '1', late: process.env.LATE === '1' });
  run.finish();
} catch (err) {
  await run.crashed();
  throw err;
} finally {
  session.end();
}
