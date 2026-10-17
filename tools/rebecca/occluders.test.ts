import { test } from 'node:test';
import assert from 'node:assert/strict';
import { FRAME_H, FRAME_W } from './masks.ts';
import { project } from './day/floors.ts';
import { occluders, type Camera } from './occluders.ts';

// A camera 3 m up at the room's south edge, looking north and down at a floor 6 m deep.
const cam: Camera = { from: [5100, -5100, 0], to: [5100, 0, 10200], fov: 200 };
const floor = [{ x0: 3400, z0: 3400, x1: 6800, z1: 10200 }];
const anywhere = () => true;
// Her chest standing at the middle of the floor.
const chest = project(cam, [5100, -1300, 6800])!;
const at = Math.round(chest.y) * FRAME_W + Math.round(chest.x);
const frame = (d: number) => {
  const all = new Float32Array(FRAME_W * FRAME_H).fill(Infinity);
  all[at] = d;
  return all;
};

test('a surface between the camera and where she stands covers her', () => {
  const out = occluders(cam, frame(chest.z - 2000), floor, anywhere);
  assert.equal(out[at], Math.fround(chest.z - 2000));
});

test('a wall behind every spot she can stand is never drawn over her', () => {
  const out = occluders(cam, frame(40000), floor, anywhere);
  assert.equal(out[at], Infinity);
});

test('the floor, and a board lying on it, are not in front of her', () => {
  // A plank 10 cm high just in front of where she stands.
  const plank = project(cam, [5100, -170, 5100])!;
  const i = Math.round(plank.y) * FRAME_W + Math.round(plank.x);
  const all = new Float32Array(FRAME_W * FRAME_H).fill(Infinity);
  all[i] = plank.z;
  assert.equal(occluders(cam, all, floor, anywhere)[i], Infinity);
});

test('a crate a metre high in front of her covers her', () => {
  const crate = project(cam, [5100, -1700, 5100])!;
  const i = Math.round(crate.y) * FRAME_W + Math.round(crate.x);
  const all = new Float32Array(FRAME_W * FRAME_H).fill(Infinity);
  all[i] = crate.z;
  assert.equal(occluders(cam, all, floor, anywhere)[i], Math.fround(crate.z));
});

test('nothing covers her where she cannot stand', () => {
  const out = occluders(cam, frame(chest.z - 2000), floor, () => false);
  assert.equal(out[at], Infinity);
});
