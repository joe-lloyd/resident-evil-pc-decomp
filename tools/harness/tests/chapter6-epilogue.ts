// Chapter 6 and the epilogue played through: get past the Hunter (FIGHT=1
// fights it), meet Chris on the heliport, and the game ends back at the title.
//
//   OVERLAY=<REB build folder> node tools/harness/tests/chapter6-epilogue.ts
import { open } from '../lab.ts';
import { useFightBack } from '../flows.ts';
import { Run, chapter6 } from '../scenario.ts';

const overlay = process.env.OVERLAY;
if (!overlay) throw new Error('set OVERLAY to the REB build folder');
// No fighting back: nothing here needs it.
const session = await open(Number(process.env.PORT ?? 7802), '--mode REB --boot rebecca:5:1');
const run = new Run(session.link, overlay);
try {
  await chapter6(run, { fightHunter: process.env.FIGHT === '1' });
  run.finish();
} catch (err) {
  await run.crashed();
  throw err;
} finally {
  session.end();
}
