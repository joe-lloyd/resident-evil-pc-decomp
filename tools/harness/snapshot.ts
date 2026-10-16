// A viewable picture of the game right now: capture the frame on the game
// machine, fetch it and save it as a PNG.
//
// The frame is the whole 640x480 window, background included. (Early dev
// boots skipped logos_state's video setup and drew a 320x240 scene with no
// background; composite.ts laid the .pak background under those frames. It is
// kept for reading old captures, but snapshots no longer need it.)
import { mkdirSync } from 'node:fs';
import path from 'node:path';
import { readBmp, writePng } from './image.ts';
import { fetch } from './lab.ts';
import type { GameLink } from './link.ts';

const remoteDir = process.env.RE1_LAB_SHOT_DIR ?? 'C:\\Users\\joell\\Tools\\wintool';

/** Save the current frame as `<outDir>/<name>.png`; returns the path. */
export async function snapshot(link: GameLink, outDir: string, name: string): Promise<string> {
  mkdirSync(outDir, { recursive: true });
  const bmp = path.join(outDir, `${name}.bmp`);
  await link.shot(`${remoteDir}\\${name}.bmp`);
  fetch(`${remoteDir}\\${name}.bmp`, bmp);
  const png = path.join(outDir, `${name}.png`);
  writePng(png, readBmp(bmp));
  return png;
}
