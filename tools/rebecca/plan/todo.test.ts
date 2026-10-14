// node --test tools/rebecca/plan/todo.test.ts
import assert from 'node:assert/strict';
import { test } from 'node:test';
import { day } from './day.ts';
import { sections, type Facts, type RoomFacts } from './todo.ts';

const room = (doors: string[], checks = 0): RoomFacts => ({ doors, checks, entry: false });
const find = (facts: Facts, id: string) => sections(day, facts).flatMap((s) => s.items).find((i) => i.id === id)!;

test('a room is done once its renders exist', () => {
  assert.equal(find({ rooms: new Map() }, 'room-woods').status, 'todo');
  assert.equal(find({ rooms: new Map([['woods', room([])]]) }, 'room-woods').status, 'done');
});

test('a walk-through path is done only when both scenes have their door', () => {
  const one = new Map([['tunnel', room(['junction'])], ['junction', room([])]]);
  assert.equal(find({ rooms: one }, 'link-tunnel-junction').status, 'todo');
  const both = new Map([['tunnel', room(['junction'])], ['junction', room(['tunnel'])]]);
  assert.equal(find({ rooms: both }, 'link-tunnel-junction').status, 'done');
});

test('a door that opens is under way, not done, once both scenes have it', () => {
  const both = new Map([['east-path', room(['cottage'])], ['cottage', room(['east-path'])]]);
  assert.equal(find({ rooms: both }, 'link-east-path-cottage').status, 'doing');
});

test('every item the plan finds has a row', () => {
  const rows = new Set(sections(day, { rooms: new Map() }).flatMap((s) => s.items.map((i) => i.id)));
  for (const s of day.steps.filter((x) => x.kind === 'find')) assert.ok(rows.has(`find-${s.id}`), s.id);
});
