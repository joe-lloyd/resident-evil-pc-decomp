// node --test tools/rebecca/arms.test.ts
// Reads the player's own files from RE1_BASE (default /tmp/re1-pc, the build's
// input): enemy/CHAR11.EMD, enemy/CHAR13.EMD and players/W31, W33, W34.EMW.
import assert from 'node:assert/strict';
import { existsSync, readFileSync } from 'node:fs';
import path from 'node:path';
import { test } from 'node:test';
import { buildArms, emdSections, emwMesh, texel, texelIndex, tmdPolys, type Poly } from './arms.ts';

const base = process.env.RE1_BASE ?? '/tmp/re1-pc';
const files = ['enemy/CHAR11.EMD', 'enemy/CHAR13.EMD', 'players/W31.EMW', 'players/W32.EMW', 'players/W33.EMW', 'players/W34.EMW'];
const missing = files.filter((f) => !existsSync(path.join(base, f)));
const read = (f: string) => new Uint8Array(readFileSync(path.join(base, f)));
const skip = missing.length ? `needs the player's ${missing.join(', ')} in ${base}` : false;

/** Points inside each triangle of a polygon, as the GPU interpolates them: weights for corners a, b, c. */
const WEIGHTS = [
  [0.34, 0.33, 0.33],
  [0.61, 0.23, 0.16],
  [0.17, 0.62, 0.21],
  [0.22, 0.14, 0.64],
  [0.81, 0.11, 0.08],
  [0.09, 0.83, 0.08],
  [0.07, 0.12, 0.81],
];
function samples(p: Poly): [number, number][] {
  const c = p.uv.map(([u, v]) => [u + (p.tsb & 0xf) * 128, v] as const);
  const tris = c.length === 4 ? [[0, 1, 2], [1, 3, 2]] : [[0, 1, 2]];
  return tris.flatMap((t) => WEIGHTS.map((w) => [0, 1].map((k) => w.reduce((sum, wi, i) => sum + wi * c[t[i]!]![k]!, 0)) as [number, number]));
}

/** A fine grid of points inside each triangle of a polygon, for the texels it can sample. */
function dense(p: Poly): [number, number][] {
  const c = p.uv.map(([u, v]) => [u + (p.tsb & 0xf) * 128, v] as const);
  const tris = c.length === 4 ? [[0, 1, 2], [1, 3, 2]] : [[0, 1, 2]];
  const out: [number, number][] = [];
  for (const t of tris)
    for (let a = 0; a <= 20; a++)
      for (let b = 0; a + b <= 20; b++) {
        const w = [a / 20, b / 20, (20 - a - b) / 20];
        out.push([0, 1].map((k) => Math.min(255, Math.floor(w.reduce((sum, wi, i) => sum + wi * c[t[i]!]![k]!, 0)))) as [number, number]);
      }
  return out;
}

test('her body and her Beretta keep every colour they had', { skip }, () => {
  const rebecca = read('enemy/CHAR13.EMD');
  const beretta = read('players/W32.EMW');
  const arms = buildArms(read('enemy/CHAR11.EMD'), rebecca, ['W31', 'W33', 'W34'].map((w) => ({ file: read(`players/${w}.EMW`) })), [beretta]);
  for (const p of [...tmdPolys(rebecca, emdSections(rebecca).mesh), ...tmdPolys(beretta, emwMesh(beretta))]) {
    const row = (p.cba - 0x7800) >> 6;
    for (const [x, y] of dense(p)) assert.equal(texel(arms.rebecca, row, x, y), texel(rebecca, row, x, y), `body texel ${x},${y}`);
  }
});

