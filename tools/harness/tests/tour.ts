// Walk every door of the rooms built with blender/kit.py, and check she comes
// out in the neighbour the scene says, inside its floor, and stays there.
// First it works out from the scene's walls where she can walk from where
// she comes into the room; a door she can't reach fails there. Then, in the
// game: for a door that opens she stands in it and presses action; for a
// walk-through path she starts a step short and walks on. Every puzzle's flag
// and every lock is set first, so the ways they open are open.
//
//   node tools/harness/tests/tour.ts [<slug> ...]      (default: every rendered kit room)
//
// Needs the engine and the overlay deployed (see mountain-trail.ts). Prints a
// line per door and exits 1 if any door fails.
import { open } from '../lab.ts';
import { Key } from '../link.ts';
import { faceTowards, headingTo, settle } from '../flows.ts';
import { dayRooms, kitRooms } from '../../rebecca/day/rooms.ts';
import { inside, nearest, opens, outward, read, walkable } from './floor.ts';
import { EVENT_FLAGS } from '../../rebecca/day/events.ts';
import { CUT_FLAGS } from '../../rebecca/day/cutscenes.ts';
import { LOCK_FLAGS } from '../../rebecca/day/scripts.ts';
import { Bank } from '../state.ts';

const bySlug = new Map(dayRooms.map((r) => [r.slug, r]));
const wanted = process.argv.slice(2);
const rooms = (wanted.length ? wanted.map((s) => bySlug.get(s)!) : kitRooms).filter((r) => r && read(r.slug)?.doors);
if (!rooms.length) throw new Error('no rendered kit rooms to tour');
// A door only exists once both its rooms are built (day/scripts.ts leaves the rest out).
const built = (slug: string) => bySlug.has(slug) && (!kitRooms.some((k) => k.slug === slug) || read(slug)?.doors !== undefined);

const first = rooms[0]!;
const session = await open(Number(process.env.PORT ?? 7801), `--mode REB --boot rebecca:${first.stage}:${first.room}`);
const link = session.link;
const failures: string[] = [];
try {
  await link.waitFor((s) => s.play, "gameplay", 120_000);
  // Every way a puzzle opens, open, and every lock unlocked (the kit rooms'
  // and the yard shed's 60): puzzles.ts tests them shut. Every cutscene seen,
  // so none takes her over on the way through: cutscenes.ts plays them.
  for (const f of EVENT_FLAGS.values()) await link.setFlag(Bank.common, f, true);
  for (const f of CUT_FLAGS.values()) await link.setFlag(Bank.common, f, true);
  for (const f of [...LOCK_FLAGS, 60]) await link.setFlag(Bank.locks, f, true);
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
          const [ox, oz] = outward(json, d.zone);
          await link.place(spot[0], spot[1], headingTo(spot[0], spot[1], ox, oz));
          await link.frames(6);
          await link.tap(Key.action, 2);
          // A lift's door takes longer to start than a door's: up to three seconds.
          for (let k = 0; k < 9 && s.stage === r.stage && s.room === r.room; k++) s = await link.frames(10);
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
