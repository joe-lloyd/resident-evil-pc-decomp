// What the owner met playing Rebecca's day, driven in the game:
//
//   walls   she walks straight at something the background draws (a wall, a
//           shut door, a counter, a drum) and stops before it, not inside or
//           behind it. Prints where she stopped and takes a picture.
//   reach   she presses action at a check from a step back from what the
//           scene drew, facing it, at an angle too; the check answers.
//   locks   the road gate and the depot gate: tried with the bolt cutters in
//           her case they stay shut; used from her case they open; from the
//           far side they stay shut until then.
//   paths   she walks the ways the owner was stopped on: out of the flume,
//           between the yard's truck and shed both ways, onto and across the
//           bridge, and over planks, logs and rocks lying on the ground.
//           Tank controls, as a player walks (flows.ts walkTo); a stop short
//           of the next point fails. Pictures at each point.
//
//   node tools/harness/tests/edges.ts [walls] [reach] [locks] [paths]   (default: all)
//
// Needs the engine and the overlay deployed (see mountain-trail.ts). OUT names
// the folder for the pictures (default /tmp/rae-tests/edges). Exits 1 if any
// case fails.
import path from 'node:path';
import { open } from '../lab.ts';
import { Key, type GameLink } from '../link.ts';
import { headingTo, face, settle, StuckError, useItem, walkTo } from '../flows.ts';
import { snapshot } from '../snapshot.ts';
import { Bank, flag, messageOnScreen, type GameState } from '../state.ts';
import { dayRooms } from '../../rebecca/day/rooms.ts';
import { CUT_FLAGS } from '../../rebecca/day/cutscenes.ts';
import { read, type Rect } from './floor.ts';
import { readScript } from '../../rebecca/day/walkable.ts';

const out = path.join(process.env.OUT ?? '/tmp/rae-tests', 'edges');
const bySlug = new Map(dayRooms.map((r) => [r.slug, r]));
const want = process.argv.slice(2);
const runs = (part: string) => !want.length || want.includes(part);

type P = { x: number; z: number };
/** She starts at `from` facing `toward` and walks at it; `stop` is the box her centre must stay out of. */
interface WallCase {
  room: string;
  what: string;
  from: P;
  toward: P;
  stop: Rect;
}
/** Where she stands to press action at a check, a step further back than the scene drew it, facing its middle. */
interface ReachCase {
  room: string;
  check: string;
  at: P;
  toward: P;
}

