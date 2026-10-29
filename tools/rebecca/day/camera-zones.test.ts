// node --test tools/rebecca/day/camera-zones.test.ts
import assert from 'node:assert/strict';
import { test } from 'node:test';
import type { FloorScene } from './floors.ts';
import { GAP, inQuad, quadsOf, roomZones, type Quad } from './camera-zones.ts';

// A long room, a camera at each end looking in: each shows the half nearest it.
const scene: FloorScene = {
  cameras: [
    { from: [-9000, -5000, 4000], to: [5000, -1200, 4000], fov: 200 },
    { from: [29000, -5000, 4000], to: [15000, -1200, 4000], fov: 200 },
  ],
  walls: [],
  bounds: { x0: 0, z0: 0, x1: 20000, z1: 8000 },
};

/** What check_camera_switch does each frame (Room.cpp): the first trigger of the live camera's group she stands in cuts to its camera. */
function walk(zones: readonly (readonly Quad[])[], camera: number, path: readonly [number, number][]): number[] {
  const seen: number[] = [];
  for (const [x, z] of path) {
    const to = zones.findIndex((quads, c) => c !== camera && quads.some((q) => inQuad(q, x, z)));
    if (to >= 0) camera = to;
    seen.push(camera);
  }
  return seen;
}

test('quads come out clockwise with Z up, the way the engine tests them', () => {
  const [q] = quadsOf([[0, 0], [1000, 0], [1000, 1000], [0, 1000]]);
  assert.ok(q);
  assert.ok(inQuad(q, 500, 500));
  assert.ok(!inQuad(q, 1500, 500));
  // A triangle is a quad with its last corner repeated, and the test still holds.
  const [t] = quadsOf([[0, 0], [1000, 0], [0, 1000]]);
  assert.ok(t && inQuad(t, 200, 200) && !inQuad(t, 800, 800));
});

test('a two-camera room gets one quad a camera, each showing her', () => {
  const z = roomZones(scene, [undefined, undefined]);
  assert.deepEqual(z.zones.map((q) => q.length), [1, 1]);
  assert.equal(z.misses.length, 0);
});

test('a step back and forth at the border does not flip the camera', () => {
  const { zones } = roomZones(scene, [undefined, undefined]);
  // Walk east from camera 0's end until the camera cuts, then sway either side of that spot.
  const east: [number, number][] = [];
  for (let x = 1000; x <= 19000; x += 50) east.push([x, 4000]);
  const seen = walk(zones, 0, east);
  const cut = east[seen.indexOf(1)]![0];
  const sway: [number, number][] = [];
  for (let k = 0; k < 20; k++) sway.push([cut - 150, 4000], [cut + 150, 4000]);
  const swayed = walk(zones, 1, sway);
  assert.ok(swayed.every((c) => c === 1), `flipped while swaying 150 either side of the cut at x ${cut}`);
  // Going back, the cut to camera 0 comes GAP or more before the cut that brought her here.
  const west = [...east].reverse();
  const back = walk(zones, 1, west);
  const cutBack = west[back.indexOf(0)]![0];
  assert.ok(cut - cutBack >= GAP - 50, `the two cuts are ${cut - cutBack} apart`);
});
