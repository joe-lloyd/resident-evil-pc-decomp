// Every door of her day puts her somewhere she can walk from: the spot it
// sets in the next room is not buried in that room's collision. The planner's
// walls are grown by her radius, so a spot just inside them is fine, as the
// game pushes her clear; one deeper than her radius leaves her stuck, as the
// yard's spot from the woods did (inside the cabin).
//
//   OVERLAY=<REB build folder> node tools/harness/tests/arrivals.ts
//
// Reads the built rooms; needs no game. Exits 1 if any door buries her.
import path from 'node:path';
import { blocked, loadShapes } from '../room-map.ts';
import { loadWorld } from '../world.ts';
import { dayRooms } from '../../rebecca/day/rooms.ts';

const overlay = process.env.OVERLAY;
if (!overlay) throw new Error('set OVERLAY to the REB build folder');
const dirs = [path.join(overlay, 'REB'), process.env.RE1_DATA ?? '/tmp/re1-pc'];
/** Deeper than this into the grown walls and she cannot move: room-map.ts's PLAYER_RADIUS. */
const DEPTH = 380;

let bad = 0;
for (const d of loadWorld().doors) {
  const r = d.to === 'save' ? { stage: 0, room: 0 } : dayRooms.find((x) => x.slug === d.to)!;
  const shapes = loadShapes(dirs, r.stage, r.room, 0x10);
  if (!blocked(shapes, d.arrive.x, d.arrive.z)) continue;
  let nearest = Infinity;
  for (let dx = -DEPTH; dx <= DEPTH; dx += 25) {
    for (let dz = -DEPTH; dz <= DEPTH; dz += 25) {
      if (!blocked(shapes, d.arrive.x + dx, d.arrive.z + dz)) nearest = Math.min(nearest, Math.hypot(dx, dz));
    }
  }
  if (nearest <= DEPTH) continue;
  bad++;
  console.log(`${d.from} > ${d.to}: puts her at (${d.arrive.x}, ${d.arrive.z}), more than ${DEPTH} inside the collision`);
}
console.log(bad ? `FAIL: ${bad} doors bury her` : 'every door puts her in the open');
process.exit(bad ? 1 : 0);
