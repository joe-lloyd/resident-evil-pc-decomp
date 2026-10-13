// node --test tools/rebecca/plan/plan.test.ts
import assert from 'node:assert/strict';
import { test } from 'node:test';
import { act1 } from './act1.ts';
import { check, type Act } from './plan.ts';

test('act 1 can be played through to its goal', () => {
  const r = check(act1);
  assert.deepEqual(r.errors, []);
  assert.deepEqual(r.warnings, []);
  assert.ok(r.order.includes('valley'));
});

const tiny = (over: Partial<Act>): Act => ({
  title: 'tiny',
  start: 'a',
  places: [
    { id: 'a', name: 'A', built: 'planned', at: [0, 0], there: '', moves: '', enemies: '', story: '' },
    { id: 'b', name: 'B', built: 'planned', at: [1, 0], there: '', moves: '', enemies: '', story: '' },
  ],
  links: [{ from: 'a', to: 'b', kind: 'door', opens: 'key' }],
  steps: [
    { id: 'key', label: 'key', at: 'a', kind: 'find', needs: [], built: 'planned' },
    { id: 'end', label: 'end', at: 'b', kind: 'goal', needs: ['key'], built: 'planned' },
  ],
  ...over,
});

test('a step behind a lock its needs do not open is an error', () => {
  const r = check(tiny({ steps: [
    { id: 'key', label: 'key', at: 'a', kind: 'find', needs: [], built: 'planned' },
    { id: 'end', label: 'end', at: 'b', kind: 'goal', needs: [], built: 'planned' },
  ] }));
  assert.deepEqual(r.errors, ["end is at b, but what it needs doesn't get her there"]);
});

test('a key locked behind its own door can never be had', () => {
  const r = check(tiny({ steps: [
    { id: 'key', label: 'key', at: 'b', kind: 'find', needs: [], built: 'planned' },
    { id: 'end', label: 'end', at: 'b', kind: 'goal', needs: ['key'], built: 'planned' },
  ] }));
  assert.deepEqual(r.errors, [
    "key is at b, but what it needs doesn't get her there",
    'key can never be done',
    'end can never be done',
  ]);
});

test('a find nothing uses is flagged', () => {
  const r = check(tiny({ steps: [
    { id: 'key', label: 'key', at: 'a', kind: 'find', needs: [], built: 'planned' },
    { id: 'spare', label: 'spare', at: 'a', kind: 'find', needs: [], built: 'planned' },
    { id: 'end', label: 'end', at: 'b', kind: 'goal', needs: ['key'], built: 'planned' },
  ] }));
  assert.deepEqual(r.errors, []);
  assert.deepEqual(r.warnings, ['nothing needs spare: mark it optional or use it']);
  assert.deepEqual(r.open, [2, 2, 1]);
});
