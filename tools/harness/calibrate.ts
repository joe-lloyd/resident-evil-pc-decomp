// Run a list of steps and take a screenshot after each one, so state values
// can be matched to what is on screen. Development aid, not a test.
//   node tools/harness/calibrate.ts <outdir> "tap 13 3|60" "tap 67 3|90" ...
// Each argument is `<protocol line>|<frames to wait>`; the line may be empty.
import { mkdirSync } from 'node:fs';
import path from 'node:path';
import { open, fetch } from './lab.ts';
import { roomLabel, screen } from './state.ts';
import { composite } from './composite.ts';

// Original PC data, for the backgrounds the screenshots lack (see composite.ts).
const dataRoot = process.env.RE1_DATA ?? '/tmp/re1-pc';

const [outDir, ...steps] = process.argv.slice(2);
if (!outDir) throw new Error('usage: calibrate.ts <outdir> "<line>|<frames>" ...');
mkdirSync(outDir, { recursive: true });

// RE1_ARGS adds launch arguments, e.g. RE1_ARGS='--boot chris:0:4'.
const session = await open(7801, process.env.RE1_ARGS ?? '');
const remoteDir = 'C:\\Users\\joell\\Tools\\wintool';
try {
  for (const [i, step] of steps.entries()) {
    const [line, wait] = step.split('|');
    if (line) session.link.raw(line);
    const s = await session.link.frames(Number(wait ?? 30));
    const name = `step${String(i).padStart(2, '0')}.bmp`;
    await session.link.shot(`${remoteDir}\\${name}`);
    fetch(`${remoteDir}\\${name}`, path.join(outDir, name));
    try {
      composite(path.join(outDir, name), dataRoot, s.stage, s.room, s.camera, path.join(outDir, name.replace('.bmp', '.png')));
    } catch {
      // No background for this screen (title, menus): keep the raw shot.
    }
    console.log(
      `${name}  frame ${s.frame}  room ${roomLabel(s)}  ${screen(s)}  title ${s.title}  fmv ${s.fmv}  msf ${s.msf.toString(16)}  msg ${s.messageChoice.toString(16)}/${s.messageId}  char ${s.player.id} hp ${s.player.hp}`,
    );
  }
} finally {
  session.end();
}
