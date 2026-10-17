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
import { CUT_FLAGS, CUTSCENES } from './cutscenes.ts';
import { pages } from './scripts.ts';

const here = path.dirname(fileURLToPath(import.meta.url));
const script = (room: string) => (room === 'save' ? path.join(here, '..', 'rooms', 'ROOM1000.c') : path.join(here, room, 'room.c'));

test("each scene's flag is set in its own room and used in no other", () => {
  const users = new Map<number, Set<string>>();
  const rooms = [...readdirSync(here).filter((d) => existsSync(script(d))), 'save'];
  for (const room of rooms) {
    for (const m of readFileSync(script(room), 'utf8').matchAll(/FG_COMMON, (\d+)/g)) {
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
