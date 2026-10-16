// node --test tools/rebecca/day/zones.test.ts
//
// The action button takes the first zone in a room's table that her probe
// lands in, so where two zones overlap only one of them works there. This
// holds the scenes' zones (day/<slug>/renders/room.json) to one rule: every
// zone keeps at least a quarter of its floor clear of the zones before it in
// the table.
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

const inside = (z: Zone, x: number, y: number) => x >= z.x0 && x < z.x1 && y >= z.z0 && y < z.z1;
/** The zones the action button can fire: doors that open (not the walks she leaves by on touch), checks, spots. */
function actionZones(j: Json): { name: string; zone: Zone }[] {
  return [
    ...(j.doors ?? []).filter((d) => d.walk === false && d.zone).map((d) => ({ name: `the door to ${d.to}`, zone: d.zone })),
    ...(j.checks ?? []).map((c) => ({ name: `"${c.text.slice(0, 30)}"`, zone: c.zone })),
    ...(j.spots ?? []).map((s) => ({ name: `the ${s.step} spot`, zone: s.zone })),
  ];
}

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

test("every room script's pickups and checks keep a quarter of their floor clear of the zones before them", () => {
  // room.json has no item pickups: they are written into room.c (scripts.ts,
  // and the hand-written rooms), in table order by aot id. A pickup must work
  // while it lies there, so it is held to every zone before it. A check or a
  // door is held only to the ones that stay: a pickup over it is gone once
  // taken (the key on the ore cart, then Hal). A check set again on the same
  // floor is the other half of a puzzle spot (its use, then its message). A
  // pickup never is, so it gets no such pass.
  type Aot = { id: number; pickup: boolean; name: string; zone: Zone };
  const bad: string[] = [];
  for (const slug of readdirSync(here)) {
    const file = path.join(here, slug, 'room.c');
    if (!existsSync(file)) continue;
    const zones: Aot[] = [];
    for (const m of readFileSync(file, 'utf8').replace(/\/\*.*?\*\//g, '').matchAll(/\b(door_aot_set|item_aot_set|aot_set)\(([^)]*)\)/g)) {
      const a = m[2]!.split(',').map((t) => t.trim());
      const [id, x, z, w, d] = a.slice(0, 5).map(Number) as [number, number, number, number, number];
      // The trigger byte: 0x80 is the action button (the rest fire on touch).
      const sat = Number(m[1] === 'door_aot_set' ? a.at(-1) : m[1] === 'aot_set' ? a[6] : a[18]);
      if (!(sat & 0x80)) continue;
      zones.push({ id, pickup: m[1] === 'item_aot_set', name: `${m[1]} ${id}`, zone: { x0: x, z0: z, x1: x + w, z1: z + d } });
    }
    const same = (p: Zone, q: Zone) => p.x0 === q.x0 && p.z0 === q.z0 && p.x1 === q.x1 && p.z1 === q.z1;
    for (const z of zones) {
      const before = zones.filter((o) => o.id < z.id && (z.pickup || !o.pickup));
      if (!z.pickup && before.some((o) => same(o.zone, z.zone))) continue;
      let own = 0;
      let count = 0;
      const step = 50;
      for (let x = z.zone.x0 + step / 2; x < z.zone.x1; x += step)
        for (let y = z.zone.z0 + step / 2; y < z.zone.z1; y += step) {
          count++;
          if (!before.some((o) => inside(o.zone, x, y))) own++;
        }
      if (count && own / count < 0.25) bad.push(`${slug}: ${z.name} works on ${Math.round((100 * own) / count)}% of its floor`);
    }
  }
  assert.deepEqual(bad, []);
});
