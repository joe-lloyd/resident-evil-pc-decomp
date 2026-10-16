// node --test tools/rebecca/day/foes.test.ts
import assert from 'node:assert/strict';
import { test } from 'node:test';
import { facing, foeLines, KILL_FLAGS, place, type Floor } from './foes.ts';

// A 10 x 6 m floor: a crate in the middle, a door on the west edge where she comes in.
const floor: Floor = {
  bounds: { x0: 1700, z0: 1700, x1: 18700, z1: 11900 },
  walls: [{ shape: 'box', x0: 9000, z0: 6000, x1: 11000, z1: 8000 }],
  doors: [{ zone: { x0: 1700, z0: 5000, x1: 2700, z1: 8000 }, arrive: { x: 3400, z: 6800 } }],
};

test('enemies stand on free floor: inside the bounds, clear of walls and doors, apart from each other', () => {
  const spots = place(floor, 3);
  assert.equal(spots.length, 3);
  for (const p of spots) {
    assert.ok(p.x > 1700 + 600 && p.x < 18700 - 600 && p.z > 1700 + 600 && p.z < 11900 - 600, `${p.x},${p.z} inside`);
    assert.ok(p.x < 9000 - 600 || p.x > 11000 + 600 || p.z < 6000 - 600 || p.z > 8000 + 600, `${p.x},${p.z} clear of the crate`);
    assert.ok(p.x > 2700 + 1000, `${p.x},${p.z} clear of the door`);
  }
  for (const [i, a] of spots.entries()) for (const b of spots.slice(i + 1)) assert.ok(Math.hypot(a.x - b.x, a.z - b.z) >= 2000);
});

test('the first stands as far from where she comes in as the room allows', () => {
  const [first] = place(floor, 1);
  assert.ok(first!.x > 17000, `at x ${first!.x}: the far, east end`);
});

test('facing: 0 is +X, 0x400 is -Z, 0xC00 is +Z', () => {
  assert.equal(facing({ x: 0, z: 0 }, { x: 100, z: 0 }), 0);
  assert.equal(facing({ x: 0, z: 0 }, { x: 0, z: -100 }), 0x400);
  assert.equal(facing({ x: 0, z: 0 }, { x: 0, z: 100 }), 0xc00);
});

test('lines: one kill flag each, consumed in order, and never the yard Cerberus\'s 200', () => {
  assert.ok(!KILL_FLAGS.includes(200));
  const flags = [186, 187];
  const lines = foeLines('woods', floor, flags);
  assert.equal(lines.length, 2);
  assert.match(lines[0]!, /^enemy\(2, 1, 186, 1, 2, 0, 0, \d+, 0, 0, \d+, 0, \d+, 0, 0, 0, 0\);/);
  assert.match(lines[1]!, /^enemy\(2, 1, 187, .*, 1, 0, 0, 0\);/);
  assert.deepEqual(flags, []);
});