/** A box round a point the old collision let her walk onto, where a camera draws something solid. */
const near = (x: number, z: number): Rect => ({ x0: x - 200, z0: z - 200, x1: x + 200, z1: z + 200 });
// Picked from the floor walkable.ts found drawn solid before the floor probe.
const WALLS: WallCase[] = [
  { room: 'yard', what: "the cabin's east end", from: { x: 29425, z: 3825 }, toward: { x: 27625, z: 3825 }, stop: near(27625, 3825) },
  { room: 'yard', what: "the truck's tail", from: { x: 7776, z: 16203 }, toward: { x: 9605, z: 17425 }, stop: near(9605, 17425) },
  { room: 'platform', what: "the wheel house", from: { x: 1419, z: 17319 }, toward: { x: 2805, z: 16745 }, stop: near(2805, 16745) },
  { room: 'camp-yard', what: "the bunkhouse corner", from: { x: 11152, z: 3598 }, toward: { x: 11985, z: 4845 }, stop: near(11985, 4845) },
  { room: 'den', what: "the den's rock", from: { x: 18112, z: 6707 }, toward: { x: 20145, z: 5865 }, stop: near(20145, 5865) },
  { room: 'logging-road', what: "the log pile", from: { x: 25725, z: 16745 }, toward: { x: 24225, z: 16745 }, stop: near(24225, 16745) },
  { room: 'camp-gate', what: "the gate hut", from: { x: 18558, z: 7752 }, toward: { x: 19805, z: 8585 }, stop: near(19805, 8585) },
  { room: 'workshop', what: "the bench", from: { x: 8785, z: 3485 }, toward: { x: 10285, z: 3485 }, stop: near(10285, 3485) },
  { room: 'bunkhouse', what: "the bunks", from: { x: 9176, z: 2687 }, toward: { x: 9605, z: 4845 }, stop: near(9605, 4845) },
  // Over the tipped chair (lower than her stride) to the desk's end.
  { room: 'booth', what: "the control desk", from: { x: 5625, z: 2805 }, toward: { x: 2805, z: 2805 }, stop: near(2805, 2805) },
  { room: 'mess', what: "the cook at the counter", from: { x: 3459, z: 7799 }, toward: { x: 4845, z: 7225 }, stop: near(4845, 7225) },
  { room: 'office', what: "the office wall", from: { x: 7225, z: 4645 }, toward: { x: 7225, z: 3145 }, stop: near(7225, 3145) },
];
// A step (700 units) back from the zone each scene drew: the action button's reach (600) fell short of it.
const REACH: ReachCase[] = [
  { room: 'yard', check: 'A winch on the truck', at: { x: 21610, z: 18360 }, toward: { x: 20060, z: 18360 } },
  { room: 'lookout', check: 'The stove is still warm', at: { x: 6165, z: 7990 }, toward: { x: 5015, z: 7990 } },
  { room: 'mess', check: 'A meat cleaver', at: { x: 7540, z: 7684 }, toward: { x: 6290, z: 7684 } },
  { room: 'den', check: 'The ranger', at: { x: 19814, z: 8183 }, toward: { x: 17414, z: 8183 } },
  { room: 'woods', check: 'Rifle brass, a handful', at: { x: 7700, z: 16405 }, toward: { x: 5950, z: 16405 } },
  { room: 'camp-yard', check: 'Someone was burned here', at: { x: 18400, z: 14110 }, toward: { x: 15300, z: 14110 } },
  { room: 'office', check: 'A safe', at: { x: 4135, z: 5228 }, toward: { x: 2635, z: 5228 } },
  { room: 'bunkhouse', check: 'Belts, buckled round', at: { x: 19420, z: 7438 }, toward: { x: 17170, z: 7438 } },
  { room: 'platform', check: 'Car 4. The door has', at: { x: 14680, z: 18105 }, toward: { x: 11730, z: 18105 } },
];

/** She walks from `from` through each of `via` in turn; `leaves` names the room the last point takes her into. */
interface PathCase {
  room: string;
  what: string;
  from: P;
  via: P[];
  leaves?: string;
}
// Chosen on the rooms' collision (walkable.ts --reach): each way is open
// there, so a stop is the engine snagging her, or the collision wrong.
const PATHS: PathCase[] = [
  // The owner could not leave the log flume: from the boat, down the path and out to the pond.
  { room: 'flume', what: 'out to the pond', from: { x: 11220, z: 13600 }, via: [{ x: 10200, z: 17500 }, { x: 10200, z: 19900 }, { x: 10200, z: 21300 }], leaves: 'pond' },
  // Nor get between the truck and the shed in the yard: from the shed door round to the road, and back.
  { room: 'yard', what: 'from the shed door past the truck', from: { x: 10880, z: 13600 }, via: [{ x: 10200, z: 15800 }, { x: 6120, z: 15900 }, { x: 5100, z: 17200 }] },
  { room: 'yard', what: 'back past the truck to the shed door', from: { x: 5100, z: 17200 }, via: [{ x: 6120, z: 15900 }, { x: 10200, z: 15800 }, { x: 10880, z: 13600 }] },
  // Nor onto the bridge: from the yard's trail, across the deck and on to the platform.
  { room: 'bridge', what: 'across the bridge', from: { x: 10200, z: 6120 }, via: [{ x: 10200, z: 10500 }, { x: 10200, z: 18700 }, { x: 10200, z: 26500 }, { x: 9520, z: 30800 }], leaves: 'platform' },
  // Logs lying on the ground, lower than her stride: over them, not round. The
  // first point is on the log.
  { room: 'camp-gate', what: 'over a strewn log by the gate', from: { x: 16490, z: 12240 }, via: [{ x: 16490, z: 13855 }, { x: 16490, z: 15640 }] },
  { room: 'camp-gate', what: 'over a strewn log by the cold deck', from: { x: 8500, z: 10200 }, via: [{ x: 8500, z: 11475 }, { x: 8500, z: 12920 }] },
  { room: 'den', what: 'over the windfall', from: { x: 9010, z: 16320 }, via: [{ x: 9860, z: 17425 }, { x: 10710, z: 18530 }] },
];

