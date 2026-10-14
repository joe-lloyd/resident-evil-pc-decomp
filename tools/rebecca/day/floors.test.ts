// node --test tools/rebecca/day/floors.test.ts
import assert from 'node:assert/strict';
import { test } from 'node:test';
import { project } from './floors.ts';

// Blender renders game x east, game z as its y and game -y as its z. A camera
// looking north (game -z) then has game west on its right: the platform's
// first camera, looking south-east, shows the booth to its north-east on the
// right of cam0.png.
test('a point east of a camera looking north lands left of centre, as in the render', () => {
  const cam = { from: [0, -1700, 10000] as [number, number, number], to: [0, -1700, 0] as [number, number, number], fov: 200 };
  const east = project(cam, [2000, -1700, 5000])!;
  const west = project(cam, [-2000, -1700, 5000])!;
  assert.equal(Math.round(east.x), 80);
  assert.equal(Math.round(west.x), 240);
});

test('the booth shows on the right of the platform camera that looks south-east', () => {
  const cam = { from: [5440, -6460, 1360] as [number, number, number], to: [17850, -340, 17000] as [number, number, number], fov: 200 };
  // The booth's middle, a metre up: x 14.1 m, z 3.8 m.
  assert.ok(project(cam, [23970, -1700, 6460])!.x > 280);
});
