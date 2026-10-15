// node --test tools/rebecca/day/look.test.ts
import assert from 'node:assert/strict';
import { test } from 'node:test';
import { look } from './look.ts';

const frame = (fill: (x: number, y: number) => [number, number, number]) => {
  const rgb = new Uint8Array(320 * 240 * 3);
  for (let y = 0; y < 240; y++) for (let x = 0; x < 320; x++) rgb.set(fill(x, y), (y * 320 + x) * 3);
  return { width: 320, height: 240, rgb };
};

test('strength 0 leaves a frame as it is', () => {
  const f = frame((x, y) => [x % 256, y, (x + y) % 256]);
  assert.deepEqual(look(f, 0).rgb, f.rgb);
});

test("a pixel's result depends only on its colour and place, so frames that differ in one patch still differ only there", () => {
  const base = frame((x, y) => [(x * 3) % 256, (y * 5) % 256, 90]);
  const patched = frame((x, y) => (x >= 100 && x < 116 && y >= 50 && y < 66 ? [200, 30, 30] : [(x * 3) % 256, (y * 5) % 256, 90]));
  const [a, b] = [look(base, 0.4).rgb, look(patched, 0.4).rgb];
  for (let y = 0; y < 240; y++)
    for (let x = 0; x < 320; x++) {
      const i = (y * 320 + x) * 3;
      const inside = x >= 100 && x < 116 && y >= 50 && y < 66;
      const same = a[i] === b[i] && a[i + 1] === b[i + 1] && a[i + 2] === b[i + 2];
      if (!inside) assert.ok(same, `pixel ${x},${y} changed outside the patch`);
    }
});

test('the tone: blacks crushed, the corners darker than the middle, and no grain on a flat frame', () => {
  const grey = look(frame(() => [128, 128, 128]), 0.4);
  const at = (x: number, y: number) => grey.rgb[(y * 320 + x) * 3 + 1]!;
  assert.ok(at(0, 0) < at(160, 120), 'a corner is darker than the middle');
  assert.equal(at(150, 110), at(170, 130), 'two points near the middle come out the same: no grain');
  const dark = look(frame(() => [6, 6, 6]), 0.4);
  assert.ok(dark.rgb[(120 * 320 + 160) * 3]! < 6, 'near black goes darker');
});
