// Her day's two people in the game: boot her into the ranger's cabin, where
// tools/rebecca/day/lookout/room.c places Hal (entity 34) and Dana, the
// ranger's partner (entity 33), check both are there, save screenshots from each of
// the room's cameras, and check each is moving: their idle changes the
// pixels where the camera shows them.
//
//   PORT=7811 node tools/harness/tests/people.ts [<outdir>]
//
// Needs the engine and the REB overlay deployed (tools/rebecca/build.ts).
// Exits 1 if either is missing, not where the script puts them, or still.
import { readFileSync } from 'node:fs';
import path from 'node:path';
import { open } from '../lab.ts';
import { settle } from '../flows.ts';
import { readPng, type Image } from '../image.ts';
import { snapshot } from '../snapshot.ts';

const outDir = process.argv[2] ?? '/tmp/rebecca-people-game';
const expected = [
  { name: 'hal', type: 34, x: 10710, z: 5610 },
  { name: 'dana', type: 33, x: 5780, z: 6290 },
];
// Spots on the cabin floor to stand her on, one per camera with luck: by the
// door looking in, and in the north-east corner looking back.
const spots = [
  { x: 6700, z: 9300, angle: 0x400 },
  { x: 10200, z: 8800, angle: 0x800 },
  { x: 4300, z: 8800, angle: 0x400 },
];

type V = [number, number, number];
interface Camera {
  from: V;
  to: V;
  fov: number;
}
const room: { cameras: Camera[] } = JSON.parse(
  readFileSync(path.join(import.meta.dirname, '..', '..', 'rebecca', 'day', 'lookout', 'renders', 'room.json'), 'utf8'),
);
const sub = (a: V, b: V): V => [a[0] - b[0], a[1] - b[1], a[2] - b[2]];
const dot = (a: V, b: V) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
const cross = (a: V, b: V): V => [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];
const unit = (a: V): V => {
  const l = Math.hypot(...a);
  return [a[0] / l, a[1] / l, a[2] / l];
};
/** Where a game point shows in the 640x480 frame (the room's 320x240 doubled); game Y points down. */
function project(cam: Camera, p: V): [number, number] {
  const fwd = unit(sub(cam.to, cam.from));
  const right = unit(cross(fwd, [0, -1, 0]));
  const up = cross(right, fwd);
  const d = sub(p, cam.from);
  const z = dot(d, fwd);
  return [2 * (160 + (dot(d, right) * cam.fov) / z), 2 * (120 - (dot(d, up) * cam.fov) / z)];
}
/** The frame box a person standing at (x, z) fills: feet to a head 2600 units up, a third as wide. */
function box(cam: Camera, x: number, z: number) {
  const [fx, fy] = project(cam, [x, 0, z]);
  const [, hy] = project(cam, [x, -2600, z]);
  const w = (fy - hy) / 3;
  return { x0: Math.max(0, fx - w), x1: Math.min(640, fx + w), y0: Math.max(0, hy), y1: Math.min(480, fy) };
}
const overlap = (a: ReturnType<typeof box>, b: ReturnType<typeof box>) => a.x0 < b.x1 && b.x0 < a.x1 && a.y0 < b.y1 && b.y0 < a.y1;
/** Pixels in the box whose brightness differs by more than a little between two frames. */
function changed(a: Image, b: Image, r: ReturnType<typeof box>): number {
  let n = 0;
  for (let y = Math.floor(r.y0); y < r.y1; y++)
    for (let x = Math.floor(r.x0); x < r.x1; x++) {
      const i = (y * a.width + x) * 3;
      if (Math.abs(a.rgb[i]! + a.rgb[i + 1]! + a.rgb[i + 2]! - b.rgb[i]! - b.rgb[i + 1]! - b.rgb[i + 2]!) > 72) n++;
    }
  return n;
}

const session = await open(Number(process.env.PORT ?? 7811), '--mode REB --boot rebecca:2:20');
const link = session.link;
/** Frames before the cabin's background animation repeats: 16 frames, three ticks each. */
const BACKDROP_LOOP = 48;
const failed: string[] = [];
try {
  await link.waitFor((s) => s.play, 'gameplay', 120_000);
  const s = await settle(link);
  for (const e of expected) {
    const found = s.enemies.find((n) => n.type === e.type);
    if (!found) failed.push(`${e.name}: no entity ${e.type} in the room`);
    else if (Math.hypot(found.x - e.x, found.z - e.z) > 50) failed.push(`${e.name}: at ${found.x}, ${found.z}, not ${e.x}, ${e.z}`);
    else console.log(`ok    ${e.name} (entity ${e.type}) at ${found.x}, ${found.z}`);
  }
  const seen = new Set<number>();
  const moving = new Set<string>();
  for (const spot of spots) {
    await link.place(spot.x, spot.z, spot.angle);
    const here = await settle(link);
    if (seen.has(here.camera)) continue;
    seen.add(here.camera);
    await snapshot(link, outDir, `cam${here.camera}`);
    // The idle, sampled a background-loop apart: the cabin's backdrop (its
    // curtain moves) repeats every 48 frames, so between samples only the
    // actor has changed. Their idle loop is 40 frames, so each sample still
    // catches it at a different point.
    const frames: Image[] = [];
    for (let i = 0; i < 6; i++) {
      await link.frames(BACKDROP_LOOP);
      frames.push(readPng(await snapshot(link, outDir, `cam${here.camera}-idle${i}`)));
    }
    const cam = room.cameras[here.camera]!;
    const her = box(cam, here.player.x, here.player.z);
    for (const e of expected) {
      const r = box(cam, e.x, e.z);
      if (r.x1 <= r.x0 || r.y1 <= r.y0 || overlap(r, her)) continue;
      const most = Math.max(...frames.slice(1).map((f) => changed(frames[0]!, f, r)));
      console.log(`      camera ${here.camera}: ${e.name} changes ${most} pixels over the idle`);
      if (most > 40) moving.add(e.name);
    }
    console.log(`shot  camera ${here.camera}`);
  }
  for (const e of expected) if (!moving.has(e.name)) failed.push(`${e.name}: no camera shows them moving`);
} finally {
  session.end();
}
console.log(failed.length ? `failed: ${failed.join('; ')}` : 'both people stand in the cabin');
process.exit(failed.length ? 1 : 0);
