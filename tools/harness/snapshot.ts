// A viewable picture of the game right now: capture the back buffer, fetch
// it, lay the room's background under it (composite.ts) and save a PNG of
// the 320x240 scene scaled 2x.
import { mkdirSync } from 'node:fs';
import path from 'node:path';
import { loadBackground } from './background.ts';
import { readBmp, writePng, type Image } from './image.ts';
import { underlay } from './composite.ts';
import { fetch } from './lab.ts';
import type { GameLink } from './link.ts';

const remoteDir = process.env.RE1_LAB_SHOT_DIR ?? 'C:\\Users\\joell\\Tools\\wintool';
const dataRoot = process.env.RE1_DATA ?? '/tmp/re1-pc';

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
      image = underlay(image, loadBackground(dataRoot, state.stage, state.room, state.camera), 1);
    } catch {
      // Stages without PC backgrounds (arrange rooms): keep the raw frame.
    }
  }
  const png = path.join(outDir, `${name}.png`);
  writePng(png, cropScale(image, 320, 240, 2));
  return png;
}
