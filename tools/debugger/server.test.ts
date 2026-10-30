// The dashboard's change log, fed real state lines: no game needed.
//   node --test tools/debugger/server.test.ts
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { test } from 'node:test';
import { parseReply, type GameState } from '../harness/state.ts';
import { changes } from './server.ts';

const line = JSON.parse(readFileSync(new URL('../harness/fixtures/feedback/20261018-140506/note.json', import.meta.url), 'utf8')).state;

/** The fixture's state line with some of its fields replaced, parsed the way the server parses it. */
function state(patch: Record<string, unknown> = {}, player: Record<string, unknown> = {}): GameState {
  const reply = parseReply(JSON.stringify({ ...line, ...patch, player: { ...line.player, ...player } }));
  if (reply.t !== 'state') throw new Error('not a state line');
  return reply.state;
}
const texts = (a: GameState, b: GameState) => changes(a, b, { 2: 'beretta', 68: 'first aid spray' }).map((c) => `${c.level} ${c.text}`);
const banks = (bank: number, hex: string) => line.banks.map((b: string, i: number) => (i === bank ? hex : b));

test('nothing changed, nothing logged', () => {
  assert.deepEqual(texts(state(), state()), []);
});

test('a health drop in play is a hit; one while the room loads is not', () => {
  assert.deepEqual(texts(state(), state({}, { hp: 60 })), ['warn player hit: hp 85 -> 60']);
  assert.deepEqual(texts(state(), state({ play: 0 }, { hp: 0 })), ['info screen gameplay -> other']);
});

test('items she gains and loses are named', () => {
  const spray = state({ items: [[1, 1], [2, 15], [68, 1], [0, 0], [0, 0], [0, 0]] });
  assert.deepEqual(texts(state(), spray), ['info bag: got first aid spray']);
  assert.deepEqual(texts(spray, state()), ['info bag: lost first aid spray']);
});

test('script flags are logged by bank name and index, except the noisy message bank', () => {
  // roomItems is bank 7; its fixture word is 00000010 (flag 3 on, in the game's bit order: byte 0 bit 4).
  assert.deepEqual(texts(state(), state({ banks: banks(7, '00000000') })), ['info flag roomItems:3 off']);
  assert.deepEqual(texts(state(), state({ banks: banks(6, 'ffffffff') })), []);
});

test('a message coming up is logged with its id', () => {
  assert.deepEqual(texts(state(), state({ msg: { ...line.msg, choice: 0x80, id: 131 } })), ['info screen gameplay -> message', 'info message 131']);
});

test('a bank written whole, as a new game does, is one line', () => {
  assert.deepEqual(texts(state(), state({ banks: banks(7, 'ffffffff') })), ['info flags: 31 changed at once']);
});
