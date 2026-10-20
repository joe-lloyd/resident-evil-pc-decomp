import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { test } from 'node:test';
import { GEAR, BAG_SLOTS } from './gear.ts';
import { KEY_ITEMS } from '../items/items.ts';
import { CUTSCENES } from './cutscenes.ts';

const script = (room: string) => readFileSync(new URL(`./${room}/room.c`, import.meta.url), 'utf8');

test('the late loss keeps the original Beretta id, its loaded count and every key item', () => {
  const types = readFileSync(new URL('../../../src/game/Types.h', import.meta.url), 'utf8');
  assert.match(types, /#define ITEM_BERETTA\s+0x02/);
  assert.ok(!GEAR.includes(0x02));
  assert.ok(KEY_ITEMS.every((it) => !GEAR.includes(it.id)));
  for (const id of [1, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 65, 67, 68, 69, 70, 71, 72, 73, 74, 75]) assert.ok(GEAR.includes(id), `item ${id}`);
  const text = script('crawl');
  assert.ok(!text.includes('remove_item(2);'));
  for (const id of GEAR) assert.equal(text.split(`remove_item(${id});`).length - 1, BAG_SLOTS);
});

test('the gallery removes no gear and the late scene spans the crawl before the hatch', () => {
  assert.ok(!script('gallery').includes('remove_item('));
  const scene = CUTSCENES.find((s) => s.id === 'cut-leave-gear')!;
  assert.equal(scene.room, 'crawl');
  assert.equal(scene.trigger.on, 'zone');
  const floor = JSON.parse(readFileSync(new URL('./crawl/renders/room.json', import.meta.url), 'utf8'));
  const door = floor.doors.find((d: { to: string }) => d.to === 'save');
  if (scene.trigger.on === 'zone') {
    assert.equal(scene.trigger.zone.x1, floor.bounds.x1);
    assert.ok(scene.trigger.zone.x0 <= 10880);
    assert.ok(scene.trigger.zone.z0 > door.zone.z1);
  }
});
