// Her items' game models read back the way RE1's own do (tools/dump_ivm.py).
import assert from 'node:assert/strict';
import { test } from 'node:test';
import { itemPickup, itemView, parseItemMesh, readItemModel } from './tmd.ts';

/** A 256 x 256 texture: left half red, right half blue. */
function texture() {
  const rgb = new Uint8Array(256 * 256 * 3);
  for (let i = 0; i < 256 * 256; i++) rgb.set(i % 256 < 128 ? [200, 0, 0] : [0, 0, 200], i * 3);
  return { width: 256, height: 256, rgb };
}

/** One triangle facing up (+z in Blender), anticlockwise seen from above, as Blender exports it. */
const flat = parseItemMesh({
  step: 'test',
  view: [[[[0, 0, 0], [0, 0, 1], [0, 1]], [[0.1, 0, 0], [0, 0, 1], [1, 1]], [[0, 0.05, 0], [0, 0, 1], [0, 0]]]],
  pickup: [[[[0, 0, 0], [0, 0, 1], [0, 1]], [[0.1, 0, 0], [0, 0, 1], [1, 1]], [[0, 0.05, 0], [0, 0, 1], [0, 0]]]],
});

function readTmd(d: Uint8Array) {
  const v = new DataView(d.buffer, d.byteOffset, d.byteLength);
  const [vertTop, nVert, normalTop, , primTop, nPrim] = [0, 1, 2, 3, 4, 5].map((k) => v.getUint32(12 + k * 4, true));
  const vert = (i: number) => [0, 1, 2].map((k) => v.getInt16(12 + vertTop! + i * 8 + k * 2, true));
  const normal = (i: number) => [0, 1, 2].map((k) => v.getInt16(12 + normalTop! + i * 8 + k * 2, true));
  const prims = Array.from({ length: nPrim! }, (_, i) => {
    const at = 12 + primTop! + i * 28;
    const h = (k: number) => v.getUint16(at + 16 + k * 2, true);
    return {
      head: v.getUint32(at, true),
      cba: v.getUint16(at + 6, true),
      tsb: v.getUint16(at + 10, true),
      uv: [[d[at + 4], d[at + 5]], [d[at + 8], d[at + 9]], [d[at + 12], d[at + 13]]],
      corners: [0, 2, 4].map((k) => ({ n: normal(h(k)), v: vert(h(k + 1)) })),
    };
  });
  return { magic: v.getUint32(0, true), objects: v.getUint32(8, true), verts: Array.from({ length: nVert! }, (_, i) => vert(i)), prims };
}

function timParts(d: Uint8Array) {
  const v = new DataView(d.buffer, d.byteOffset, d.byteLength);
  const clutLen = v.getUint32(8, true);
  const clut = Array.from({ length: 256 }, (_, i) => v.getUint16(20 + i * 2, true));
  const at = 8 + clutLen;
  return { flags: v.getUint32(4, true), clutAt: [v.getUint16(12, true), v.getUint16(14, true)], size: [v.getUint16(at + 8, true) * 2, v.getUint16(at + 10, true)], clut, end: at + v.getUint32(at, true) };
}

test('a triangle comes out as RE1 writes them: mode 0x34, CLUT at row 480, wound against its normal, up as -y', () => {
  const { tmd } = itemPickup(flat, texture());
  const m = readTmd(tmd);
  assert.equal(m.magic, 0x41);
  assert.equal(m.objects, 1);
  const p = m.prims[0]!;
  assert.equal(p.head, 0x34000609);
  assert.equal(p.cba, 0x7800);
  assert.equal(p.tsb, 0x0080);
  const [a, b, c] = p.corners.map((k) => k.v);
  const e1 = b!.map((x, k) => x - a![k]!);
  const e2 = c!.map((x, k) => x - a![k]!);
  const cross = [e1[1]! * e2[2]! - e1[2]! * e2[1]!, e1[2]! * e2[0]! - e1[0]! * e2[2]!, e1[0]! * e2[1]! - e1[1]! * e2[0]!];
  const n = p.corners[0]!.n;
  assert.deepEqual(n, [0, -4096, 0]);
  assert.ok(cross.reduce((s, x, k) => s + x * n[k]!, 0) < 0);
  assert.deepEqual(m.verts.map((x) => x.join(' ')).sort(), ['0 0 0', '0 0 50', '100 0 0']);
  // The room's texture is 128 wide: u 1 is its last column; v 1 is the top row.
  assert.deepEqual(p.uv, [[0, 0], [0, 255], [127, 0]]);
});

test('the TIM is 8-bit with its CLUT at (0, 480) and no see-through colour', () => {
  const view = itemView(flat, texture());
  const t = timParts(view);
  assert.equal(t.flags, 9);
  assert.deepEqual(t.clutAt, [0, 480]);
  assert.deepEqual(t.size, [256, 256]);
  assert.ok(!t.clut.includes(0));
  assert.ok(t.clut.includes((200 >> 3) | 0), 'the red half');
  assert.ok(t.clut.includes((200 >> 3) << 10), 'the blue half');
  assert.equal(readTmd(view.subarray(t.end)).magic, 0x41);
});

test('the jerrycan examined is centred, stands 4800 units tall, its thinnest side across x, wound as RE1 winds', () => {
  const jerrycan = readItemModel('jerrycan');
  assert.ok(jerrycan, 'models/jerrycan.json: run render-items.ts');
  const view = itemView(jerrycan.mesh, jerrycan.texture);
  const m = readTmd(view.subarray(timParts(view).end));
  const span = [0, 1, 2].map((k) => [Math.min(...m.verts.map((p) => p[k]!)), Math.max(...m.verts.map((p) => p[k]!))]);
  for (const [lo, hi] of span) assert.ok(Math.abs(lo! + hi!) <= 2, `centred: ${lo} ${hi}`);
  const [x, y, z] = span.map(([lo, hi]) => hi! - lo!);
  // 165 mm deep, 345 wide, 540 tall with its handles: it stands, its height up
  // the screen (y), its depth along the viewer's x, its width across (z).
  assert.equal(y, 4800);
  assert.ok(x! < z! && z! < y!, `${x} < ${z} < ${y}`);
  const outward = m.prims.filter((p) => {
    const [a, b, c] = p.corners.map((k) => k.v);
    const e1 = b!.map((v, k) => v - a![k]!);
    const e2 = c!.map((v, k) => v - a![k]!);
    const cross = [e1[1]! * e2[2]! - e1[2]! * e2[1]!, e1[2]! * e2[0]! - e1[0]! * e2[2]!, e1[0]! * e2[1]! - e1[1]! * e2[0]!];
    const n = p.corners.map((k) => k.n).reduce((s, v) => s.map((x, k) => x + v[k]!));
    return cross.reduce((s, x, k) => s + x * n[k]!, 0) > 0;
  });
  // Decimation leaves a sliver or two whose normals disagree with their face.
  assert.ok(outward.length <= m.prims.length / 50, `${outward.length} of ${m.prims.length} wound the wrong way`);
});
