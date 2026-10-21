// node --test tools/rebecca/day/cutscenes.test.ts
//
// The cutscenes as scripts.ts writes them into the rooms: each scene's
// once-only flag belongs to its room alone, and each line fits the message
// box, two lines on one page.
import assert from 'node:assert/strict';
import { existsSync, readdirSync, readFileSync } from 'node:fs';
import path from 'node:path';
import { test } from 'node:test';
import { fileURLToPath } from 'node:url';
import { CUTSCENES as PLANNED } from '../plan/todo.ts';
import { compileScene } from './cutscene.ts';
import { CUT_FLAGS, CUTSCENES } from './cutscenes.ts';
import { pages } from './scripts.ts';

const here = path.dirname(fileURLToPath(import.meta.url));
const script = (room: string) => (room === 'save' ? path.join(here, '..', 'rooms', 'ROOM1000.c') : path.join(here, room, 'room.c'));

// The room loads the models of the enemies its init procedure sets and of no
// others (room_set, src/game/RoomInit.cpp). An enemy() in a main or event
// procedure gets no model, and the game crashes drawing it: the yard's dog did,
// when cut-dog set it.
test('every enemy a room script sets is set by its init procedure', () => {
  const rooms = [...readdirSync(here).filter((d) => existsSync(script(d))), 'save'];
  const late: string[] = [];
  for (const room of rooms) {
    let part = 'init';
    for (const [i, line] of readFileSync(script(room), 'utf8').split('\n').entries()) {
      part = /^\/\/ (init|main|event) procedure \d+/.exec(line)?.[1] ?? part;
      if (part !== 'init' && /^\s*enemy\(/.test(line)) late.push(`${room}/room.c:${i + 1} (${part}): ${line.trim()}`);
    }
  }
  assert.deepEqual(late, []);
});

test("each scene's flag is set in its own room and set in no other", () => {
  const users = new Map<number, Set<string>>();
  const rooms = [...readdirSync(here).filter((d) => existsSync(script(d))), 'save'];
  for (const room of rooms) {
    for (const m of readFileSync(script(room), 'utf8').matchAll(/set\(FG_COMMON, (\d+), 0\)/g)) {
      const n = Number(m[1]);
      users.set(n, (users.get(n) ?? new Set()).add(room));
    }
  }
  const bad: string[] = [];
  for (const c of CUTSCENES) {
    const flag = CUT_FLAGS.get(c.id)!;
    const text = readFileSync(script(c.room), 'utf8');
    if (!text.includes(`set(FG_COMMON, ${flag}, 0);`)) bad.push(`${c.id}: ${c.room} never sets FG_COMMON ${flag}`);
    const others = [...(users.get(flag) ?? [])].filter((r) => r !== c.room);
    if (others.length) bad.push(`${c.id}: FG_COMMON ${flag} is also used in ${others.join(', ')}`);
  }
  assert.deepEqual(bad, []);
});

test('every line of a scene fits the message box: one page, two lines', () => {
  const long = CUTSCENES.flatMap((c) =>
    c.beats.flatMap((b) => {
      if (b.kind !== 'say') return [];
      const p = pages(b.text);
      return p.length === 1 && p[0]!.split('\\n').length <= 2 ? [] : [`${c.id}: ${b.text}`];
    }),
  );
  assert.deepEqual(long, []);
});


test('every planned cutscene has a script, with Chris included in the sleep scene', () => {
  const made = new Set([...CUTSCENES.map((c) => c.id), 'cut-chris']);
  assert.deepEqual(PLANNED.map(([id]) => id).filter((id) => !made.has(id)), []);
});

test('entry scenes wait for their story flags and for the previous scene to finish', () => {
  for (const id of ['cut-dog', 'cut-mine-chase', 'cut-credits']) {
    const c = CUTSCENES.find((s) => s.id === id)!;
    const result = compileScene(c, 0, CUT_FLAGS.get(id)!, {
      say: () => 128, freeAction: () => 0, freeBit: () => 12,
      itemAction: () => undefined, arrival: () => ({ x: 3315, z: 2805 }),
    });
    const main = result.main.join('\n');
    assert.ok(main.includes('ck(FG_STATUS, 15, 1)'));
    for (const r of c.requires!) assert.ok(main.includes(`ck(${r.bank}, ${r.flag}, ${r.set ? 0 : 1})`));
    if (id === 'cut-dog') {
      const event = result.event.join('\n');
      assert.ok(event.lastIndexOf('wait_voice();') < event.indexOf('enemy(2,'));
    }
  }
});
