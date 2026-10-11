// node --test tools/rebecca/new_room.test.ts
// Reads the built room back the way the engine reads it: the switch-zone
// table through a port of is_entity_in_switch_zone (Room.cpp), the collision
// block through the quadrant and box tests (RoomCollision.cpp), and checks
// what the composer (rdt.ts) keeps of the donor. Needs the player's
// ROOM3000.RDT: RE1_DATA, default /tmp/re1-pc.
import assert from 'node:assert/strict';
import { existsSync, readFileSync, readdirSync } from 'node:fs';
import path from 'node:path';
import { test } from 'node:test';
import { buildRoomRdt, parseScene } from './new_room.ts';

const dataRoot = process.env.RE1_DATA ?? '/tmp/re1-pc';
const sceneSource = readFileSync(new URL('./blender/mountain_trail.py', import.meta.url), 'utf8');
const stage3 = existsSync(dataRoot) ? readdirSync(dataRoot).find((d) => d.toLowerCase() === 'stage3') : undefined;
const templatePath = stage3 && path.join(dataRoot, stage3, 'ROOM3000.RDT');
const skip = templatePath && existsSync(templatePath) ? false : 'no ROOM3000.RDT under RE1_DATA';

const scene = parseScene(sceneSource);
const PLAYER_RADIUS = 200;

function load(): { template: Uint8Array; room: Uint8Array; view: DataView } {
  const template = Uint8Array.from(readFileSync(templatePath as string));
  const room = buildRoomRdt(template, scene);
  return { template, room, view: new DataView(room.buffer, room.byteOffset, room.byteLength) };
}

/** is_entity_in_switch_zone: four edge tests over zero-extended corners. */
function inZone(view: DataView, at: number, x: number, z: number): boolean {
  const c = (n: number) => view.getUint16(at + 4 + n * 2, true);
  const [x0, y0, x1, y1, x2, y2, x3, y3] = [c(0), c(1), c(2), c(3), c(4), c(5), c(6), c(7)];
  const dx = x - x0;
  const dz = z - y0;
  if ((x1 - x0) * dz > (y1 - y0) * dx) return false;
  if ((x3 - x0) * dz < (y3 - y0) * dx) return false;
  const dx2 = x - x2;
  const dz2 = z - y2;
  if ((x1 - x2) * dz2 < (y1 - y2) * dx2) return false;
  if ((x3 - x2) * dz2 > (y3 - y2) * dx2) return false;
  return true;
}

/** The camera the engine would cut to from `camera` with the player at (x, z), or undefined. */
function cutFrom(view: DataView, camera: number, x: number, z: number): number | undefined {
  let at = view.getUint32(0x48, true);
  while (view.getUint16(at + 2, true) !== camera) at += 20; // display_room_camera_bg
  for (at += 20; view.getUint16(at + 2, true) === camera; at += 20) {
    if (inZone(view, at, x, z)) return view.getUint16(at, true);
  }
  return undefined;
}

function headerContains(view: DataView, camera: number, x: number, z: number): boolean {
  let at = view.getUint32(0x48, true);
  while (view.getUint16(at + 2, true) !== camera) at += 20;
  return inZone(view, at, x, z);
}

/** check_room_collision's lookup: a point is blocked when it is inside a blocking box grown by the radius. */
function blocked(view: DataView, x: number, z: number): boolean {
  const at = view.getUint32(0x4c, true);
  const cellX = view.getInt16(at, true);
  const cellZ = view.getInt16(at + 2, true);
  const quadrant = (x < cellX ? 1 : 0) | (z < cellZ ? 2 : 0);
  let first = 0;
  for (let q = 0; q < quadrant; q++) first += view.getInt32(at + 4 + q * 4, true);
  const count = view.getInt32(at + 4 + quadrant * 4, true);
  for (let i = first; i < first + count; i++) {
    const r = at + 0x18 + i * 12;
    // Zero-extended, as boundary_classify reads them.
    const [xMax, zMax, xMin, zMin] = [view.getUint16(r, true), view.getUint16(r + 2, true), view.getUint16(r + 4, true), view.getUint16(r + 6, true)];
    const inside = x >= xMin - PLAYER_RADIUS && x <= xMax + PLAYER_RADIUS && z >= zMin - PLAYER_RADIUS && z <= zMax + PLAYER_RADIUS;
    if (inside && (view.getUint16(r + 10, true) & 0x100) !== 0) return true;
  }
  return false;
}

test('the scene gives two cameras and the trail extent', () => {
  assert.equal(scene.cameras.length, 2);
  assert.deepEqual(scene.trailX, [2000, 5000]);
  assert.deepEqual(scene.trailZ, [0, 16000]);
  assert.equal(scene.cameras[0].fov, 250);
});

