// How tall the player stands in game units, measured on screen in one of
// Rebecca's day rooms: stand her at known points, find the top of her head
// where the frame stops matching the room's background render, and solve the
// camera's projection for the height that puts the head there. Development
// aid for keeping the Blender scenes to her scale, not a test.
//
//   node tools/harness/measure-height.ts <slug> <stage>:<room> x,z [x,z ...]
import path from 'node:path';
import { readFileSync } from 'node:fs';
import { open } from './lab.ts';
import { readPng, type Image } from './image.ts';
import { settle } from './flows.ts';
import { snapshot } from './snapshot.ts';

const [slug, where, ...points] = process.argv.slice(2);
if (!slug || !where || !points.length) throw new Error('usage: measure-height.ts <slug> <stage>:<room> x,z ...');
const renders = path.join(import.meta.dirname, '..', 'rebecca', 'day', slug, 'renders');
const room = JSON.parse(readFileSync(path.join(renders, 'room.json'), 'utf8')) as {
  cameras: { from: number[]; to: number[]; fov: number }[];
};

type V = [number, number, number];
const sub = (a: V, b: V): V => [a[0] - b[0], a[1] - b[1], a[2] - b[2]];
const dot = (a: V, b: V) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
const cross = (a: V, b: V): V => [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];
const norm = (a: V): V => {
  const l = Math.hypot(...a);
  return [a[0] / l, a[1] / l, a[2] / l];
};

/** Screen position (320x240) of game point p for a camera; game Y points down. */
function project(cam: { from: number[]; to: number[]; fov: number }, p: V): [number, number] {
  const eye = cam.from as V;
  const fwd = norm(sub(cam.to as V, eye));
  const right = norm(cross(fwd, [0, -1, 0]));
  const up = cross(right, fwd);
  const d = sub(p, eye);
  const z = dot(d, fwd);
  return [160 - (dot(d, right) * cam.fov) / z, 120 - (dot(d, up) * cam.fov) / z];
}

/** Topmost row (in 240 lines) in columns cx +- 12 where the frame differs from the background. */
function headRow(frame: Image, bg: Image, cx: number): number {
  for (let y = 0; y < 240; y++) {
    let hits = 0;
    for (let x = Math.max(0, Math.round(cx) - 12); x < Math.min(320, Math.round(cx) + 12); x++) {
      const f = ((y * 2) * frame.width + x * 2) * 3;
      const b = (y * 320 + x) * 3;
      const diff = Math.abs(frame.rgb[f]! - bg.rgb[b]!) + Math.abs(frame.rgb[f + 1]! - bg.rgb[b + 1]!) + Math.abs(frame.rgb[f + 2]! - bg.rgb[b + 2]!);
      if (diff > 60) hits++;
    }
    if (hits >= 3) return y;
  }
  return -1;
}

const [stage, roomId] = where.split(':').map(Number) as [number, number];
const session = await open(7802, `--mode REB --boot rebecca:${stage}:${roomId}`);
try {
  await settle(session.link);
  for (const pt of points) {
    const [x, z] = pt.split(',').map(Number) as [number, number];
    await session.link.place(x, z, 0);
    const s = await settle(session.link);
    const cam = room.cameras[s.camera]!;
    const frame = readPng(await snapshot(session.link, '/tmp/rae-tests', `height-${slug}-${x}-${z}`));
    const bg = readPng(path.join(renders, `cam${s.camera}.png`));
    const [fx, fy] = project(cam, [s.player.x, 0, s.player.z]);
    const top = headRow(frame, bg, fx);
    // Solve for the height whose head lands on the measured row.
    let lo = 0;
    let hi = 4000;
    for (let i = 0; i < 40; i++) {
      const mid = (lo + hi) / 2;
      if (project(cam, [s.player.x, -mid, s.player.z])[1] > top) lo = mid;
      else hi = mid;
    }
    console.log(`at (${s.player.x}, ${s.player.z}) camera ${s.camera}: feet row ${fy.toFixed(1)}, head row ${top}, height ${Math.round(lo)}`);
  }
} finally {
  session.end();
}
