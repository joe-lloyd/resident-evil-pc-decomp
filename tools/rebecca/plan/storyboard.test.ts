// node --test tools/rebecca/plan/storyboard.test.ts
import assert from 'node:assert/strict';
import { test } from 'node:test';
import { readFileSync } from 'node:fs';
import { day } from './day.ts';
import { dayRooms } from '../day/rooms.ts';
import { CUTSCENES } from '../day/cutscenes.ts';
import { SUPPLIES, SUPPLY_KINDS } from '../day/supplies.ts';
import { DOCUMENTS } from '../files/documents.ts';
import { MAP_ITEMS } from './maps.ts';
import { buildStoryboard, renderStoryboard } from './storyboard.ts';

const board = buildStoryboard();

test('every place appears once as a scene and a route card', () => {
  assert.deepEqual(board.scenes.map((s) => s.place.id), day.places.map((p) => p.id));
  const html = renderStoryboard(board);
  for (const p of day.places) {
    assert.equal(html.split(`id="scene-${p.id}"`).length - 1, 1, p.id);
    assert.equal(html.split(`data-card="${p.id}"`).length - 1, 1, p.id);
  }
});

test('every standalone entry thought appears in the audit', () => {
  const expected: string[] = [];
  for (const r of dayRooms) {
    const script = readFileSync(new URL(`../day/${r.slug}/room.c`, import.meta.url), 'utf8');
    if (/message\(128,\s*255,\s*0\)/.test(script) && !CUTSCENES.some((c) => c.room === r.slug && c.trigger.on === 'enter')) expected.push(r.slug);
  }
  assert.deepEqual(board.audit.map((a) => a.slug).sort(), expected.sort());
  const html = renderStoryboard(board);
  for (const a of board.audit) {
    assert.ok(a.text.length > 0, a.slug);
    assert.ok(html.includes(`data-audit="${a.room}"`), a.slug);
  }
});

test('supply quantities, file and map totals match their source tables', () => {
  for (const act of day.acts) {
    const slugs = new Set(day.places.filter((p) => p.act === act.n).map((p) => p.room ?? p.id));
    const expected = Object.entries(SUPPLIES).filter(([slug]) => slugs.has(slug)).flatMap(([, kinds]) => kinds);
    const actual = board.items.filter((i) => i.act === act.n && i.source === 'supplies');
    assert.equal(actual.length, expected.length);
    assert.equal(actual.reduce((n, i) => n + i.qty, 0), expected.reduce((n, k) => n + SUPPLY_KINDS[k].qty, 0));
    assert.equal(board.balance.find((b) => b.act === act.n)?.rounds, board.items.filter((i) => i.act === act.n && i.placed && (i.kind === 'ammo' || i.kind === 'weapon')).reduce((n, i) => n + i.rounds, 0));
  }
  assert.equal(board.items.filter((i) => i.kind === 'file').length, DOCUMENTS.length);
  assert.equal(board.items.filter((i) => i.kind === 'map').length, MAP_ITEMS.length);
  assert.equal(board.items.filter((i) => i.room === 'cabin' && i.kind === 'heal').length, 1);
  assert.equal(board.items.filter((i) => i.room === 'cabin' && i.kind === 'ribbons').reduce((n, i) => n + i.qty, 0), 3);
});

test('the audit excludes entry cutscenes and includes the hand-written cabin', () => {
  assert.ok(board.audit.some((a) => a.room === 'cabin' && a.text.includes('The door isn\'t locked.')));
  for (const room of ['ridge', 'woods', 'gallery', 'crash', 'save']) assert.ok(!board.audit.some((a) => a.room === room), room);
});

test('the tracker exposes unwritten scenes, an unmapped reward and missing art', () => {
  for (const id of ['cut-credits', 'cut-dog', 'cut-mine-chase']) assert.ok(board.missing.some((m) => m.detail.includes(id)), id);
  assert.ok(!board.missing.some((m) => m.detail.includes('cut-chris')), 'Chris is written inside cut-sleep');
  assert.ok(board.missing.some((m) => m.room === 'mast' && m.detail.includes('supplies has no matching pickup step')));
  assert.ok(board.missing.some((m) => m.room === 'save' && m.title.startsWith('Render')));
});

test('starting kit, loaded gun and hand-written enemy spawns enter the balance', () => {
  assert.deepEqual(board.balance.map((b) => [b.act, b.rounds, b.enemies]), [[1, 30, 8], [2, 60, 36], [3, 45, 11], [4, 15, 1]]);
  assert.equal(board.items.find((i) => i.room === 'crash' && i.kind === 'weapon')?.rounds, 15);
  assert.equal(board.items.find((i) => i.room === 'cabin' && i.kind === 'ribbons')?.name, 'Ink ribbons');
});