/** Into the room, cutscenes seen, standing in control. */
async function enter(link: GameLink, slug: string): Promise<GameState> {
  const r = bySlug.get(slug)!;
  await link.room(r.stage, r.room);
  return settle(link, (s) => s.stage === r.stage && s.room === r.room);
}

async function placeFacing(link: GameLink, at: P, toward: P): Promise<GameState> {
  await link.place(at.x, at.z, headingTo(at.x, at.z, toward.x, toward.z));
  await link.frames(8);
  return face(link, headingTo(at.x, at.z, toward.x, toward.z), 40);
}

const inRect = (r: Rect, p: P) => p.x > r.x0 && p.x < r.x1 && p.z > r.z0 && p.z < r.z1;

async function walls(link: GameLink, fail: (s: string) => void): Promise<void> {
  for (const c of WALLS) {
    await enter(link, c.room);
    const start = await placeFacing(link, c.from, c.toward);
    const far = Math.hypot(c.toward.x - c.from.x, c.toward.z - c.from.z);
    if (Math.hypot(start.player.x - c.from.x, start.player.z - c.from.z) > 300) {
      fail(`${c.room}: could not stand her at (${c.from.x}, ${c.from.z})`);
      continue;
    }
    // Walk at it until she stops, or is as far past it as she started short.
    await link.down(Key.up);
    let s = start;
    let entered = false;
    let still = 0;
    for (let k = 0; k < 80 && still < 6; k++) {
      const prev = s;
      s = await link.frames(3);
      if (inRect(c.stop, { x: s.player.x, z: s.player.z })) entered = true;
      still = Math.hypot(s.player.x - prev.player.x, s.player.z - prev.player.z) < 10 ? still + 1 : 0;
      if (Math.hypot(s.player.x - c.from.x, s.player.z - c.from.z) > far + 400 || s.room !== start.room) break;
    }
    const name = `walls-${c.room}-${c.what.replace(/[^a-z0-9]+/gi, '-').toLowerCase()}`;
    await snapshot(link, out, name);
    await link.up(Key.up);
    s = await link.frames(5);
    const p = { x: s.player.x, z: s.player.z };
    const left = Math.hypot(c.toward.x - p.x, c.toward.z - p.z);
    const ok = !entered && s.room === start.room;
    console.log(`${ok ? 'ok  ' : 'FAIL'} walls ${c.room}: ${c.what}: from (${c.from.x}, ${c.from.z}) she ${ok ? 'stopped' : 'walked into it, to'} (${p.x}, ${p.z}), ${Math.round(left)} from (${c.toward.x}, ${c.toward.z}); picture ${name}.png`);
    if (!ok) fail(`${c.room}: walked into ${c.what}`);
  }
}

