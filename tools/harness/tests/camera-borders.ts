// At camera borders, a small step back and forth should not flip the camera.
// RE1 leaves a gap between the trigger into a camera and the trigger back out
// (rebecca/day/camera-zones.ts); this walks it in the game.
//
// For each border of each room named, read from the deployed overlay's room
// file: stand her well inside one camera's area, walk her at the other until
// the camera cuts, then sway a few steps back and forth there with tank
// controls, the way a player hesitates in a doorway. Every cut during the
// sway is a flicker.
//
//   OVERLAY=<REB build folder, as deployed> node tools/harness/tests/camera-borders.ts [slug ...]
//
// Needs the lab variables (lab.ts). Exits 1 if any border flickers.
import { readFileSync } from 'node:fs';
import path from 'node:path';
import { open } from '../lab.ts';
import { Key, type GameLink } from '../link.ts';
import { blocked, loadShapes, type Shape } from '../room-map.ts';
import { settle } from '../flows.ts';
import { dayRooms } from '../../rebecca/day/rooms.ts';
import { inQuad, type Quad } from '../../rebecca/day/camera-zones.ts';

type Trigger = { from: number; to: number; quad: Quad };

/** The switch-zone table at RDT+0x48: groups by camFrom, each opening with a header that is not tested. */
function triggers(rdt: Buffer): Trigger[] {
  const cameras = rdt.readUInt8(1);
  const out: Trigger[] = [];
  let group = -1;
  for (let at = rdt.readUInt32LE(0x48); at + 20 <= rdt.length; at += 20) {
    const to = rdt.readUInt16LE(at);
    const from = rdt.readUInt16LE(at + 2);
    if (from >= cameras) break;
    if (from !== group) {
      group = from;
      continue;
    }
    const p = (i: number) => [rdt.readUInt16LE(at + 4 + i * 4), rdt.readUInt16LE(at + 6 + i * 4)] as const;
    out.push({ from, to, quad: [p(0), p(1), p(2), p(3)] });
  }
  return out;
}

/** A point of the quad she can stand on, nearest `toward`; undefined if the floor misses it. */
function standIn(q: Quad, shapes: Shape[], toward: readonly [number, number]): [number, number] | undefined {
  const xs = q.map((p) => p[0]);
  const zs = q.map((p) => p[1]);
  let best: [number, number] | undefined;
  for (let x = Math.min(...xs); x <= Math.max(...xs); x += 250) {
    for (let z = Math.min(...zs); z <= Math.max(...zs); z += 250) {
      if (!inQuad(q, x, z) || blocked(shapes, x, z, 500)) continue;
      if (!best || Math.hypot(x - toward[0], z - toward[1]) < Math.hypot(best[0] - toward[0], best[1] - toward[1])) best = [x, z];
    }
  }
  return best;
}

const middle = (q: Quad) => [(q[0][0] + q[1][0] + q[2][0] + q[3][0]) / 4, (q[0][1] + q[1][1] + q[2][1] + q[3][1]) / 4] as const;
/** Game angle facing from a to b: she walks along (cos a, -sin a), a in 4096ths of a turn. */
const facing = (ax: number, az: number, bx: number, bz: number) => (Math.round((Math.atan2(-(bz - az), bx - ax) * 4096) / (2 * Math.PI)) + 4096) % 4096;

async function hold(link: GameLink, key: number, frames: number): Promise<void> {
  await link.down(key);
  await link.frames(frames);
  await link.up(key);
}

/** Cuts seen while `act` runs, from the state lines the game sent meanwhile. */
async function cutsDuring(link: GameLink, act: () => Promise<void>): Promise<number> {
  const first = (await link.state()).frame;
  await act();
  await link.frames(10);
  const seen = link.history.filter((s) => s.frame >= first);
  return seen.filter((s, i) => i > 0 && s.camera !== seen[i - 1]!.camera).length;
}

