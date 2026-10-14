// node --test tools/rebecca/npc/emd.test.ts
// Reads the player's own models from RE1_BASE (default /tmp/re1-pc): every
// .emd in enemy/, and Barry's and Rebecca's NPC models by name.
import assert from 'node:assert/strict';
import { existsSync, readdirSync, readFileSync } from 'node:fs';
import path from 'node:path';
import { test } from 'node:test';
import { pose, readAnimations, readEmd, readKeyframe, readMesh, readSkeleton, readTexture, restKeyframe, section, textureImage, withSection, writeEmd, writeTexture } from './emd.ts';
import { fitSkin } from './skin.ts';

const enemy = path.join(process.env.RE1_BASE ?? '/tmp/re1-pc', 'enemy');
const models = existsSync(enemy) ? readdirSync(enemy).filter((f) => /\.emd$/i.test(f)) : [];
const find = (name: string) => models.find((f) => f.toLowerCase() === name);
const read = (name: string) => new Uint8Array(readFileSync(path.join(enemy, find(name) ?? name)));
const skip = find('em1022.emd') && find('em1023.emd') ? false : `needs the player's enemy/EM1022.EMD and EM1023.EMD in ${enemy}`;

test('every model in the game writes back as the same bytes', { skip: models.length ? false : `no models in ${enemy}` }, () => {
  for (const f of models) {
    const file = new Uint8Array(readFileSync(path.join(enemy, f)));
    assert.deepEqual(writeEmd(readEmd(file)), file, f);
  }
  assert.ok(models.length >= 60, `read ${models.length} models`);
});

test('a texture written into a model reads back, and nothing else in the file moves', { skip }, () => {
  const file = read('em1022.emd');
  const emd = readEmd(file);
  const tim = section(emd, 'tim');
  const before = readTexture(tim);
  const pixels = before.pixels.map((p, i) => (p + i) & 0xff);
  const palettes = before.palettes.map((p, r) => p.map((c, i) => (c + i + r * 7) & 0x7fff));
  const out = writeEmd(withSection(emd, 'tim', writeTexture(tim, { palettes, pixels })));
  assert.equal(out.length, file.length);
  const after = readTexture(section(readEmd(out), 'tim'));
  assert.deepEqual(after.pixels, pixels);
  assert.deepEqual(after.palettes, palettes);
  const timAt = file.length - 20 - tim.length;
  assert.deepEqual(out.subarray(0, timAt + 20), file.subarray(0, timAt + 20), 'the sections before the texture and the TIM header');
  assert.deepEqual(out.subarray(-20), file.subarray(-20), 'the directory');
});

test("Barry's and Rebecca's models: 15 joints, their animations, a mesh object per joint", { skip }, () => {
  for (const [name, animations, objects] of [['em1022.emd', 59, 15], ['em1023.emd', 65, 16]] as const) {
    const emd = readEmd(read(name));
    const skeleton = readSkeleton(section(emd, 'emr'));
    assert.equal(skeleton.offsets.length, 15, name);
    assert.deepEqual(skeleton.parents, [-1, 0, 0, 2, 3, 4, 2, 6, 7, 0, 9, 10, 0, 12, 13], name);
    assert.equal(readAnimations(section(emd, 'edd')).length, animations, name);
    const mesh = readMesh(section(emd, 'tmd'));
    assert.equal(mesh.length, objects, name);
    // Each half of the sheet has its own palette row, and every polygon samples
    // the half whose row it names: so a skin can be fitted per half.
    for (const t of mesh.flatMap((o) => o.triangles)) assert.ok(t.uv.every(([u]) => (u < 128 ? 0 : 1) === t.row), `${name} polygon at 0x${t.at.toString(16)}`);
  }
});

test('posing: standing, the head is above the feet; a fall ends with the head on the floor', { skip }, () => {
  const emd = readEmd(read('em1022.emd'));
  const emr = section(emd, 'emr');
  const skeleton = readSkeleton(emr);
  const anims = readAnimations(section(emd, 'edd'));
  const head = (key: ReturnType<typeof restKeyframe>) => -pose(skeleton, key)[1]!.t[1];
  const foot = (key: ReturnType<typeof restKeyframe>) => -pose(skeleton, key)[5]!.t[1];
  const first = (a: number) => readKeyframe(emr, skeleton, anims[a]![0]!.keyframe);
  const last = (a: number) => readKeyframe(emr, skeleton, anims[a]!.at(-1)!.keyframe);
  assert.ok(head(restKeyframe(skeleton)) - foot(restKeyframe(skeleton)) > 2000, 'rest: about 1.5 m between head and foot');
  assert.ok(head(first(0)) > 2400, 'idle: standing');
  assert.ok(head(last(4)) < 100, 'animation 4 ends lying down');
});

