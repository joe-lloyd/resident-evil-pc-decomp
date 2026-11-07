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

test('enemies a step brings or takes away stand inside that step\'s test, and still use a kill flag each', () => {
  const flags = [186, 187, 188];
  const when = (w: { after?: string; until?: string }) => [w.after && `done(${w.after})`, w.until && `!done(${w.until})`].filter(Boolean).join(' && ');
  const lines = foeLines('test-stirred', floor, flags, 0, when, {
    'test-stirred': [['zombie', 1], ['zombie', 2, { after: 'ring-bell' }]],
  });
  assert.equal(lines[1], 'if (done(ring-bell)) {');
  assert.match(lines[2]!, /^ {4}enemy\(17, 0, 187, /);
  assert.match(lines[3]!, /^ {4}enemy\(17, 0, 188, /);
  assert.equal(lines[4], '}');
  assert.deepEqual(flags, []);
  // The brought ones stand apart from the one already there.
  const at = (l: string) => l.match(/, (\d+), 0, (\d+), \d+, 0, 0, 0\);/)!.slice(1).map(Number);
  const [first, second] = [at(lines[0]!), at(lines[2]!)];
  assert.ok(Math.hypot(first[0]! - second[0]!, first[1]! - second[1]!) >= 2000, `${first} and ${second} apart`);
});

test('every step that brings or takes away enemies is a step of the plan, or a mark of how one was done', async () => {
  const { day } = await import('../plan/day.ts');
  const { FOES } = await import('./foes.ts');
  const { MARK_FLAGS } = await import('./events.ts');
  const steps = new Set([...day.steps.map((s) => s.id), ...MARK_FLAGS.keys()]);
  for (const [slug, groups] of Object.entries(FOES)) {
    for (const g of groups) for (const s of [g[2]?.after, g[2]?.until]) if (s) assert.ok(steps.has(s), `${slug}: ${s} is not a plan step`);
  }
});

test('each kind of enemy in a room takes the next block of sound slots', () => {
  for (const line of foeLines('junction', floor, [186, 187])) assert.match(line, /^enemy\(3, .*, 0\);  \/\/ a spinner$/);
  const lines = foeLines('washout', floor, [186, 187, 188], 0, () => 'done(generator-on)');
  assert.match(lines[0]!, /^enemy\(10, .*, 0\);  \/\/ a adder$/);
  assert.match(lines[3]!, /^ {4}enemy\(2, .*, 1\);  \/\/ a cerberus$/);
});

test('a room with a third kind of enemy has no sound for it', () => {
  const foes = { three: [['zombie', 1], ['crow', 1], ['adder', 1]] } as const;
  assert.throws(() => foeLines('three', floor, [186, 187, 188], 0, undefined, foes), /3 kinds of enemy/);
});
