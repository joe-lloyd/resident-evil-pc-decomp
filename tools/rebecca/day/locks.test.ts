// node --test tools/rebecca/day/locks.test.ts
//
// The ways she opens with a tool, read from the generated room scripts: shut
// until she uses the tool on them from the lock's side, shut from the far
// side until then; and the action zones scripts.ts grows round what the
// scenes drew.
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { test } from 'node:test';
import { generous, GROW } from './scripts.ts';

const script = (room: string) => readFileSync(new URL(`./${room}/room.c`, import.meta.url), 'utf8');

/** The init lines from `if (ck(FG_LOCK, flag, 1)) {` to its closing brace, or undefined. */
function lockBlock(text: string, flag: number): string | undefined {
  const at = text.indexOf(`if (ck(FG_LOCK, ${flag}, 1)) {`);
  if (at < 0) return undefined;
  const end = text.indexOf('\n}\n', at);
  return text.slice(at, end + 2);
}

for (const { from, to, room, flag, item } of [
  { from: 'road', to: 'washout', room: 'ROOM_41A', flag: 43, item: 28 },
  { from: 'camp-yard', to: 'depot', room: 'ROOM_414', flag: 41, item: 28 },
  { from: 'creek', to: 'lodge', room: 'ROOM_21D', flag: 47, item: 43 },
]) {
  test(`${from} to ${to} opens only when she uses item ${item} on it there`, () => {
    const block = lockBlock(script(from), flag)!;
    const [shut, open] = block.split('} else {');
    // While the lock is on: her line, and the item can be used there. No door.
    assert.match(shut!, /SCE_MESSAGE/);
    assert.match(shut!, new RegExp(`SCE_USEITEM, 1, 9, 0, ${item - 27}, 0, 1, 0\\);`));
    assert.doesNotMatch(shut!, /door_aot_set/);
    assert.match(open!, new RegExp(`door_aot_set\\(.*${room}.*\\);`));
    // Using it raises the lock's flag, in main.
    const main = script(from).slice(script(from).indexOf('// main procedure'));
    assert.match(main, new RegExp(`testitem\\(${item}\\)[\\s\\S]*set\\(FG_LOCK, ${flag}, 0\\);`));
  });

  test(`${to} back to ${from} stays shut until the lock is open`, () => {
    const block = lockBlock(script(to), flag)!;
    const [shut, open] = block.split('} else {');
    assert.match(shut!, /SCE_MESSAGE/);
    assert.doesNotMatch(shut!, /door_aot_set/);
    assert.match(open!, /door_aot_set/);
  });
}

test('the bolt cutters leave her case after the second of their two locks', () => {
  // Cutting the road gate takes them only if the depot is open, and the other way round.
  assert.match(script('road'), /set\(FG_LOCK, 43, 0\);\n\s+if \(ck\(FG_LOCK, 41, 0\)\) \{\n\s+if \(item_ck\(28\)\) \{\n\s+remove_item\(28\);/);
  assert.match(script('camp-yard'), /set\(FG_LOCK, 41, 0\);\n\s+if \(ck\(FG_LOCK, 43, 0\)\) \{\n\s+if \(item_ck\(28\)\) \{\n\s+remove_item\(28\);/);
});

test("a key still turns as she tries the door, as RE1's do", () => {
  assert.match(script('camp-yard'), /\ndoor_aot_set\(\d+, [^;]*ROOM_412[^;]*, 58, 193\);/);
});

test('action zones grow by GROW, on each side only half way to the next zone there, and walks she leaves by on touch not at all', () => {
  const z = (x0: number, z0: number, x1: number, z1: number) => ({ x0, z0, x1, z1 });
  const kit = {
    doors: [
      { zone: z(0, 0, 1000, 600), touch: true },
      { zone: z(5000, 0, 6000, 600), touch: false },
    ],
    checks: [
      { zone: z(2000, 3000, 2600, 3600) },
      { zone: z(2900, 3000, 3500, 3600) },
      { zone: z(9000, 9000, 9600, 9600) },
    ],
  };
  const out = generous(kit, (d) => d.touch);
  assert.equal(GROW, 510);
  assert.deepEqual(out.doors!.map((d) => d.zone), [z(0, 0, 1000, 600), z(4490, 0, 6510, 1110)]);
  assert.deepEqual(out.checks!.map((c) => c.zone), [z(1490, 2490, 2750, 4110), z(2750, 2490, 4010, 4110), z(8490, 8490, 10110, 10110)]);
});