test('a skin fits: each half keeps to 256 colours, and an image within them comes back exact', { skip }, () => {
  const texture = readTexture(section(readEmd(read('em1023.emd')), 'tim'));
  // An image of 300 greys left and 40 colours right: the left half has to be reduced.
  const rgb = new Uint8Array(256 * 256 * 3);
  for (let y = 0; y < 256; y++)
    for (let x = 0; x < 256; x++) {
      const i = (y * 256 + x) * 3;
      const v = x < 128 ? (y * 128 + x) % 300 : 8 * ((x + y) % 40);
      rgb.set(x < 128 ? [v % 256, Math.floor(v / 2), 255 - (v % 256)] : [v, 64, 128], i);
    }
  const fitted = fitSkin(texture, { width: 256, height: 256, rgb });
  const back = textureImage(fitted).rgb;
  let right = 0;
  for (let y = 0; y < 256; y++)
    for (let x = 128; x < 256; x++) {
      const i = (y * 256 + x) * 3;
      for (let k = 0; k < 3; k++) right = Math.max(right, Math.abs(back[i + k]! - rgb[i + k]!));
    }
  assert.ok(right <= 8, `the right half's 40 colours come back within a 5-bit step (off by ${right})`);
  assert.ok(new Set(fitted.pixels.filter((_, i) => i % 256 < 128)).size <= 256);
  assert.ok(!fitted.palettes.some((p, r) => [...fitted.pixels.keys()].some((i) => (i % 256 < 128 ? 0 : 1) === r && p[fitted.pixels[i]!] === 0)), 'no texel is see-through');
});

test("each person's model: our skin, their idle swapped into animation 0, and nothing else changes", { skip }, async () => {
  const { people, personModel } = await import('./people.ts');
  for (const person of people) {
    const file = read(person.model.toLowerCase());
    const out = personModel(file, person);
    assert.equal(out.length, file.length, person.slug);
    const [before, after] = [file, out].map((f) => readEmd(f));
    const anims = [before, after].map((e) => readAnimations(section(e!, 'edd')));
    assert.deepEqual(anims[1]![0], anims[0]![person.idle], `${person.slug}: animation 0 plays ${person.idle}`);
    assert.deepEqual(anims[1]![person.idle], anims[0]![0], `${person.slug}: the still pose moves to ${person.idle}`);
    assert.deepEqual(anims[1]!.filter((_, a) => a !== 0 && a !== person.idle), anims[0]!.filter((_, a) => a !== 0 && a !== person.idle), `${person.slug}: the other animations`);
    assert.deepEqual(section(after!, 'emr'), section(before!, 'emr'), `${person.slug}: the skeleton and keyframes`);
    // The mesh: the same vertices and triangles; only the moved parts sample elsewhere.
    const [was, now] = [before, after].map((e) => readMesh(section(e!, 'tmd')));
    now!.forEach((o, part) => {
      if (!person.reshape.some((r) => r.part === part)) assert.deepEqual(o.vertices, was![part]!.vertices, `${person.slug}: part ${part} keeps its shape`);
      o.triangles.forEach((t, k) => {
        const old = was![part]!.triangles[k]!;
        assert.deepEqual([t.vertices, t.normals], [old.vertices, old.normals]);
        assert.ok(t.uv.every(([u]) => (u < 128 ? 0 : 1) === t.row), `${person.slug}: part ${part} samples the half its palette row is for`);
        if (!person.ownIslands.some((i) => i.part === part)) assert.deepEqual(t.uv, old.uv, `${person.slug}: part ${part} keeps its UVs`);
      });
    });
    for (const { part } of person.ownIslands.filter((i) => i.apart === undefined)) {
      const mine = new Set(now![part]!.triangles.flatMap((t) => t.uv.map(([u, v]) => v * 256 + u)));
      const others = now!.flatMap((o, p) => (p === part ? [] : o.triangles.flatMap((t) => t.uv.map(([u, v]) => v * 256 + u))));
      assert.ok(!others.some((i) => mine.has(i)), `${person.slug}: part ${part} shares no UV corner with another part`);
    }
    assert.notDeepEqual(readTexture(section(after!, 'tim')).pixels, readTexture(section(before!, 'tim')).pixels, `${person.slug}: the texture is ours`);
  }
});
