// node --test tools/rebecca/masks.test.ts
import assert from 'node:assert/strict';
import { test } from 'node:test';
import { buildMasks, FRAME_H, FRAME_W, maskPakName } from './masks.ts';

/** A frame with a red box from (100, 50) to (180, 130) at 8 m, the rest open. */
function scene() {
  const rgb = new Uint8Array(FRAME_W * FRAME_H * 3).fill(40);
  const depth = new Float32Array(FRAME_W * FRAME_H).fill(Infinity);
  for (let y = 50; y < 130; y++) {
    for (let x = 100; x < 180; x++) {
      depth[y * FRAME_W + x] = 8000;
      rgb.set([200, 30, 30], (y * FRAME_W + x) * 3);
    }
  }
  return { background: { width: FRAME_W, height: FRAME_H, rgb }, depth };
}

test('the sprites cover exactly the foreground tiles, at depth Z / 16', () => {
  const { background, depth } = scene();
  const { sprites, block, pak } = buildMasks(background, depth);
  const covered = new Set<number>();
  for (const s of sprites) for (let y = s.y; y < s.y + s.h; y++) for (let x = s.x; x < s.x + s.w; x++) covered.add(y * FRAME_W + x);
  for (let y = 50; y < 130; y++) for (let x = 100; x < 180; x++) assert.ok(covered.has(y * FRAME_W + x), `(${x}, ${y}) uncovered`);
  assert.deepEqual([...new Set(sprites.map((s) => s.depth))], [500]);
  // 16-pixel tiles from x 96 to 191 and y 48 to 143: six rows of one merged sprite each.
  assert.deepEqual(sprites.map((s) => [s.x, s.y, s.w, s.h]), [48, 64, 80, 96, 112, 128].map((y) => [96, y, 96, 16]));
  const b = new DataView(block.buffer);
  assert.equal(b.getInt32(0, true), 1);
  assert.equal(b.getUint16(4, true), 6);
  assert.ok(pak && pak.length > 100);
});

test('a frame with nothing in front has an empty block and no pak', () => {
  const { background } = scene();
  const { block, pak } = buildMasks(background, new Float32Array(FRAME_W * FRAME_H).fill(Infinity));
  assert.deepEqual([...block], [0, 0, 0, 0]);
  assert.equal(pak, undefined);
});

test('pak names use the zero-based stage and the decimal room', () => {
  assert.equal(maskPakName(1, 3, 0), 'OSP01030.pak');
  assert.equal(maskPakName(2, 0x13, 1), 'OSP02191.pak');
});
