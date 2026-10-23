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
import { blockOf, drawArea, FILL, MAP_SHOWN, MAP_W } from './draw.ts';
import { floors, SIDES, UNITS } from './floors.ts';
import { buildingFloor, CELL, inOutline, isFloor, organic, outlineOf } from './outline.ts';
import { ENGINE_FILE, engineSource } from './engine.ts';
import { areaFile, mapFiles, STAGE_FILES } from './files.ts';
import { ARROWS, BASE_H, BASE_W, LABEL_H, LABEL_W, OV_H, OV_W, overview } from './overview.ts';
import { mapIn } from './pickups.ts';
import { doorInPlan, DOOR_REACH, inRoom, planArea } from './plans.ts';
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

test('outdoors and underground, a room is drawn round every spot she can stand on and every door she leaves by', () => {
  const missed: string[] = [];
  for (const f of floors().values()) {
    if (!organic(f)) continue;
    const o = outlineOf(f);
    let n = 0;
    const b = f.bounds;
    // Her collision grid, every 10 cm (day/walkable.ts).
    for (let z = b.z0; z <= b.z1; z += 170) for (let x = b.x0; x <= b.x1; x += 170) if (isFloor(f, x, z) && !inOutline(o, x / UNITS, z / UNITS)) n++;
    if (n) missed.push(`${f.place}: ${n} spots outside its outline`);
  }
  assert.deepEqual(missed, []);
});

test('outdoors and underground a room is a free shape; a building keeps its straight walls', () => {
  const boxy: string[] = [];
  for (const f of floors().values()) {
    const o = outlineOf(f);
    let on = 0;
    let [i0, j0, i1, j1] = [Infinity, Infinity, -1, -1];
    for (let j = 0; j < o.rows; j++)
      for (let i = 0; i < o.cols; i++) {
        if (!o.cells[j * o.cols + i]) continue;
        on++;
        [i0, j0, i1, j1] = [Math.min(i0, i), Math.min(j0, j), Math.max(i1, i), Math.max(j1, j)];
      }
    const fill = on / ((i1 - i0 + 1) * (j1 - j0 + 1));
    // A free shape leaves part of its bounding box empty. The woods and the
    // valley path are walkable nearly to their bounds once she steps over
    // debris (#32), so they fill about 93%; a box fills 100%.
    if (organic(f) && fill > 0.95) boxy.push(`${f.place} fills ${(fill * 100).toFixed(0)}% of its box`);
    if (!organic(f)) {
      // A building's outline is its floor, cell for cell.
      let off = 0;
      for (let j = 0; j < o.rows; j++)
        for (let i = 0; i < o.cols; i++) {
          const x = (o.x0 + (i + 0.5) * CELL) * UNITS;
          const z = (o.y0 + (j + 0.5) * CELL) * UNITS;
          if (Number(buildingFloor(f, x, z)) !== o.cells[j * o.cols + i]) off++;
        }
      if (off) boxy.push(`${f.place}: ${off} cells off its floor`);
    }
  }
  assert.deepEqual(boxy, []);
});

test("every door is drawn on its room's outline, or where it stands when it is out in the floor", () => {
  const bad: string[] = [];
  for (const a of AREAS) {
    const d = drawArea(a.id);
    for (const r of d.plan.rooms) {
      const k = a.places.indexOf(r.floor.place);
      for (const door of r.floor.doors) {
        const at = d.doors.find((x) => x.place === r.floor.place && x.to === door.to);
        if (!at) {
          bad.push(`${a.id}: ${r.floor.place}'s door to ${door.to} is not drawn`);
          continue;
        }
        if (d.owner[at.y * MAP_W + at.x] !== k) bad.push(`${a.id}: ${r.floor.place}'s door to ${door.to} is off its room`);
        // A door with floor DOOR_REACH past it stands out in the room (a tower's in its clearing), drawn where it is.
        const { at: face, side } = doorInPlan(r, door);
        const [sx, sy] = SIDES[side]!;
        const out = inRoom(r, { x: face.x + sx! * DOOR_REACH, y: face.y + sy! * DOOR_REACH });
        const edge = [
          [1, 0],
          [-1, 0],
          [0, 1],
          [0, -1],
        ].some(([dx, dy]) => {
          const [x, y] = [at.x + dx!, at.y + dy!];
          return x < 0 || y < 0 || x >= MAP_W || y >= MAP_SHOWN || d.owner[y * MAP_W + x] !== k;
        });
        if (!out && !edge) bad.push(`${a.id}: ${r.floor.place}'s door to ${door.to} is not on its outline`);
      }
    }
  }
  assert.deepEqual(bad, []);
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