const overlay = process.env.OVERLAY;
if (!overlay) throw new Error('set OVERLAY to the REB build folder that is deployed');
const want = process.argv.slice(2);
const rooms = dayRooms.filter((r) => (want.length ? want.includes(r.slug) : ['yard', 'woods', 'platform', 'creek', 'camp-yard'].includes(r.slug)));
const session = await open(Number(process.env.PORT ?? 7811), '--mode REB --god --boot rebecca');
const { link } = session;
let flickers = 0;
try {
  await link.waitFor((s) => s.play, 'gameplay', 120_000);
  for (const spec of rooms) {
    const file = path.join(overlay, 'REB', `Stage${spec.stage + 1}`, `ROOM${spec.stage + 1}${spec.room.toString(16).toUpperCase().padStart(2, '0')}0.RDT`);
    const all = triggers(readFileSync(file));
    const shapes = loadShapes([path.join(overlay, 'REB'), process.env.RE1_DATA ?? '/tmp/re1-pc'], spec.stage, spec.room);
    await link.room(spec.stage, spec.room);
    // Its arrival scripts first: a first visit can move her and open messages.
    await settle(link);
    // A border: two cameras whose triggers into each other come within NEAR.
    const NEAR = 4000;
    const dist = (a: Quad, b: Quad) => Math.hypot(middle(a)[0] - middle(b)[0], middle(a)[1] - middle(b)[1]);
    const borders: { a: number; b: number; into: Trigger }[] = [];
    for (const into of all) {
      if (into.from > into.to || borders.some((x) => x.a === into.from && x.b === into.to)) continue;
      const near = all.filter((t) => t.from === into.to && t.to === into.from && dist(t.quad, into.quad) < NEAR);
      if (near.length) borders.push({ a: into.from, b: into.to, into });
    }
    const lines: string[] = [];
    for (const { a, b, into } of borders) {
      // Stand where the live camera cuts to A, near the trigger into B, facing it.
      const live = (await link.state()).camera;
      const toA = all.filter((t) => t.to === a && t.from === live).sort((x, y) => dist(x.quad, into.quad) - dist(y.quad, into.quad))[0];
      const here = live === a ? all.filter((t) => t.from === b && t.to === a) : toA ? [toA] : [];
      const target = middle(into.quad);
      const from = here.map((t) => standIn(t.quad, shapes, target)).find(Boolean);
      const [ax, az] = from ?? [NaN, NaN];
      const [bx, bz] = (Number.isFinite(ax) && standIn(into.quad, shapes, [ax, az])) || target;
      if (!Number.isFinite(ax)) {
        lines.push(`  ${a}>${b}: no floor to stand on in camera ${live}'s trigger into ${a}: skipped`);
        continue;
      }
      await link.place(Math.round(ax), Math.round(az), facing(ax, az, bx, bz));
      await link.frames(15);
      const start = await settle(link);
      if (Math.hypot(start.player.x - ax, start.player.z - az) > 600) {
        lines.push(`  ${a}>${b}: placed at (${Math.round(ax)}, ${Math.round(az)}), a script moved her to (${start.player.x}, ${start.player.z}): skipped`);
        continue;
      }
      // The cut is checked as she moves: a step, if standing there was not enough.
      if (start.camera !== a) await hold(link, Key.up, 3);
      if ((await link.state()).camera !== a) {
        lines.push(`  ${a}>${b}: placed at (${Math.round(ax)}, ${Math.round(az)}), camera is ${start.camera}, not ${a}: skipped`);
        continue;
      }
      // Walk at B until the camera cuts, at most 4 s.
      let cut = false;
      await link.down(Key.up);
      for (let f = 0; f < 120 && !cut; f += 3) cut = (await link.frames(3)).camera !== a;
      await link.up(Key.up);
      if (!cut) {
        const s = await link.state();
        lines.push(`  ${a}>${b}: walked 4 s from (${Math.round(ax)}, ${Math.round(az)}) and stopped at (${s.player.x}, ${s.player.z}) without a cut: skipped`);
        continue;
      }
      // Sway: a few steps back, a few forward, six times.
      const cuts = await cutsDuring(link, async () => {
        for (let k = 0; k < 6; k++) {
          await hold(link, Key.down, 8);
          await hold(link, Key.up, 8);
        }
      });
      if (cuts > 1) flickers++;
      const at = await link.state();
      lines.push(`  ${a}>${b}: ${cuts} cut${cuts === 1 ? '' : 's'} while swaying at (${at.player.x}, ${at.player.z})${cuts > 1 ? '  FLICKER' : ''}`);
    }
    console.log(`${spec.slug}: ${all.length} triggers, ${borders.length} borders`);
    for (const l of lines) console.log(l);
  }
} finally {
  session.end();
}
console.log(flickers ? `FAIL: ${flickers} borders flicker` : 'PASS');
process.exit(flickers ? 1 : 0);
