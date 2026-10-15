// The walks between Rebecca's outdoor rooms (src/game/PathWalk.cpp has the
// file format): a walk's Blender scene renders walk.NNNN.png and walk.json
// (blender/reb.py export_walk); here each picture becomes a background pak
// and they are packed into one RBW1 file.
import { readFileSync } from 'node:fs';
import path from 'node:path';
import { readPng } from '../harness/image.ts';
import { look } from './day/look.ts';
import { makePak } from './pak.ts';

export function buildWalk(rendersDir: string): Uint8Array {
  const meta = JSON.parse(readFileSync(path.join(rendersDir, 'walk.json'), 'utf8')) as { frames: number; ticks: number; stepTicks: number };
  if (meta.frames < 1 || meta.frames > 0xffff || meta.ticks < 1 || meta.ticks > 255 || meta.stepTicks < 0 || meta.stepTicks > 255) {
    throw new Error(`${rendersDir}: bad walk.json`);
  }
  const paks = Array.from({ length: meta.frames }, (_, k) => makePak(look(readPng(path.join(rendersDir, `walk.${String(k).padStart(4, '0')}.png`)))));
  const head = 8 + 4 * paks.length;
  const out = new Uint8Array(head + paks.reduce((n, p) => n + p.length, 0));
  const v = new DataView(out.buffer);
  out.set([...'RBW1'].map((c) => c.charCodeAt(0)), 0);
  v.setUint16(4, meta.frames, true);
  out[6] = meta.ticks;
  out[7] = meta.stepTicks;
  let at = head;
  paks.forEach((p, i) => {
    v.setUint32(8 + i * 4, at, true);
    out.set(p, at);
    at += p.length;
  });
  return out;
}

/** objspr\walkNN.dat: walk number NN, the door record's +0x08 byte. */
export const walkFileName = (n: number) => `WALK${String(n).padStart(2, '0')}.DAT`;