test('camera records, counts and empty masks', { skip }, () => {
  const { room, view } = load();
  assert.equal(room[1], 2);
  assert.equal(room[0], 0);
  scene.cameras.forEach((camera, i) => {
    const at = 0x94 + i * 0x2c;
    assert.deepEqual(
      [8, 12, 16, 20, 24, 28, 32, 36, 40].map((o) => view.getInt32(at + o, true)),
      [camera.from.x, camera.from.y, camera.from.z, camera.to.x, camera.to.y, camera.to.z, 0, 0, camera.fov],
    );
    assert.equal(view.getInt32(view.getUint32(at, true), true), 0, `camera ${i} mask group count`);
  });
});

test('the donor sections it keeps are byte for byte the donor\'s, and snd.vb is last', { skip }, () => {
  const { template, room, view } = load();
  const tv = new DataView(template.buffer, template.byteOffset, template.byteLength);
  const slot = (v: DataView, s: number) => v.getUint32(0x48 + 4 * s, true);
  // Every pointer lands inside the file.
  for (let s = 0; s < 19; s++) assert.ok(slot(view, s) < room.length, `slot ${s} points past the end`);
  // Kept sections: the event table, the player animations, the effects and the sound bank.
  for (const s of [8, 9, 10, 13, 16, 17, 18]) {
    const from = slot(tv, s);
    const to = slot(view, s);
    assert.ok(to, `slot ${s} was dropped`);
    assert.deepEqual(room.subarray(to, to + 64), template.subarray(from, from + 64), `slot ${s} bytes`);
  }
  // The effect tables name the same effect data as the donor's.
  for (const s of [14, 15]) {
    for (let i = 0; i < 8; i++) {
      const was = tv.getUint32(slot(tv, s) - 4 * i, true);
      const now = view.getUint32(slot(view, s) - 4 * i, true);
      if (was === 0xffffffff) assert.equal(now, was);
      else assert.deepEqual(room.subarray(now, now + 32), template.subarray(was, was + 32), `effect table ${s} entry ${i}`);
    }
  }
  // snd.vb is the last section, whole: the engine loads models over it.
  const vb = slot(view, 18);
  assert.ok(room.length - vb > 100_000, `snd.vb is ${room.length - vb} bytes`);
  assert.deepEqual(room.subarray(vb), template.subarray(slot(tv, 18), slot(tv, 18) + room.length - vb));
  // Dead donor data is gone: the room is far smaller than its donor.
  assert.ok(room.length < template.length / 2, `${room.length} bytes from a ${template.length}-byte donor`);
});

test('camera 0 cuts to camera 1 below Z 8000 and camera 1 cuts back above it', { skip }, () => {
  const { view } = load();
  for (const x of [2000, 3500, 5000]) {
    assert.equal(cutFrom(view, 0, x, 1000), undefined);
    assert.equal(cutFrom(view, 0, x, 7999), undefined);
    assert.equal(cutFrom(view, 0, x, 8000), 1);
    assert.equal(cutFrom(view, 0, x, 15500), 1);
    assert.equal(cutFrom(view, 1, x, 15500), undefined);
    assert.equal(cutFrom(view, 1, x, 8000), undefined);
    assert.equal(cutFrom(view, 1, x, 7999), 0);
    assert.equal(cutFrom(view, 1, x, 1000), 0);
  }
});

test('each camera header covers the whole trail', { skip }, () => {
  const { view } = load();
  for (const camera of [0, 1]) {
    for (const z of [0, 1000, 8000, 15500, 16000]) assert.ok(headerContains(view, camera, 3500, z), `camera ${camera} at z ${z}`);
    assert.ok(!headerContains(view, camera, 3500, 30000));
  }
});

test('the trail is walkable and its edges are walls', { skip }, () => {
  const { view } = load();
  for (const z of [0 + PLAYER_RADIUS + 100, 1000, 8000, 15000]) {
    for (const x of [2000 + PLAYER_RADIUS + 100, 3500, 5000 - PLAYER_RADIUS - 100]) assert.equal(blocked(view, x, z), false, `(${x}, ${z})`);
  }
  assert.equal(blocked(view, 1800, 4000), true);
  assert.equal(blocked(view, 5200, 12000), true);
  assert.equal(blocked(view, 3500, 0), true);
  assert.equal(blocked(view, 3500, 150), true);
  assert.equal(blocked(view, 3500, 16100), true);
});

test('the main script is one procedure holding return', { skip }, () => {
  const { room, view } = load();
  const main = view.getUint32(0x64, true);
  assert.deepEqual([...room.subarray(main, main + 6)], [4, 0, 0, 0, 0, 0]);
});
