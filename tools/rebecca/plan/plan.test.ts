// node --test tools/rebecca/plan/plan.test.ts
import assert from 'node:assert/strict';
import { test } from 'node:test';
import { day } from './day.ts';
import { check, type Plan } from './plan.ts';
import { checkMaps } from './maps.ts';

test("Rebecca's day can be played through to her credits", () => {
  const r = check(day);
  assert.deepEqual(r.errors, []);
  assert.deepEqual(r.warnings, []);
  assert.equal(r.order.at(-1), 'credits');
  assert.equal(day.places.length, 58);
});

const tiny = (over: Partial<Plan>): Plan => ({
  title: 'tiny',
  start: 'a',
  acts: [{ n: 1, title: '', time: '', summary: '' }],
  places: [
    { id: 'a', name: 'A', built: 'planned', act: 1, cameras: 1, at: [0, 0], there: '', moves: '', enemies: '', story: '' },
    { id: 'b', name: 'B', built: 'planned', act: 1, cameras: 1, at: [1, 0], there: '', moves: '', enemies: '', story: '' },
  ],
  links: [{ from: 'a', to: 'b', kind: 'door', opens: 'key' }],
  steps: [
    { id: 'key', label: 'key', at: 'a', act: 1, kind: 'find', needs: [], built: 'planned' },
    { id: 'end', label: 'end', at: 'b', act: 1, kind: 'goal', needs: ['key'], built: 'planned' },
  ],
  ...over,
});

test('a step behind a lock its needs do not open is an error', () => {
  const r = check(tiny({ steps: [
    { id: 'key', label: 'key', at: 'a', act: 1, kind: 'find', needs: [], built: 'planned' },
    { id: 'end', label: 'end', at: 'b', act: 1, kind: 'goal', needs: [], built: 'planned' },
  ] }));
  assert.deepEqual(r.errors, ["end is at b, but what it needs doesn't get her there"]);
});

test('a key locked behind its own door can never be had', () => {
  const r = check(tiny({ steps: [
    { id: 'key', label: 'key', at: 'b', act: 1, kind: 'find', needs: [], built: 'planned' },
    { id: 'end', label: 'end', at: 'b', act: 1, kind: 'goal', needs: ['key'], built: 'planned' },
  ] }));
  assert.deepEqual(r.errors, [
    "key is at b, but what it needs doesn't get her there",
    'key can never be done',
    'end can never be done',
  ]);
});

test('a find nothing uses is flagged', () => {
  const r = check(tiny({ steps: [
    { id: 'key', label: 'key', at: 'a', act: 1, kind: 'find', needs: [], built: 'planned' },
    { id: 'spare', label: 'spare', at: 'a', act: 1, kind: 'find', needs: [], built: 'planned' },
    { id: 'end', label: 'end', at: 'b', act: 1, kind: 'goal', needs: ['key'], built: 'planned' },
  ] }));
  assert.deepEqual(r.errors, []);
  assert.deepEqual(r.warnings, ['nothing needs spare: mark it optional or use it']);
  assert.deepEqual(r.open, [2, 2, 1]);
});

test('every room is on one map, and each map is a step she can take', () => {
  assert.deepEqual(checkMaps(day), []);
});
