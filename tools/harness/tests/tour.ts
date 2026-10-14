// Walk every door of the rooms built with blender/kit.py, and check she comes
// out in the neighbour the scene says, inside its floor, and stays there.
// First it works out from the scene's walls where she can walk from where
// she comes into the room; a door she can't reach fails there. Then, in the
// game: for a door that opens she stands in it and presses action; for a
// walk-through path she starts a step short and walks on.
//
//   node tools/harness/tests/tour.ts [<slug> ...]      (default: every rendered kit room)
//
// Needs the engine and the overlay deployed (see mountain-trail.ts). Prints a
// line per door and exits 1 if any door fails.
import { existsSync, readFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { open } from '../lab.ts';
import { Key } from '../link.ts';
import { faceTowards, settle } from '../flows.ts';
import { dayRooms, kitRooms } from '../../rebecca/day/rooms.ts';

const day = path.join(path.dirname(fileURLToPath(import.meta.url)), '..', '..', 'rebecca', 'day');
type Rect = { x0: number; z0: number; x1: number; z1: number };
interface Json {
  bounds: Rect;
  doors?: { to: string; zone: Rect; arrive: { x: number; z: number } }[];
  walls?: Rect[];
  voids?: Rect[];
  checks?: { zone: Rect }[];
}
const read = (slug: string): Json | undefined => {
  const f = path.join(day, slug, 'renders', 'room.json');
  return existsSync(f) ? (JSON.parse(readFileSync(f, 'utf8')) as Json) : undefined;
};

const bySlug = new Map(dayRooms.map((r) => [r.slug, r]));
const wanted = process.argv.slice(2);
const rooms = (wanted.length ? wanted.map((s) => bySlug.get(s)!) : kitRooms).filter((r) => r && read(r.slug)?.doors);
if (!rooms.length) throw new Error('no rendered kit rooms to tour');
// A door only exists once both its rooms are built (day/scripts.ts leaves the rest out).
const built = (slug: string) => bySlug.has(slug) && (!kitRooms.some((k) => k.slug === slug) || read(slug)?.doors !== undefined);

/** Her body's reach round the point she stands on, in game units. */
const BODY = 450;
const inside = (r: Rect, x: number, z: number, pad = 0) => x > r.x0 - pad && x < r.x1 + pad && z > r.z0 - pad && z < r.z1 + pad;

/** Whether the game has this door firing on the action button (it is in the room script as 0x80). */
function opens(slug: string, zone: Rect): boolean {
  const c = readFileSync(path.join(day, slug, 'room.c'), 'utf8');
  for (const m of c.matchAll(/door_aot_set\(\d+, (\d+), (\d+), (\d+), (\d+),.*, (\d+)\);/g)) {
    if (Number(m[1]) === zone.x0 && Number(m[2]) === zone.z0) return (Number(m[5]) & 0x80) !== 0;
  }
  throw new Error(`no door at (${zone.x0}, ${zone.z0}) in ${slug}/room.c`);
}

/** Grid step for working out where she can walk, in game units. */
const CELL = 250;

/**
 * The floor she can reach from where she comes into the room (any door's
 * arrival), keeping her body clear of walls and drops and out of the room's
 * walk-through doors, which would take her out. Returns the reachable cell
 * centres.
 */
function walkable(json: Json, touchZones: Rect[]): [number, number][] {
  const b = json.bounds;
  const blockers = [...(json.walls ?? []), ...(json.voids ?? [])];
  const free = (x: number, z: number) =>
    inside(b, x, z, -BODY) && !blockers.some((r) => inside(r, x, z, BODY)) && !touchZones.some((r) => inside(r, x, z));
  const nx = Math.ceil((b.x1 - b.x0) / CELL);
  const nz = Math.ceil((b.z1 - b.z0) / CELL);
  const at = (i: number, k: number): [number, number] => [b.x0 + (i + 0.5) * CELL, b.z0 + (k + 0.5) * CELL];
  const seen = new Set<number>();
  const queue: [number, number][] = [];
  for (const d of json.doors ?? []) {
    const i = Math.floor((d.arrive.x - b.x0) / CELL);
    const k = Math.floor((d.arrive.z - b.z0) / CELL);
    // She may arrive a little inside a wall's reach: start from the nearest free cell.
    let best: [number, number] | undefined;
    for (let r = 0; r <= 4 && !best; r++) {
      for (let di = -r; di <= r && !best; di++) for (let dk = -r; dk <= r && !best; dk++) {
        const [x, z] = at(i + di, k + dk);
        if (i + di >= 0 && i + di < nx && k + dk >= 0 && k + dk < nz && free(x, z)) best = [i + di, k + dk];
      }
    }
    if (best && !seen.has(best[0] * 4096 + best[1])) {
      seen.add(best[0] * 4096 + best[1]);
      queue.push(best);
    }
  }
  const out: [number, number][] = [];
  while (queue.length) {
    const [i, k] = queue.pop()!;
    out.push(at(i, k));
    for (const [di, dk] of [[1, 0], [-1, 0], [0, 1], [0, -1]]) {
      const ni = i + di!, nk = k + dk!;
      if (ni < 0 || nk < 0 || ni >= nx || nk >= nz || seen.has(ni * 4096 + nk)) continue;
      const [x, z] = at(ni, nk);
      if (!free(x, z)) continue;
      seen.add(ni * 4096 + nk);
      queue.push([ni, nk]);
    }
  }
  return out;
}

/** The reachable spot nearest `x, z` that passes `ok`. */
function nearest(cells: [number, number][], x: number, z: number, ok: (c: [number, number]) => boolean): [number, number] | undefined {
  let best: [number, number] | undefined;
  for (const c of cells) if (ok(c) && (!best || Math.hypot(c[0] - x, c[1] - z) < Math.hypot(best[0] - x, best[1] - z))) best = c;
  return best && [Math.round(best[0]), Math.round(best[1])];
}

const first = rooms[0]!;
const session = await open(Number(process.env.PORT ?? 7801), `--mode REB --boot rebecca:${first.stage}:${first.room}`);
const link = session.link;
const failures: string[] = [];
try {
  await link.waitFor((s) => s.play, "gameplay", 120_000);
  for (const r of rooms) {
    const json = read(r.slug)!;
    for (const d of json.doors ?? []) {
      if (!built(d.to)) continue;
      const target = bySlug.get(d.to)!;
      const label = `${r.slug} -> ${d.to}`;
      try {
        let s = await link.state();
        if (s.stage !== r.stage || s.room !== r.room) s = await link.room(r.stage, r.room);
        await settle(link);
        const cx = (d.zone.x0 + d.zone.x1) / 2;
        const cz = (d.zone.z0 + d.zone.z1) / 2;
        const open = opens(r.slug, d.zone);
        const touchZones = (json.doors ?? []).filter((o) => o !== d && !opens(r.slug, o.zone)).map((o) => o.zone);
        const cells = walkable(json, touchZones);
        if (open) {
          // A door that opens: she can stand in it, and action there takes her through.
          const spot = nearest(cells, cx, cz, ([x, z]) => inside(d.zone, x, z));
          if (!spot) throw new Error('no spot in its zone she can walk to from where she comes in');
          await link.place(spot[0], spot[1]);
          await link.frames(6);
          await faceTowards(link, cx, cz);
          await link.tap(Key.action, 2);
          s = await link.frames(20);
          if (s.stage === r.stage && s.room === r.room) throw new Error(`stood in it at (${s.player.x}, ${s.player.z}) and action did nothing`);
        } else {
          // A walk-through path: she can get a step short of it, and walking on takes her out.
          const spot = nearest(cells, cx, cz, ([x, z]) => !inside(d.zone, x, z, 600) && inside(d.zone, x, z, 1600));
          if (!spot) throw new Error('no spot a step short of it she can walk to from where she comes in');
          await link.place(spot[0], spot[1]);
          await link.frames(4);
          const deadline = Date.now() + 15_000;
          for (;;) {
            await faceTowards(link, cx, cz);
            await link.down(Key.up);
            s = await link.frames(8);
            if (s.stage !== r.stage || s.room !== r.room) break;
            if (Date.now() > deadline) throw new Error(`walked at it for 15 s and still in ${r.slug} at (${s.player.x}, ${s.player.z})`);
          }
          await link.release();
        }
        s = await settle(link, (st) => st.stage !== r.stage || st.room !== r.room);
        if (s.stage !== target.stage || s.room !== target.room) throw new Error(`came out in ${s.stage}:${s.room.toString(16)}, not ${d.to}`);
        s = await link.frames(60);
        if (s.stage !== target.stage || s.room !== target.room) throw new Error(`walked straight back out of ${d.to}`);
        const tb = read(d.to)?.bounds;
        if (tb && (s.player.x < tb.x0 || s.player.x > tb.x1 || s.player.z < tb.z0 || s.player.z > tb.z1)) {
          throw new Error(`landed off ${d.to}'s floor at (${s.player.x}, ${s.player.z})`);
        }
        console.log(`ok    ${label}  (arrived at ${s.player.x}, ${s.player.z})`);
      } catch (err) {
        await link.release().catch(() => undefined);
        // Close a message she may have opened instead, so the next jump can run.
        for (let i = 0; i < 4; i++) await link.tap(Key.action, 2).then(() => link.frames(10)).catch(() => undefined);
        failures.push(label);
        console.log(`FAIL  ${label}: ${(err as Error).message}`);
      }
    }
  }
} finally {
  session.end();
}
console.log(failures.length ? `${failures.length} doors failed` : 'every door works');
process.exit(failures.length ? 1 : 0);
