// node --test tools/rebecca/npc/zombies.test.ts
// Builds the camp's dead from the player's own zombie models in RE1_BASE
// (default /tmp/re1-pc)/enemy, as build.ts does.
import assert from 'node:assert/strict';
import { existsSync, readdirSync, readFileSync } from 'node:fs';
import path from 'node:path';
import { test } from 'node:test';
import { readEmd, readTexture, section, type SectionName } from './emd.ts';
import { zombieModel, zombies } from './zombies.ts';

const enemy = path.join(process.env.RE1_BASE ?? '/tmp/re1-pc', 'enemy');
const files = existsSync(enemy) ? readdirSync(enemy) : [];
const find = (name: string) => files.find((f) => f.toLowerCase() === name.toLowerCase());
const skip = zombies.every((z) => find(z.model)) ? false : `needs the player's enemy/${zombies.map((z) => z.model).join(', ')} in ${enemy}`;

test('a logger is its zombie with only the texture changed: same size, same skeleton, mesh and animations', { skip }, () => {
  for (const z of zombies) {
    const file = new Uint8Array(readFileSync(path.join(enemy, find(z.model)!)));
    const out = zombieModel(file, z);
    assert.equal(out.length, file.length, z.slug);
    const [a, b] = [readEmd(file), readEmd(out)];
    for (const name of ['emr', 'edd', 'tmd'] as SectionName[]) assert.deepEqual(section(b, name), section(a, name), `${z.slug} ${name}`);
    assert.notDeepEqual(readTexture(section(b, 'tim')).pixels, readTexture(section(a, 'tim')).pixels, `${z.slug} texture`);
  }
});

test("the loggers are RE1's three zombie ids, each its own body", () => {
  assert.deepEqual(zombies.map((z) => [z.slug, z.entity, z.model]), [
    ['faller', 0, 'EM1100.EMD'],
    ['bucker', 1, 'EM1101.EMD'],
    ['rigger', 17, 'EM1111.EMD'],
  ]);
});
