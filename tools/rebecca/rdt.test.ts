// node --test tools/rebecca/rdt.test.ts
import assert from 'node:assert/strict';
import { Buffer } from 'node:buffer';
import { test } from 'node:test';
import { scaleModel } from './rdt.ts';

test("scaling a model's mesh moves its vertices and nothing else", () => {
  // A TMD: id, flags 0, one object; the object's vertices start 28 bytes after the table.
  const tmd = new Uint8Array(12 + 28 + 16);
  const v = new DataView(tmd.buffer);
  v.setUint32(0, 0x41, true);
  v.setUint32(8, 1, true);
  v.setUint32(12, 28, true); // vertices at object table + 28
  v.setUint32(16, 2, true); // two of them
  const verts = [1440, -90, 1080, 7, 0, 51, -1080, 9];
  verts.forEach((n, i) => v.setInt16(40 + 2 * i, n, true));
  const tim = new Uint8Array([1, 2, 3]);
  const out = scaleModel({ tmd, tim }, 0.5);
  const got = Array.from({ length: 8 }, (_, i) => new DataView(out.tmd!.buffer).getInt16(40 + 2 * i, true));
  assert.deepEqual(got, [720, -45, 540, 7, 0, 26, -540, 9]);
  assert.equal(out.tim, tim);
  assert.equal(v.getInt16(40, true), 1440, 'the original is untouched');
});

test('a model read with Node scales the same: its Buffer is a view into a shared pool', () => {
  const tmd = new Uint8Array(12 + 28 + 8);
  const v = new DataView(tmd.buffer);
  v.setUint32(8, 1, true);
  v.setUint32(12, 28, true);
  v.setUint32(16, 1, true);
  v.setInt16(40, 1000, true);
  const pooled = Buffer.concat([Buffer.alloc(100), Buffer.from(tmd)]).subarray(100);
  const out = scaleModel({ tmd: pooled }, 0.5);
  assert.equal(new DataView(out.tmd!.buffer, out.tmd!.byteOffset).getInt16(40, true), 500);
});
