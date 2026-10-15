// The person models' animation list: the idle swapped into entry 0.
import assert from 'node:assert/strict';
import { test } from 'node:test';
import { idleFirst } from './people.ts';

/** Three entries of 4 bytes each, entry n filled with n + 1. */
const list = () => Uint8Array.from([1, 1, 1, 1, 2, 2, 2, 2, 3, 3, 3, 3]);

test('the idle and entry 0 swap places, the rest untouched', () => {
  assert.deepEqual([...idleFirst(list(), 2)], [3, 3, 3, 3, 2, 2, 2, 2, 1, 1, 1, 1]);
});

test('a Node Buffer, as readFileSync gives, swaps the same and is left as it was', () => {
  // A Buffer's slice() is a view of its bytes, not a copy.
  const edd = Buffer.from(list());
  assert.deepEqual([...idleFirst(edd, 2)], [3, 3, 3, 3, 2, 2, 2, 2, 1, 1, 1, 1]);
  assert.deepEqual([...edd], [...list()]);
});
