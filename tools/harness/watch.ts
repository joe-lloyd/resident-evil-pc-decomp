// Explore a running game: print a short line whenever the room, screen,
// message or flags change, and send any line typed on stdin as a command.
//   node tools/harness/watch.ts [port]     (game launched and tunnelled already)
//   node tools/harness/watch.ts [port] --launch
//   node tools/harness/watch.ts [port] --launch --steps "wait 300;tap 67;wait 90;quit"
// A step is a protocol line, `wait <frames>` or `quit`.
import readline from 'node:readline';
import { GameLink } from './link.ts';
import { open } from './lab.ts';
import { roomLabel, screen, type GameState } from './state.ts';

const port = Number(process.argv[2] ?? 7801);
const session = process.argv.includes('--launch') ? await open(port) : undefined;
const link = session?.link ?? (await GameLink.connect(port));

function summary(s: GameState): string {
  const flags = s.banks.map((b) => Buffer.from(b).toString('hex')).join('|');
  return [
    `room ${roomLabel(s)} cam ${s.camera}`,
    screen(s),
    `title ${s.title}`,
    `msf ${s.msf.toString(16)}`,
    `msg ${s.messageChoice.toString(16)}/${s.messageId}`,
    `char ${s.player.id}/${s.charModel} hp ${s.player.hp}/${s.player.maxHp}`,
    `enemies ${s.enemies.map((e) => e.type.toString(16)).join(',')}`,
    `flags ${flags.length}`,
  ].join('  ');
}

let last = '';
let lastFlags = '';
setInterval(() => {
  const s = link.latest;
  if (!s) return;
  const line = summary(s);
  const flags = s.banks.map((b) => Buffer.from(b).toString('hex')).join('|');
  if (line !== last) console.log(`[${s.frame}] ${line}`);
  if (lastFlags && flags !== lastFlags) console.log(`[${s.frame}] flags changed`);
  last = line;
  lastFlags = flags;
}, 100);

async function step(cmd: string): Promise<void> {
  const [word, arg] = cmd.trim().split(/\s+/, 2);
  if (word === 'quit') {
    session?.end();
    process.exit(0);
  } else if (word === 'wait') {
    await link.frames(Number(arg));
  } else if (word) {
    link.raw(cmd.trim());
  }
}

const stepsAt = process.argv.indexOf('--steps');
if (stepsAt >= 0) {
  for (const cmd of (process.argv[stepsAt + 1] ?? '').split(';')) await step(cmd);
} else {
  readline.createInterface({ input: process.stdin }).on('line', (cmd) => void step(cmd));
}
