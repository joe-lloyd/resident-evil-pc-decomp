// node --test tools/rebecca/maps/maps.test.ts
//
// Her map screen's files and tables, as the engine reads them: the pictures in
// RE1's map format, every room drawn in its own palette block, the overview's
// stages and sprites inside its picture, a visited bit for every room, and a
// pickup for every map in the room the plan puts it.
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import path from 'node:path';
import { test } from 'node:test';
import { fileURLToPath } from 'node:url';
import { dayRooms } from '../day/rooms.ts';
import { day } from '../plan/day.ts';
import { AREAS, MAP_ITEMS, STAGES } from '../plan/maps.ts';
import { blockOf, FILL, MAP_SHOWN } from './draw.ts';
import { ENGINE_FILE, engineSource } from './engine.ts';
import { areaFile, mapFiles, STAGE_FILES } from './files.ts';
import { ARROWS, BASE_H, BASE_W, LABEL_H, LABEL_W, OV_H, OV_W, overview } from './overview.ts';
import { mapIn } from './pickups.ts';
import { planArea } from './plans.ts';
import { mapRooms } from './tables.ts';
import { decodeTim8 } from './tim.ts';

const dayDir = path.join(path.dirname(fileURLToPath(import.meta.url)), '..', 'day');

test('every area map is a 128 x 128 8-bit TIM the size of RE1s, with every room drawn in its own palette block', () => {
  const files = new Map(mapFiles().map((f) => [f.name, f.bytes]));
  const bad: string[] = [];
  AREAS.forEach((a, i) => {
    const bytes = files.get(areaFile(i))!;
    // map_display_load_textures reads the CLUT at 0x14 and the pixels at 0x220.
    if (bytes.length !== 16928) bad.push(`${a.id}: ${bytes.length} bytes, RE1's are 16928`);
    const t = decodeTim8(bytes);
    if (t.width !== 128 || t.height !== 128) bad.push(`${a.id}: ${t.width} x ${t.height}`);
    const used = new Set(t.pixels.subarray(0, 128 * MAP_SHOWN));
    a.places.forEach((p, k) => {
      if (!used.has(blockOf(k) + FILL)) bad.push(`${a.id}: ${p} has no floor drawn`);
    });
    for (const index of used) if (index >= blockOf(a.places.length)) bad.push(`${a.id}: index ${index} is past its rooms' blocks`);
  });
  assert.deepEqual(bad, []);
});

test('no two rooms of an area are drawn over each other', () => {
  assert.deepEqual(
    AREAS.flatMap((a) => planArea(a.id).overlaps.map((o) => `${a.id}: ${o}`)),
    [],
  );
});

test("the overview's four stages show more of the mountain each", () => {
  const files = new Map(mapFiles().map((f) => [f.name, f.bytes]));
  const stages = STAGE_FILES.map((f) => decodeTim8(files.get(f)!));
  const base = (t: (typeof stages)[number]) => Array.from({ length: BASE_H }, (_, y) => t.pixels.subarray(y * OV_W, y * OV_W + BASE_W)).flatMap((r) => [...r]);
  for (let s = 1; s < stages.length; s++) {
    const changed = base(stages[s]!).filter((v, i) => v !== base(stages[s - 1]!)[i]).length;
    assert.ok(changed > 20, `stage ${s + 1} adds ${changed} pixels to stage ${s}'s mountain`);
  }
  assert.equal(stages.length, STAGES.length);
  assert.ok(stages.every((t) => t.width === OV_W && t.height === OV_H));
});

test("the overview's cut-outs, names and arrows each have their own part of its picture", () => {
  const o = overview();
  const parts = [
    { name: 'the mountain', u: 0, v: 0, w: BASE_W, h: BASE_H },
    { name: 'the arrows', u: ARROWS.u, v: ARROWS.v, w: 32, h: 8 },
    ...o.markers.map((m, i) => ({ name: `${STAGES[i]!.name}'s cut-out`, u: m.u, v: m.v, w: m.at.w, h: m.at.h })),
    ...o.labels.map((l, i) => ({ name: `${AREAS[i]!.name}'s name`, u: l.u, v: l.v, w: LABEL_W, h: LABEL_H })),
  ];
  const bad: string[] = [];
  for (const [i, a] of parts.entries()) {
    if (a.u + a.w > OV_W || a.v + a.h > OV_H) bad.push(`${a.name} runs off the picture`);
    for (const b of parts.slice(i + 1)) if (a.u < b.u + b.w && b.u < a.u + a.w && a.v < b.v + b.h && b.v < a.v + a.h) bad.push(`${a.name} overlaps ${b.name}`);
  }
  assert.deepEqual(bad, []);
});

test('every room of her day has a place on one map and a visited bit of its own, below the maps', () => {
  const rooms = mapRooms();
  assert.equal(rooms.length, day.places.length);
  const key = (r: { stage: number; room: number }) => `${r.stage}:${r.room}`;
  assert.equal(new Set(rooms.map(key)).size, rooms.length);
  assert.equal(new Set(rooms.map((r) => r.bit)).size, rooms.length);
  assert.ok(rooms.every((r) => r.bit < 0x7c));
  for (const r of dayRooms) assert.ok(rooms.some((m) => key(m) === key(r)), `${r.slug} is on no map`);
});

test('RebMaps.cpp is what engine.ts writes', () => {
  assert.equal(readFileSync(ENGINE_FILE, 'utf8'), engineSource());
});

test('each map lies in the room the plan finds it in, on a flag of its own', () => {
  const flags = new Set<number>();
  for (const m of MAP_ITEMS) {
    const step = day.steps.find((s) => s.id === m.step)!;
    const slug = day.places.find((p) => p.id === step.at)?.room ?? step.at;
    const item = mapIn(slug);
    assert.ok(item, `${m.id}: no map in ${slug}`);
    const script = readFileSync(path.join(dayDir, slug, 'room.c'), 'utf8');
    const pickup = new RegExp(`item_aot_set\\(\\d+(?:, \\d+){4}, ${item.id}\\b[^;]*, ${item.flag}, 129, 0, 0\\);`).exec(script);
    assert.ok(pickup, `${slug}/room.c has no pickup of item ${item.id} on FG_ITEM ${item.flag}`);
    flags.add(item.flag);
  }
  assert.equal(flags.size, MAP_ITEMS.length);
});

