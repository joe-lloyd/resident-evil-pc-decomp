// Put a room's pre-rendered background under a game screenshot. The game's
// screenshot is the Direct3D back buffer, which holds characters, 3D objects
// and foreground mask pieces over black; the background is drawn elsewhere.
//
// Placement is measured, not assumed: in the test-mode screenshots the scene
// is rendered 1:1 into the top-left 320x240 of the 640x480 buffer, so the
// background goes there at scale 1. Foreground mask pieces match the
// background pixel for pixel at offset (0, 0) and scale 1, and not at any
// other offset. Pass scale 2 for a build that renders the scene full window.
// Usage: node tools/harness/composite.ts <shot.bmp> <dataRoot> <stage> <room> <camera> <out.png> [--scale 2]
import { loadBackground } from './background.ts';
import { readBmp, writePng } from './image.ts';
import type { Image } from './image.ts';

/**
 * Pure core: every pure black shot pixel inside the scaled background's
 * top-left footprint shows the nearest-neighbour scaled background.
 */
export function underlay(shot: Image, background: Image, scale: number): Image {
  if (!Number.isInteger(scale) || scale < 1) throw new Error(`bad scale ${scale}`);
  const w = Math.min(shot.width, background.width * scale);
  const h = Math.min(shot.height, background.height * scale);
  const rgb = Uint8Array.from(shot.rgb);
  for (let y = 0; y < h; y++) {
    const by = Math.floor(y / scale);
    for (let x = 0; x < w; x++) {
      const i = (y * shot.width + x) * 3;
      if (rgb[i] !== 0 || rgb[i + 1] !== 0 || rgb[i + 2] !== 0) continue;
      const b = (by * background.width + Math.floor(x / scale)) * 3;
      rgb[i] = background.rgb[b]!;
      rgb[i + 1] = background.rgb[b + 1]!;
      rgb[i + 2] = background.rgb[b + 2]!;
    }
  }
  return { width: shot.width, height: shot.height, rgb };
}

export function composite(
  shotBmpPath: string,
  dataRoot: string,
  stage: number,
  room: number,
  camera: number,
  outPng: string,
  scale = 1,
): void {
  const shot = readBmp(shotBmpPath);
  const background = loadBackground(dataRoot, stage, room, camera);
  writePng(outPng, underlay(shot, background, scale));
}

if (import.meta.main) {
  const usage = 'usage: node tools/harness/composite.ts <shot.bmp> <dataRoot> <stage> <room> <camera> <out.png> [--scale N]';
  const [shot, dataRoot, stage, room, camera, out, flag, scale] = process.argv.slice(2);
  if (shot === undefined || dataRoot === undefined || stage === undefined || room === undefined || camera === undefined || out === undefined) {
    console.error(usage);
    process.exit(2);
  }
  if (flag !== undefined && (flag !== '--scale' || scale === undefined)) {
    console.error(usage);
    process.exit(2);
  }
  composite(shot, dataRoot, Number(stage), Number(room), Number(camera), out, scale === undefined ? 1 : Number(scale));
  console.log(`wrote ${out}`);
}
