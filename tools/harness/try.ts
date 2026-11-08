// Load a playthrough checkpoint into the lab's game and hand her to the
// keyboard, to try a job by hand from where a run saved it. No god mode, so
// hurt is real. The game is left running on the lab's desktop.
//
//   node tools/harness/try.ts <snaps>/after-<goal>.json
import { load, restore } from './checkpoint.ts';

const file = process.argv[2];
if (!file) throw new Error('usage: try.ts <checkpoint.json>');
const cp = load(file);
// lab.ts reads its default at module load. Rebecca's playtest lives here.
process.env.RE1_LAB_GAME_DIR ??= 'D:\\Games\\RE1-files';
const { open } = await import('./lab.ts');
const session = await open(Number(process.env.PORT ?? 7811), '--mode REB --boot rebecca');
let restored = false;
try {
  await session.link.waitFor((st) => st.play, 'gameplay', 180_000);
  await restore(session.link, cp);
  await session.link.keyboard(true);
  restored = true;
} finally { session.end(!restored); }
process.stdout.write(`Loaded ${file}. Game left running.\n`);
