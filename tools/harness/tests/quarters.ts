// Play Rebecca's day as four quarters side by side (playthrough.ts --quarter),
// each its own game on its own port, recorded, then stitch them: a quarter
// whose start was made up from the plan plays again from the real end of the
// quarter before, once that exists, until every quarter starts where the one
// before really ended, or one fails.
//
//   TYPESAFE_API_KEY=$(ssh vault get typesafe-api-key) OVERLAY=<REB build folder> \
//     RE1_LAB_GAME_DIR='D:\Games\RE1-files' RE1_LAB_REPO_DIR='C:\Users\joell\Tools\re1-files' \
//     node tools/harness/tests/quarters.ts [<out folder>]
//
// The ports put each game's window in its own corner of the second screen
// (src/platform/win32/main.cpp PlaceTestWindow). Each quarter's log, pictures
// and video are under <out>/q<n>/, the checkpoints under <out>/snaps/.
import { spawn } from 'node:child_process';
import { createWriteStream, existsSync, mkdirSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { load } from '../checkpoint.ts';

const out = process.argv[2] ?? '/tmp/rae-tests/quarters';
const snaps = path.join(out, 'snaps');
mkdirSync(snaps, { recursive: true });
const PORTS = [7840, 7850, 7860, 7870];
const script = path.join(path.dirname(fileURLToPath(import.meta.url)), 'playthrough.ts');

/** Play quarter `q`; resolves with whether it passed. Each try records to its own video. */
function play(q: number, attempt: number): Promise<boolean> {
  const dir = path.join(out, `q${q}`);
  mkdirSync(dir, { recursive: true });
  const log = createWriteStream(path.join(dir, `log-${attempt}.txt`));
  const child = spawn(process.execPath, [script, '--quarter', String(q)], {
    env: { ...process.env, PORT: String(PORTS[q - 1]), OUT: dir, SNAPS: snaps, RECORD: `reb-q${q}-${attempt}`, HARNESS_TRACE: '1' },
    stdio: ['ignore', 'pipe', 'pipe'],
  });
  child.stdout.pipe(log);
  child.stderr.pipe(log);
  return new Promise((resolve) => child.on('exit', (code) => resolve(code === 0)));
}

const endOf = (q: number) => path.join(snaps, `q${q}-end.json`);
/** Quarter q has a real end: it passed from a start that was itself real all the way back. */
const realEnd = (q: number) => existsSync(endOf(q)) && !load(endOf(q)).built;

const passed = new Map<number, boolean>();
const attempts = new Map<number, number>();
let todo = [1, 2, 3, 4];
for (let round = 1; todo.length && round <= 4; round++) {
  console.log(`round ${round}: quarters ${todo.join(', ')}`);
  const results = await Promise.all(
    todo.map(async (q) => {
      const n = (attempts.get(q) ?? 0) + 1;
      attempts.set(q, n);
      const ok = await play(q, n);
      console.log(`  quarter ${q}, try ${n}: ${ok ? 'passed' : 'FAILED'}${existsSync(endOf(q)) && load(endOf(q)).built ? ' (from a made-up start)' : ''}`);
      return [q, ok] as const;
    }),
  );
  for (const [q, ok] of results) passed.set(q, ok);
  // Again: each quarter that passed only from a made-up start, now that the one before has a real end.
  todo = [2, 3, 4].filter((q) => passed.get(q) && !realEnd(q) && realEnd(q - 1));
  if (results.some(([, ok]) => !ok)) break;
}

const chain = [1, 2, 3, 4].map((q) => `quarter ${q}: ${!passed.get(q) ? 'FAILED' : realEnd(q) ? 'real' : 'made-up start'}`);
console.log(chain.join('\n'));
const whole = [1, 2, 3, 4].every(realEnd);
console.log(whole ? 'PASS: the whole day, stitched from four real quarters' : 'FAIL: the day is not stitched end to end yet');
process.exit(whole ? 0 : 1);
