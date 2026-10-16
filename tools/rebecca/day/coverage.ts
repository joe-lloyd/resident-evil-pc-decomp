// Can the player be seen wherever she can walk? For each half-metre cell of a
// day room's floor, take the camera whose floor holds it and check that her
// feet and head land on screen and that no foreground object hides her.
// Prints a map, X across and Z down: the camera's digit where it shows her,
// '!' where it loses her, '#' a wall; and the share of floor she is lost on.
//
//   node tools/rebecca/day/coverage.ts <slug> [renders dir]
//
// The renders dir defaults to day/<slug>/renders; a preview's will do
// (render.ts --preview writes room.json and the depth renders).
import { existsSync, readFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { autoFloors, badness, readDepth, type FloorScene, type Rect } from './floors.ts';
import { dayRooms } from './rooms.ts';

/** Worse than this, she is not properly seen: off screen, hidden, or a speck. */
const LOST = 2;

export function coverage(scene: FloorScene, floors: readonly (Rect | readonly Rect[])[], depths: readonly (Float32Array | undefined)[], step = 850) {
  const { bounds } = scene;
  let total = 0;
  let lost = 0;
  const rows: string[] = [];
  for (let z = bounds.z0 + step / 2; z < bounds.z1; z += step) {
    let row = '';
    for (let x = bounds.x0 + step / 2; x < bounds.x1; x += step) {
      if (scene.walls.some((w) => x >= w.x0 && x < w.x1 && z >= w.z0 && z < w.z1)) {
        row += '#';
        continue;
      }
      total++;
      const cam = floors.findIndex((f) => [f].flat().some((r) => x >= r.x0 && x < r.x1 && z >= r.z0 && z < r.z1));
      if (cam < 0 || badness(scene, cam, x, z, depths[cam]) > LOST) {
        lost++;
        row += '!';
      } else {
        row += String(cam);
      }
    }
    rows.push(row);
  }
  return { lost: total ? lost / total : 0, map: rows.join('\n') };
}

if (process.argv[1] === fileURLToPath(import.meta.url)) {
  const [slug, dir] = process.argv.slice(2);
  const spec = dayRooms.find((r) => r.slug === slug);
  if (!spec) throw new Error(`no day room ${slug}`);
  const renders = dir ?? path.join(path.dirname(fileURLToPath(import.meta.url)), slug, 'renders');
  const json = JSON.parse(readFileSync(path.join(renders, 'room.json'), 'utf8')) as FloorScene & { voids?: Rect[] };
  const scene: FloorScene = { ...json, walls: [...json.walls, ...(json.voids ?? [])] };
  const depths = scene.cameras.map((_, i) => {
    const f = path.join(renders, `cam${i}.depth.png`);
    return existsSync(f) ? readDepth(f) : undefined;
  });
  const floors = spec.cameraFloor === 'auto' ? autoFloors(scene, depths) : spec.cameraFloor;
  const { lost, map } = coverage(scene, floors, depths);
  console.log(map);
  console.log(`${slug}: ${floors.map((f, i) => `camera ${i} ${[f].flat().length} rects`).join(', ')}`);
  console.log(`${slug}: she is lost on ${(lost * 100).toFixed(1)}% of the floor`);
}