async function reach(link: GameLink, fail: (s: string) => void): Promise<void> {
  for (const c of REACH) {
    await enter(link, c.room);
    const stood = await placeFacing(link, c.at, c.toward);
    await link.tap(Key.action, 3);
    let s = await link.frames(20);
    if (process.env.HARNESS_TRACE) console.log(`    stood at (${stood.player.x}, ${stood.player.z}) angle ${stood.player.angle}`);
    const shown = messageOnScreen(s);
    const msgId = s.messageId;
    const name = `reach-${c.room}-${c.check.slice(0, 16).replace(/[^a-z0-9]+/gi, '-').toLowerCase()}`;
    if (shown) await snapshot(link, out, name);
    s = await settle(link);
    console.log(`${shown ? 'ok  ' : 'FAIL'} reach ${c.room}: "${c.check}" from (${c.at.x}, ${c.at.z}), facing (${c.toward.x}, ${c.toward.z}): ${shown ? `message ${msgId}; picture ${name}.png` : 'nothing'}`);
    if (!shown) fail(`${c.room}: "${c.check}" did not answer`);
  }
}

/** The bolt cutters on the road gate and the depot gate (FG_LOCK flags, day/scripts.ts). */
const LOCKS = [
  { from: 'road', to: 'washout', flag: 43 },
  { from: 'camp-yard', to: 'depot', flag: 41 },
];
/** Where she stands at a door, facing it: where the game puts her coming back through it (its script, walkable.ts readScript), a step from it. */
function atDoor(from: string, to: string): { stand: P; gate: P } {
  const d = read(from)!.doors!.find((x) => x.to === to)!;
  const back = readScript(from).arrivals.find((a) => a.from === to)!;
  return { stand: { x: back.x, z: back.z }, gate: { x: (d.zone.x0 + d.zone.x1) / 2, z: (d.zone.z0 + d.zone.z1) / 2 } };
}
const CUTTERS = 28;

async function locks(link: GameLink, fail: (s: string) => void): Promise<void> {
  for (const lock of LOCKS) {
    const l = { ...lock, ...atDoor(lock.from, lock.to) };
    const from = bySlug.get(l.from)!;
    const to = bySlug.get(l.to)!;
    const here = (s: GameState, r: { stage: number; room: number }) => s.stage === r.stage && s.room === r.room;
    await link.setFlag(Bank.locks, l.flag, false);
    let s = await enter(link, l.from);
    if (!s.items.some((it) => it.id === CUTTERS)) await link.give(CUTTERS, 2);
    // With the cutters in her case, the gate does not open by itself: she
    // walks up to it and presses action, as the owner did.
    await placeFacing(link, l.stand, l.gate);
    await link.down(Key.up);
    await link.frames(25);
    await link.up(Key.up);
    await link.tap(Key.action, 3);
    s = await link.frames(20);
    const said = messageOnScreen(s);
    await snapshot(link, out, `locks-${l.from}-tried`);
    s = await settle(link);
    s = await link.frames(60);
    s = await link.frames(60);
    s = await settle(link);
    const stayed = here(s, from) && !flag(s, Bank.locks, l.flag);
    console.log(`${stayed && said ? 'ok  ' : 'FAIL'} locks ${l.from}: tried with the cutters in her case: ${said ? 'her line' : 'no line'}, ${stayed ? 'still shut' : 'it opened'}`);
    if (!stayed || !said) fail(`${l.from}: the gate to ${l.to} opened, or said nothing, when tried`);
    // From the far side, still shut.
    await enter(link, l.to);
    const far = atDoor(l.to, l.from);
    await placeFacing(link, far.stand, far.gate);
    // Walk into it: from this side it was a walk she left by on touch.
    await link.down(Key.up);
    await link.frames(60);
    await link.up(Key.up);
    await link.tap(Key.action, 3);
    s = await link.frames(20);
    const farSaid = messageOnScreen(s);
    await snapshot(link, out, `locks-${l.to}-far-side`);
    s = await settle(link);
    s = await link.frames(60);
    const farShut = here(s, to);
    console.log(`${farShut ? 'ok  ' : 'FAIL'} locks ${l.to}: the way back to ${l.from} from the far side: ${farSaid ? 'her line' : 'no line'}, ${farShut ? 'still shut' : 'it opened'}`);
    if (!farShut) fail(`${l.to}: the way to ${l.from} opened from the far side`);
    // Used from her case at the gate: it opens, and then takes her through.
    s = await enter(link, l.from);
    if (!s.items.some((it) => it.id === CUTTERS)) await link.give(CUTTERS, 2);
    await placeFacing(link, l.stand, l.gate);
    await link.down(Key.up);
    await link.frames(25);
    await link.up(Key.up);
    await useItem(link, CUTTERS, false);
    await link.frames(45);
    s = await link.frames(60);
    await snapshot(link, out, `locks-${l.from}-cut`);
    s = await settle(link);
    const cut = flag(s, Bank.locks, l.flag);
    await link.tap(Key.action, 3);
    try {
      s = await link.waitFor((t) => here(t, to), `${l.to}`, 20_000);
    } catch {
      s = await link.state();
    }
    s = await settle(link);
    const through = here(s, to);
    console.log(`${cut && through ? 'ok  ' : 'FAIL'} locks ${l.from}: used the cutters: ${cut ? `FG_LOCK ${l.flag} raised` : 'the lock stayed'}, ${through ? `then through to ${l.to}` : 'and she did not get through'}`);
    if (!cut || !through) fail(`${l.from}: using the cutters did not open the way to ${l.to}`);
  }
}