test("each gun polygon shows on her sheet what it showed on Jill's, and each hand polygon lands on her own hand", { skip }, () => {
  const jill = read('enemy/CHAR11.EMD');
  const rebecca = read('enemy/CHAR13.EMD');
  const weapons = ['W31', 'W33', 'W34'].map((w) => read(`players/${w}.EMW`));
  const arms = buildArms(jill, rebecca, weapons.map((file) => ({ file })), [read('players/W32.EMW')]);
  const hand = new Set(
    tmdPolys(rebecca, emdSections(rebecca).mesh)
      .filter((p) => p.object === 14)
      .flatMap((p) => dense(p).flatMap(([x, y]) => [-1, 0, 1].flatMap((dy) => [-1, 0, 1].map((dx) => (y + dy) * 256 + x + dx)))),
  );
  let gun = 0;
  let onHand = 0;
  weapons.forEach((before, i) => {
    const after = arms.weapons[i]!;
    const was = tmdPolys(before, emwMesh(before));
    const now = tmdPolys(after, emwMesh(after));
    assert.equal(now.length, was.length);
    now.forEach((p, k) => {
      if (p.cba === 0x7800) {
        for (const [x, y] of samples(p)) assert.ok(hand.has(Math.floor(y) * 256 + Math.floor(x)), `weapon ${i} polygon ${k} samples off her hand at ${x},${y}`);
        onHand++;
        return;
      }
      assert.equal(p.cba, 0x7840, 'a gun polygon is on her second palette row');
      const old = samples(was[k]!);
      samples(p).forEach(([x, y], t) => {
        const [ox, oy] = old[t]!;
        // A point exactly on a texel edge can round either way once turned.
        if ([x, y, ox, oy].some((n) => Math.abs(n - Math.round(n)) < 1e-6)) return;
        assert.equal(texel(arms.rebecca, 1, Math.floor(x), Math.floor(y)), texel(jill, 0, Math.floor(ox), Math.floor(oy)), `weapon ${i} polygon ${k}`);
      });
      // See-through stays see-through at each corner: the engine draws only entry 0 clear.
      p.uv.forEach(([u, v], c) => {
        const [ou, ov] = was[k]!.uv[c]!;
        const clear = texelIndex(jill, ou + (was[k]!.tsb & 0xf) * 128, ov) === 0;
        assert.equal(texelIndex(arms.rebecca, u + (p.tsb & 0xf) * 128, v) === 0, clear, `weapon ${i} polygon ${k} corner ${c}: transparency`);
      });
      gun++;
    });
  });
  assert.deepEqual({ gun, onHand }, { gun: 154, onHand: 22 });
});

test('only texture fields change, and no file changes size', { skip }, () => {
  const rebecca = read('enemy/CHAR13.EMD');
  const w33 = read('players/W33.EMW');
  const arms = buildArms(read('enemy/CHAR11.EMD'), rebecca, [{ file: w33 }]);
  assert.equal(arms.rebecca.length, rebecca.length);
  assert.equal(arms.weapons[0]!.length, w33.length);
  const tim = emdSections(rebecca).tim;
  for (let i = 0; i < tim; i++) assert.equal(arms.rebecca[i], rebecca[i], `model byte 0x${i.toString(16)} before the texture`);
  const textureFields = new Set(tmdPolys(w33, emwMesh(w33)).flatMap((p) => Array.from({ length: p.uv.length * 4 }, (_, j) => p.at + 4 + j)));
  w33.forEach((b, i) => {
    if (!textureFields.has(i)) assert.equal(arms.weapons[0]![i], b, `weapon byte 0x${i.toString(16)}`);
  });
});

test('the files passed in come back unchanged, Buffers included, as build.ts passes them', { skip }, () => {
  // readFileSync gives Buffers, whose slice() is a view, not a copy.
  const buf = (f: string) => readFileSync(path.join(base, f));
  const jill = buf('enemy/CHAR11.EMD');
  const rebecca = buf('enemy/CHAR13.EMD');
  const weapons = ['W31', 'W33', 'W34'].map((w) => buf(`players/${w}.EMW`));
  const before = [jill, rebecca, ...weapons].map((b) => Buffer.from(b));
  buildArms(jill, rebecca, weapons.map((file) => ({ file })), [buf('players/W32.EMW')]);
  [jill, rebecca, ...weapons].forEach((b, i) => assert.ok(b.equals(before[i]!), `input ${i} was changed`));
});
