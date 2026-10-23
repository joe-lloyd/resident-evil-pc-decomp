// node --test tools/rebecca/day/walkable.test.ts
//
// The check that holds her collision to what the cameras draw, on a room
// drawn here: a camera over a floor with a wall standing across it and a
// door in the wall, its depth of every surface traced the way Blender
// renders cam<N>.zall.png.
import assert from 'node:assert/strict';
import { test } from 'node:test';
import { FRAME_H, FRAME_W } from '../masks.ts';
import { check, KNEE_INSIDE, seenBy, unproject, type Camera, type RoomJson, type Script } from './walkable.ts';

type V3 = [number, number, number];
const cam: Camera = { from: [5000, -3400, 0], to: [5000, 0, 6000], fov: 200 };
/** The wall: x 0-10000 at z 8000-8200, 800 high; the floor beyond it ends at z 12000 (a drop). */
const WALL = { x0: 0, z0: 8000, x1: 10000, z1: 8200 };

/** The view depth of the first surface along each pixel's ray: the wall, the floor, or nothing. */
function zall(): Float32Array {
  const out = new Float32Array(FRAME_W * FRAME_H).fill(Infinity);
  for (let py = 0; py < FRAME_H; py++) {
    for (let px = 0; px < FRAME_W; px++) {
      // A point on the ray at view depth 1, and the ray from the eye through it.
      const p = unproject(cam, px, py, 1);
      const dir = p.map((v, k) => v - cam.from[k]!) as V3;
      let best = Infinity;
      // The wall's near face, z = 8000, up to 800 high.
      if (dir[2] > 0) {
        const t = (WALL.z0 - cam.from[2]) / dir[2];
        const y = cam.from[1] + t * dir[1];
        const x = cam.from[0] + t * dir[0];
        if (t > 0 && y <= 0 && y >= -800 && x >= WALL.x0 && x <= WALL.x1) best = t;
      }
      // The floor, y = 0, as far as z 12000.
      if (dir[1] > 0) {
        const t = -cam.from[1] / dir[1];
        const z = cam.from[2] + t * dir[2];
        if (t > 0 && t < best && z <= 12000) best = t;
      }
      out[py * FRAME_W + px] = best;
    }
  }
  return out;
}

const bounds = { x0: 1000, z0: 4000, x1: 9000, z1: 14000 };
const room = (walls: RoomJson['walls']): RoomJson => ({ cameras: [cam], bounds, walls });
/** She comes in at the south edge. */
const IN = { from: 'yard', x: 5000, z: 6000 };
const script = (zones: Script['zones'] = [], arrivals = [IN]): Script => ({ arrivals, zones });
const seen = [seenBy(cam, zall(), bounds, KNEE_INSIDE)];

test('floor her collision gives her inside a wall the camera draws is solid; beyond it, past the floor, there is none', () => {
  const r = check(room([]), seen, [bounds], script([], []));
  // The cells either side of the wall have it drawn through her; past z
  // 12000 the camera sees nothing where the floor would be.
  assert.deepEqual(r.cameras, [{ cells: 2365, solid: 215, hole: 430 }]);
});

test('with the wall and the drop walled off she stands only on floor the camera draws', () => {
  const r = check(room([{ ...WALL, shape: 'box' }, { x0: 0, z0: 12000, x1: 10000, z1: 14000 }]), seen, [bounds], script([], []));
  assert.deepEqual(r.cameras, [{ cells: 1591, solid: 0, hole: 0 }]);
});

test('a door that opens in a wall she can walk through is a way round it', () => {
  // The scene's walls leave a gap at x 4500-5500 behind the door.
  const walls = [
    { x0: 0, z0: 8000, x1: 4500, z1: 8200, shape: 'box' as const },
    { x0: 5500, z0: 8000, x1: 10000, z1: 8200, shape: 'box' as const },
  ];
  // The room ends at the wall: the floor beyond is the hut's.
  const hut = { ...room(walls), bounds: { ...bounds, z1: 9500 } };
  const door = script([{ what: 'the door to hut', zone: { x0: 4500, z0: 7400, x1: 5500, z1: 8000 }, at: 'her', door: 'hut' }]);
  assert.deepEqual(check(hut, seen, [bounds], door).doors, ['hut: she walks 300 units past it, to (5000, 8300)']);
  const shut = { ...room([{ ...WALL, shape: 'box' }]), bounds: { ...bounds, z1: 9500 } };
  assert.deepEqual(check(shut, seen, [bounds], door).doors, []);
});

test('an arrival inside a wall is listed', () => {
  const r = check(room([{ ...WALL, shape: 'box' }]), seen, [bounds], script([], [{ from: 'yard', x: 5000, z: 8100 }]));
  assert.deepEqual(r.arrivals, ['from yard at (5000, 8100)']);
});

test('a zone she cannot get within reach of is listed', () => {
  const zones: Script['zones'] = [
    { what: 'a boot beyond the wall', zone: { x0: 4800, z0: 13000, x1: 5200, z1: 13400 }, at: 'ahead' },
    { what: 'a poster on the far side', zone: { x0: 4800, z0: 8200, x1: 5200, z1: 8600 }, at: 'ahead' },
    { what: 'a shell case', zone: { x0: 4800, z0: 7000, x1: 5200, z1: 7400 }, at: 'ahead' },
    { what: 'a door in the wall she stands in', zone: { x0: 4800, z0: 8000, x1: 5200, z1: 8200 }, at: 'her' },
  ];
  const r = check(room([{ ...WALL, shape: 'box' }]), seen, [bounds], script(zones));
  assert.deepEqual(r.zones, ['a boot beyond the wall at (4800, 13000)-(5200, 13400), floor 5515 away', 'a door in the wall she stands in at (4800, 8000)-(5200, 8200), floor 515 away']);
});