async function paths(link: GameLink, fail: (s: string) => void): Promise<void> {
  for (const c of PATHS) {
    await enter(link, c.room);
    const start = await placeFacing(link, c.from, c.via[0]!);
    const name = (k: number) => `paths-${c.room}-${c.what.replace(/[^a-z0-9]+/gi, '-').toLowerCase()}-${k}`;
    let why = '';
    let s = start;
    for (const [k, p] of c.via.entries()) {
      const last = k === c.via.length - 1;
      try {
        // The last point of a way out is past the edge: she walks till the room changes.
        s = await walkTo(link, p.x, p.z, { radius: last && c.leaves ? 0 : 300, timeoutMs: 40_000 });
      } catch (err) {
        if (!(err instanceof StuckError)) throw err;
        why = `stopped at (${err.state.player.x}, ${err.state.player.z}) short of (${p.x}, ${p.z})`;
        await snapshot(link, out, name(k));
        break;
      }
      if (s.room !== start.room) break;
      await snapshot(link, out, name(k));
    }
    s = await settle(link);
    const left = s.stage !== start.stage || s.room !== start.room;
    const want = c.leaves ? bySlug.get(c.leaves)! : undefined;
    const ok = !why && (want ? left && s.stage === want.stage && s.room === want.room : !left);
    console.log(`${ok ? 'ok  ' : 'FAIL'} paths ${c.room}: ${c.what}: ${ok ? (want ? `out into ${c.leaves}` : `through to (${s.player.x}, ${s.player.z})`) : why || `ended in stage ${s.stage} room ${s.room.toString(16)}`}`);
    if (!ok) fail(`${c.room}: ${c.what}: ${why || 'did not get through'}`);
  }
}

const first = bySlug.get('platform')!;
const session = await open(Number(process.env.PORT ?? 7801), `--mode REB --boot rebecca:${first.stage}:${first.room}`);
const link = session.link;
const failures: string[] = [];
try {
  await link.waitFor((s) => s.play, 'gameplay', 120_000);
  await link.god(true);
  // Every cutscene seen, so none takes her over as she comes and goes.
  for (const f of CUT_FLAGS.values()) await link.setFlag(Bank.common, f, true);
  const fail = (s: string) => failures.push(s);
  if (runs('walls')) await walls(link, fail);
  if (runs('reach')) await reach(link, fail);
  if (runs('locks')) await locks(link, fail);
  if (runs('paths')) await paths(link, fail);
} finally {
  session.end();
}
console.log(failures.length ? `${failures.length} failed:\n  ${failures.join('\n  ')}` : 'all passed');
process.exit(failures.length ? 1 : 0);
