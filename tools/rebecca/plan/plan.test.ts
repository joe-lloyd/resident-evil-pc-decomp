// node --test tools/rebecca/plan/plan.test.ts
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { test } from 'node:test';
import { dayRooms } from '../day/rooms.ts';
import { day } from './day.ts';
import { check, type Plan } from './plan.ts';
import { checkMaps } from './maps.ts';
import { checkMusic } from './music.ts';
import { checkSaves, SAVES } from './saves.ts';
import { CUTSCENES } from './todo.ts';

test("Rebecca's day can be played through to her credits", () => {
  const r = check(day);
  assert.deepEqual(r.errors, []);
  assert.deepEqual(r.warnings, []);
  assert.equal(r.order.at(-1), 'credits');
  assert.equal(day.places.length, 58);
});

const tiny = (over: Partial<Plan>): Plan => ({
  title: 'tiny',
  start: 'a',
  acts: [{ n: 1, title: '', time: '', summary: '' }],
  places: [
    { id: 'a', name: 'A', built: 'planned', act: 1, cameras: 1, at: [0, 0], there: '', moves: '', enemies: '', story: '' },
    { id: 'b', name: 'B', built: 'planned', act: 1, cameras: 1, at: [1, 0], there: '', moves: '', enemies: '', story: '' },
  ],
  links: [{ from: 'a', to: 'b', kind: 'door', opens: 'key' }],
  steps: [
    { id: 'key', label: 'key', at: 'a', act: 1, kind: 'find', needs: [], built: 'planned' },
    { id: 'end', label: 'end', at: 'b', act: 1, kind: 'goal', needs: ['key'], built: 'planned' },
  ],
  ...over,
});

test('a step behind a lock its needs do not open is an error', () => {
  const r = check(tiny({ steps: [
    { id: 'key', label: 'key', at: 'a', act: 1, kind: 'find', needs: [], built: 'planned' },
    { id: 'end', label: 'end', at: 'b', act: 1, kind: 'goal', needs: [], built: 'planned' },
  ] }));
  assert.deepEqual(r.errors, ["end is at b, but what it needs doesn't get her there"]);
});

test('a key locked behind its own door can never be had', () => {
  const r = check(tiny({ steps: [
    { id: 'key', label: 'key', at: 'b', act: 1, kind: 'find', needs: [], built: 'planned' },
    { id: 'end', label: 'end', at: 'b', act: 1, kind: 'goal', needs: ['key'], built: 'planned' },
  ] }));
  assert.deepEqual(r.errors, [
    "key is at b, but what it needs doesn't get her there",
    'key can never be done',
    'end can never be done',
  ]);
});

test('a find nothing uses is flagged', () => {
  const r = check(tiny({ steps: [
    { id: 'key', label: 'key', at: 'a', act: 1, kind: 'find', needs: [], built: 'planned' },
    { id: 'spare', label: 'spare', at: 'a', act: 1, kind: 'find', needs: [], built: 'planned' },
    { id: 'end', label: 'end', at: 'b', act: 1, kind: 'goal', needs: ['key'], built: 'planned' },
  ] }));
  assert.deepEqual(r.errors, []);
  assert.deepEqual(r.warnings, ['nothing needs spare: mark it optional or use it']);
  assert.deepEqual(r.open, [2, 2, 1]);
});

test('every room is on one map, and each map is a step she can take', () => {
  assert.deepEqual(checkMaps(day), []);
});

test('every room and cutscene has its music decided, within RE1\'s three channels', () => {
  assert.deepEqual(checkMusic(day, CUTSCENES.map(([id]) => id)), []);
});

test('save rooms are as rare and as near as RE1 places its own, quiet, with the save room music', () => {
  assert.deepEqual(checkSaves(day), []);
});

test("the save screen names a save by her save room's place", () => {
  // The engine's table of her save rooms: { stage, room, name }, // place.
  const cpp = readFileSync(new URL('../../../src/game/SaveLoadScreen.cpp', import.meta.url), 'utf8');
  const table = [...cpp.matchAll(/\{ (\d+), 0x([0-9A-F]{2}), s_rebLoc\w+ \},\s*\/\/ ([\w-]+)/g)].map(([, stage, room, place]) => `${place} ${stage} ${parseInt(room!, 16)}`);
  const want = SAVES.map((s) => {
    const folder = day.places.find((p) => p.id === s.place)?.room ?? s.place;
    const r = dayRooms.find((d) => d.slug === folder);
    return `${s.place} ${r?.stage} ${r?.room}`;
  });
  assert.deepEqual(table.sort(), want.sort());
});
