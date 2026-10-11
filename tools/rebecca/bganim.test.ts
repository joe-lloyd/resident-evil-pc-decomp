// node --test tools/rebecca/bganim.test.ts
import assert from 'node:assert/strict';
import { test } from 'node:test';
import type { Image } from '../harness/image.ts';
import { animFileName, buildAnim } from './bganim.ts';

const W = 320;
const H = 240;

function frame(paint?: (x: number, y: number) => [number, number, number] | undefined): Image {
  const rgb = new Uint8Array(W * H * 3).fill(64);
  if (paint) {
    for (let y = 0; y < H; y++) {
      for (let x = 0; x < W; x++) {
        const c = paint(x, y);
        if (c) rgb.set(c, (y * W + x) * 3);
      }
    }
  }
  return { width: W, height: H, rgb };
}

/** A flame: a bright box at (100..110, 40..60) whose colour depends on the frame. */
const flame = (k: number) => frame((x, y) => (x >= 100 && x < 110 && y >= 40 && y < 60 ? [255, 120 + k * 40, 0] : undefined));

function parse(file: Uint8Array) {
  const v = new DataView(file.buffer, file.byteOffset, file.byteLength);
  let p = 4;
  const layers = [];
  const count = v.getUint16(p, true);
  p += 2;
  for (let i = 0; i < count; i++) {
    const head = { bank: file[p]!, bit: file[p + 1]!, value: file[p + 2]!, ticks: file[p + 3]!, frames: v.getUint16(p + 4, true) };
    p += 6;
    const frames = [];
    for (let f = 0; f < head.frames; f++) {
      const rects = [];
      const n = v.getUint16(p, true);
      p += 2;
      for (let r = 0; r < n; r++) {
        const rect = { x: v.getUint16(p, true), y: v.getUint16(p + 2, true), w: v.getUint16(p + 4, true), h: v.getUint16(p + 6, true) };
        p += 8;
        const first = v.getUint16(p, true);
        p += rect.w * rect.h * 2;
        rects.push({ ...rect, first });
      }
      frames.push(rects);
    }
    layers.push({ ...head, frames });
  }
  assert.equal(p, file.length, 'the file ends after its last layer');
  return { magic: String.fromCharCode(...file.subarray(0, 4)), layers };
}

test('a looping animation stores only the tiles that move, in every frame', () => {
  const file = buildAnim(flame(0), [{ frames: [flame(0), flame(1), flame(2)], ticks: 4 }])!;
  const { magic, layers } = parse(file);
  assert.equal(magic, 'RBA1');
  assert.equal(layers.length, 1);
  const [l] = layers;
  assert.deepEqual([l!.bank, l!.ticks, l!.frames.length], [0xff, 4, 3]);
  // x 100..110 is inside tile 6 (96..112); y 40..60 spans tiles 2 and 3 (32..64).
  for (const rects of l!.frames) assert.deepEqual(rects.map(({ x, y, w, h }) => ({ x, y, w, h })), [{ x: 96, y: 32, w: 16, h: 32 }]);
});

test('a change of state is one frame shown while its flag is set', () => {
  const cleared = frame((x, y) => (x >= 200 && y >= 200 ? [10, 80, 10] : undefined));
  const { layers } = parse(buildAnim(frame(), [{ frames: [cleared], ticks: 0, when: { bank: 1, bit: 210, value: true } }])!);
  assert.deepEqual([layers[0]!.bank, layers[0]!.bit, layers[0]!.value, layers[0]!.ticks], [1, 210, 1, 0]);
  const rect = layers[0]!.frames[0]![0]!;
  assert.deepEqual([rect.x, rect.y, rect.w, rect.h], [192, 192, 128, 48]);
});

test('render noise under the change threshold is not an animation', () => {
  const noisy = frame((x, y) => ((x + y) % 7 === 0 ? [66, 66, 66] : undefined));
  assert.equal(buildAnim(frame(), [{ frames: [frame(), noisy], ticks: 3 }]), undefined);
});

test('the file name matches the engine: stage, room in decimal, camera', () => {
  assert.equal(animFileName(2, 20, 1), 'ANM02201.dat');
});
