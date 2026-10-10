// A viewable picture of the game right now: capture the back buffer, fetch
// it, lay the room's background under it (composite.ts) and save a PNG of
// the 320x240 scene scaled 2x.
import { existsSync, mkdirSync } from 'node:fs';
import path from 'node:path';
import { backgroundPath, loadBackground } from './background.ts';
import { readBmp, writePng, type Image } from './image.ts';
import { underlay } from './composite.ts';
import { fetch } from './lab.ts';
import type { GameLink } from './link.ts';

const remoteDir = process.env.RE1_LAB_SHOT_DIR ?? 'C:\\Users\\joell\\Tools\\wintool';
// Folders that hold Stage<n>/RC<n><room><camera>.pak, first match wins. The REB
// overlay comes first, so the backgrounds of rooms it adds are found; every other
// room falls through to the player's game data. RE1_OVERLAY and RE1_DATA override.
const dataRoots = [process.env.RE1_OVERLAY ?? '/tmp/rae-reb/REB', process.env.RE1_DATA ?? '/tmp/re1-pc'];

function cropScale(image: Image, w: number, h: number, scale: number): Image {
  const out = new Uint8Array(w * scale * h * scale * 3);
  for (let y = 0; y < h * scale; y++) {
    for (let x = 0; x < w * scale; x++) {
      const s = (Math.floor(y / scale) * image.width + Math.floor(x / scale)) * 3;
      out.set(image.rgb.subarray(s, s + 3), (y * w * scale + x) * 3);
    }
  }
  return { width: w * scale, height: h * scale, rgb: out };
}

/** Save the current frame as `<outDir>/<name>.png`; returns the path. */
export async function snapshot(link: GameLink, outDir: string, name: string): Promise<string> {
  mkdirSync(outDir, { recursive: true });
  const state = await link.state();
  const bmp = path.join(outDir, `${name}.bmp`);
  await link.shot(`${remoteDir}\\${name}.bmp`);
  fetch(`${remoteDir}\\${name}.bmp`, bmp);
  let image = readBmp(bmp);
  if (state.play) {
    try {
      const root = dataRoots.find((r) => existsSync(backgroundPath(r, state.stage, state.room, state.camera)));
      if (root !== undefined) image = underlay(image, loadBackground(root, state.stage, state.room, state.camera), 1);
    } catch {
      // Stages without PC backgrounds (arrange rooms): keep the raw frame.
    }
  }
  const png = path.join(outDir, `${name}.png`);
  writePng(png, cropScale(image, 320, 240, 2));
  return png;
}
