// node --test tools/rebecca/day/supplies.test.ts
import assert from 'node:assert/strict';
import { test } from 'node:test';
import { ITEM_FLAGS, supplyLines, supplyModels } from './supplies.ts';
import type { Floor } from './foes.ts';

const floor: Floor = {
  bounds: { x0: 1700, z0: 1700, x1: 11900, z1: 8500 },
  walls: [],
  doors: [{ zone: { x0: 1700, z0: 4000, x1: 2700, z1: 6000 }, arrive: { x: 3400, z: 5100 } }],
};

test("a room's models: one per kind, in the order its pickups name them", () => {
  // The lodge's spray and red herb, then the ink ribbons a save room has (plan/saves.ts).
  assert.deepEqual(supplyModels('lodge'), [
    { from: 'Stage3/ROOM3090.RDT', index: 0 },
    { from: 'Stage1/ROOM10C0.RDT', index: 1 },
    { from: 'Stage3/ROOM30E0.RDT', index: 2 },
  ]);
  assert.deepEqual(supplyModels('nowhere'), []);
});

test('each pickup has its own flag, kept while the item is there, and the model slot of its kind', () => {
  const flags = [180, 181, 182];
  const lines = supplyLines('lodge', floor, flags, 7);
  assert.deepEqual(flags, []);
  assert.equal(lines[0], 'if (ck(FG_ITEM, 180, 0)) {  // spray');
  assert.match(lines[1]!, /^ {4}item_aot_set\(7, \d+, \d+, 1200, 1200, 65, 1, 0, 255, .*, 180, 129, 0, 0\);$/);
  assert.match(lines[4]!, /^ {4}item_aot_set\(8, \d+, \d+, 1200, 1200, 67, 1, 1, 255, .*, 181, 129, 1, 0\);$/);
  assert.match(lines[7]!, /^ {4}item_aot_set\(9, \d+, \d+, 1200, 1200, 47, 3, 2, 255, .*, 182, 129, 0, 0\);$/);
});

test('the flags stay clear of the rest of her day: 230-247, and the save room\'s 22', () => {
  assert.ok(ITEM_FLAGS.every((f) => f < 230 && f !== 22));
});
