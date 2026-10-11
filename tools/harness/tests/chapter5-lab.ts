// Chapter 5 played through: turn the elevator power on, face Wesker and run
// back to the house.
//
//   OVERLAY=<REB build folder> node tools/harness/tests/chapter5-lab.ts
import { open } from '../lab.ts';
import { useFightBack } from '../flows.ts';
import { Run, chapter5 } from '../scenario.ts';

const overlay = process.env.OVERLAY;
if (!overlay) throw new Error('set OVERLAY to the REB build folder');
// No fighting back: nothing here needs it.
const session = await open(Number(process.env.PORT ?? 7802), '--mode REB --boot rebecca:4:17');
const run = new Run(session.link, overlay);
try {
  await chapter5(run);
  run.finish();
} catch (err) {
  await run.crashed();
  throw err;
} finally {
  session.end();
}
