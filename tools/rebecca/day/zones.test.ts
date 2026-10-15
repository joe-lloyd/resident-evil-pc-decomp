// node --test tools/rebecca/day/zones.test.ts
//
// The action button takes the first zone in a room's table that her probe
// lands in, so where two zones overlap only one of them works there. These
// hold the scenes' zones (day/<slug>/renders/room.json) to two rules: a save
// room's typewriter and box overlap nothing, and every zone keeps at least a
// quarter of its floor clear of the zones before it in the table.
import assert from 'node:assert/strict';
import { existsSync, readdirSync, readFileSync } from 'node:fs';
import path from 'node:path';
import { test } from 'node:test';
import { fileURLToPath } from 'node:url';

type Zone = { x0: number; z0: number; x1: number; z1: number };
interface Json {
  doors?: { to: string; zone: Zone; walk?: boolean }[];
  checks?: { zone: Zone; text: string }[];
  spots?: { step: string; zone: Zone }[];
  /** The cabin's record has only its lid: its zones are in its hand-written room.c. */
  saves?: { typewriter?: Zone; box?: Zone } | null;
}
const here = path.dirname(fileURLToPath(import.meta.url));
const rooms = readdirSync(here).flatMap((slug) => {
  const file = path.join(here, slug, 'renders', 'room.json');
  return existsSync(file) ? [{ slug, json: JSON.parse(readFileSync(file, 'utf8')) as Json }] : [];
});

const overlap = (a: Zone, b: Zone) => a.x0 < b.x1 && b.x0 < a.x1 && a.z0 < b.z1 && b.z0 < a.z1;
const inside = (z: Zone, x: number, y: number) => x >= z.x0 && x < z.x1 && y >= z.z0 && y < z.z1;
/** The zones the action button can fire: doors that open (not the walks she leaves by on touch), checks, spots. */
function actionZones(j: Json): { name: string; zone: Zone }[] {
  return [
    ...(j.doors ?? []).filter((d) => d.walk === false && d.zone).map((d) => ({ name: `the door to ${d.to}`, zone: d.zone })),
    ...(j.checks ?? []).map((c) => ({ name: `"${c.text.slice(0, 30)}"`, zone: c.zone })),
    ...(j.spots ?? []).map((s) => ({ name: `the ${s.step} spot`, zone: s.zone })),
  ];
}

test("a save room's typewriter and box overlap no other zone", () => {
  const bad: string[] = [];
  for (const { slug, json } of rooms) {
    const { typewriter, box } = json.saves ?? {};
    if (!typewriter || !box) continue;
    for (const [what, z] of [['typewriter', typewriter], ['box', box]] as const) {
      for (const o of actionZones(json)) if (overlap(z, o.zone)) bad.push(`${slug}: the ${what} overlaps ${o.name}`);
    }
    if (overlap(typewriter, box)) bad.push(`${slug}: the typewriter overlaps the box`);
  }
  assert.deepEqual(bad, []);
});

test('every zone keeps a quarter of its floor clear of the zones before it', () => {
  // The table's order (day/scripts.ts): doors, the typewriter and box, the
  // checks, then the spots. A zone works only where no earlier one covers it.
  const bad: string[] = [];
  for (const { slug, json } of rooms) {
    const { typewriter, box } = json.saves ?? {};
    const all = actionZones(json);
    const zones = [
      ...all.filter((z) => z.name.startsWith('the door')),
      ...(typewriter && box ? [{ name: 'the typewriter', zone: typewriter }, { name: 'the box', zone: box }] : []),
      ...all.filter((z) => z.name.startsWith('"')),
      ...all.filter((z) => z.name.endsWith(' spot')),
    ];
    zones.forEach((z, i) => {
      let own = 0;
      let count = 0;
      const step = 50;
      for (let x = z.zone.x0 + step / 2; x < z.zone.x1; x += step)
        for (let y = z.zone.z0 + step / 2; y < z.zone.z1; y += step) {
          count++;
          if (!zones.slice(0, i).some((o) => inside(o.zone, x, y))) own++;
        }
      if (count && own / count < 0.25) bad.push(`${slug}: ${z.name} works on ${Math.round((100 * own) / count)}% of its floor`);
    });
  }
  assert.deepEqual(bad, []);
});
