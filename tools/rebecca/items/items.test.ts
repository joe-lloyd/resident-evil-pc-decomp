// node --test tools/rebecca/items/items.test.ts
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { test } from 'node:test';
import { day } from '../plan/day.ts';
import { engineSource, ENGINE_FILE } from './engine.ts';
import { KEY_ITEMS } from './items.ts';

test('RebItems.cpp is written from items.ts', () => {
  assert.equal(readFileSync(ENGINE_FILE, 'utf8'), engineSource(), 'run node tools/rebecca/items/engine.ts');
});

test('names fit as RE1 names do, descriptions in short lines', () => {
  for (const k of KEY_ITEMS) {
    assert.ok(k.name.length <= 15 && k.name === k.name.toUpperCase(), k.name);
    for (const line of k.description.split('\n')) assert.ok(line.length <= 26, `${k.name}: "${line}"`);
    assert.ok(k.description.split('\n').length <= 3, k.name);
  }
});

test('each takes a different RE1 item, none with a behaviour of its own', () => {
  const ids = KEY_ITEMS.map((k) => k.id);
  assert.equal(new Set(ids).size, ids.length);
  // The Sword Key (the save room still holds it), the books, the chemicals and the herbs.
  const kept = [0x33, 0x3e, 0x3f, 0x40, 0x15, 0x16, 0x17, 0x18, 0x19, 0x1a, 0x1b, 0x26, 0x43, 0x44, 0x45];
  for (const k of KEY_ITEMS) assert.ok(!kept.includes(k.id), `${k.name} takes 0x${k.id.toString(16)}`);
});

test('the items she uses at a spot can be: item-use flags start at item 27', () => {
  for (const step of ['crank', 'jerrycan', 'fuel', 'dynamite', 'cog', 'fuses', 'op-key']) {
    const k = KEY_ITEMS.find((i) => i.step === step)!;
    assert.ok(k.id >= 0x1b, `${k.name} is ${k.id}`);
  }
});

test('every key item is a step of the plan that finds it', () => {
  for (const k of KEY_ITEMS) {
    const step = day.steps.find((s) => s.id === k.step);
    assert.ok(step && step.kind === 'find', `${k.step} is a find step`);
  }
});
