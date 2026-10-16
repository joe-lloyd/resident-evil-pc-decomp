// node --test tools/rebecca/day/flags.test.ts
//
// A pickup stays taken by its FG_ITEM flag, set when she takes it. Two
// pickups on one flag would take each other: these hold every room script of
// her day (day/<slug>/room.c) to one item per flag, in one room.
import assert from 'node:assert/strict';
import { existsSync, readdirSync, readFileSync } from 'node:fs';
import path from 'node:path';
import { test } from 'node:test';
import { fileURLToPath } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));

test('every item flag belongs to one pickup, in one room', () => {
  const owner = new Map<number, string>();
  const bad: string[] = [];
  for (const slug of readdirSync(here)) {
    const file = path.join(here, slug, 'room.c');
    if (!existsSync(file)) continue;
    for (const m of readFileSync(file, 'utf8').matchAll(/item_aot_set\(([^;]*)\);/g)) {
      const a = m[1]!.replace(/\/\*.*?\*\//g, '').split(',').map((t) => Number(t.trim()));
      // Operands: id, x, z, w, d, item, count, model, 255, six position bytes, two turn bytes, flag, ...
      const [item, flag] = [a[5]!, a[17]!];
      const who = `item ${item} in ${slug}`;
      const was = owner.get(flag);
      if (was && was !== who) bad.push(`FG_ITEM ${flag}: ${was} and ${who}`);
      owner.set(flag, who);
    }
  }
  assert.deepEqual(bad, []);
});
