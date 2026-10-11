// Chapter 4 played through: mix V-JOLT, kill Plant 42 at its roots, take the
// Helmet Key and go on to the lab.
//
//   OVERLAY=<REB build folder> node tools/harness/tests/chapter4-guardhouse.ts
import { open } from '../lab.ts';
import { useFightBack } from '../flows.ts';
import { Run, chapter4 } from '../scenario.ts';

const overlay = process.env.OVERLAY;
if (!overlay) throw new Error('set OVERLAY to the REB build folder');
// No fighting back: nothing here needs it.
const session = await open(Number(process.env.PORT ?? 7802), '--mode REB --boot rebecca:3:8');
const run = new Run(session.link, overlay);
try {
  await chapter4(run);
  run.finish();
} catch (err) {
  await run.crashed();
  throw err;
} finally {
  session.end();
}
