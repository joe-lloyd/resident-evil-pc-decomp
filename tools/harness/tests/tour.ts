// Walk every door of the rooms built with blender/kit.py: jump into the
// room, stand her a step short of the door, face it and go through (walking
// on for a touch door, the action button for a door that opens), and check
// she comes out in the neighbour the scene says, inside its floor, and stays.
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
  doors?: { to: string; zone: Rect }[];
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

/**
 * Where to stand to walk into a door: a step short of it, with a straight
 * walk to it that crosses no wall, drop or thing to examine (pressing action
 * on one of those opens it instead of the door). Tries the way toward the
 * middle of the floor first, then straight in from each side.
 */
function approach(json: Json, zone: Rect): [number, number] {
  const cx = (zone.x0 + zone.x1) / 2;
  const cz = (zone.z0 + zone.z1) / 2;
  const b = json.bounds;
  const mx = (b.x0 + b.x1) / 2;
  const mz = (b.z0 + b.z1) / 2;
  const blockers = [...(json.walls ?? []), ...(json.voids ?? [])];
  const checks = (json.checks ?? []).map((c) => c.zone);
  const len = Math.hypot(mx - cx, mz - cz) || 1;
  const dirs: [number, number][] = [[(mx - cx) / len, (mz - cz) / len], [0, 1], [0, -1], [1, 0], [-1, 0]];
  for (const back of [1500, 1100, 800]) {
    for (const [dx, dz] of dirs) {
      const x = cx + dx * back;
      const z = cz + dz * back;
      if (!inside(b, x, z, -BODY) || inside(zone, x, z)) continue;
      let clear = true;
      for (let t = 0; t <= 1 && clear; t += 0.05) {
        const px = x + (cx - x) * t;
        const pz = z + (cz - z) * t;
        if (inside(zone, px, pz)) break;
        if (blockers.some((r) => inside(r, px, pz, BODY)) || checks.some((r) => inside(r, px, pz))) clear = false;
      }
      if (clear) return [Math.round(x), Math.round(z)];
    }
  }
  const len2 = Math.min(1500, len * 0.8);
  return [Math.round(cx + ((mx - cx) / len) * len2), Math.round(cz + ((mz - cz) / len) * len2)];
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
        const [sx, sz] = approach(json, d.zone);
        await link.place(sx, sz);
        await link.frames(4);
        await faceTowards(link, cx, cz);
        const deadline = Date.now() + 20_000;
        await link.down(Key.up);
        for (;;) {
          s = await link.frames(6);
          if (s.stage !== r.stage || s.room !== r.room) break;
          if (Date.now() > deadline) throw new Error(`still in ${r.slug} at (${s.player.x}, ${s.player.z})`);
          await link.tap(Key.action, 2);
        }
        await link.release();
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
