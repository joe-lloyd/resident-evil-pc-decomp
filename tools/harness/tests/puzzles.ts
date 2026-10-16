// Work every puzzle of Rebecca's day (rebecca/day/events.ts) in the game, the
// way a player does, and check it happens only when it should:
//   - with what it needs still undone, using the item or pressing action
//     leaves its flag clear and the item in her case;
//   - with them done, it sets its flag and takes the item;
//   - the way it opens in this room then takes her through;
//   - what it leaves to pick up is there, and she can take it.
// Each puzzle starts clean: its own flag and its needs' flags cleared, the
// room entered again so its script writes the "before" zones.
//
//   node tools/harness/tests/puzzles.ts [<step> ...]      (default: every puzzle whose scene marks its spot)
//
// Needs the engine and the overlay deployed (see mountain-trail.ts). Prints a
// line per puzzle and exits 1 if any fails.
import { open } from '../lab.ts';
import { Key, type GameLink } from '../link.ts';
import { faceTowards, headingTo, settle, useItem } from '../flows.ts';
import { Bank, flag, type GameState } from '../state.ts';
import { dayRooms } from '../../rebecca/day/rooms.ts';
import { EVENT_FLAGS, EVENTS, GIVE_FLAGS, keyItem, type RoomEvent } from '../../rebecca/day/events.ts';
import { inside, nearest, opens, outward, read, walkable, type Rect } from './floor.ts';

const bySlug = new Map(dayRooms.map((r) => [r.slug, r]));
const spotOf = (e: RoomEvent): Rect | undefined => read(e.room)?.spots?.find((sp) => sp.step === e.step)?.zone;
const wanted = process.argv.slice(2);
const events = EVENTS.filter((e) => (wanted.length ? wanted.includes(e.step) : true) && spotOf(e));
if (!events.length) throw new Error('no puzzle has its spot in a rendered scene');

const done = (s: GameState, step: string) => flag(s, Bank.common, EVENT_FLAGS.get(step)!);

/** Close whatever she opened (a message, the status screen) and wait for control in this room. */
const calm = (link: GameLink, room: { stage: number; room: number }) => settle(link, (s) => s.stage === room.stage && s.room === room.room);

/** How far ahead of her the game looks for a zone she is acting on or using an item at (update_player_position). */
const REACH = 600;

/** Stand her where the point she reaches falls in the spot, facing its middle. */
async function stand(link: GameLink, slug: string, zone: Rect): Promise<void> {
  const json = read(slug)!;
  const touch = (json.doors ?? []).filter((d) => !opens(slug, d.zone)).map((d) => d.zone);
  const cx = (zone.x0 + zone.x1) / 2;
  const cz = (zone.z0 + zone.z1) / 2;
  const reaches = ([x, z]: [number, number]) => {
    const d = Math.hypot(cx - x, cz - z) || 1;
    return inside(zone, x + ((cx - x) / d) * REACH, z + ((cz - z) / d) * REACH);
  };
  const at = nearest(walkable(json, touch), cx, cz, reaches);
  if (!at) throw new Error('nowhere she can walk to reaches its spot');
  await link.place(at[0], at[1]);
  await link.frames(6);
  await faceTowards(link, cx, cz);
}

/** Use the item if the puzzle takes one, else press action; then wait out her line. */
async function work(link: GameLink, e: RoomEvent, room: { stage: number; room: number }): Promise<GameState> {
  if (e.use) {
    const id = keyItem(e.use).id;
    if (!(await link.state()).items.some((it) => it.id === id)) await link.give(id, 1);
    await useItem(link, id);
    // The script waits a second after the status screen closes before it acts.
    await link.frames(90);
  } else {
    await link.tap(Key.action, 3);
    await link.frames(30);
  }
  return calm(link, room);
}

const first = bySlug.get(events[0]!.room)!;
const session = await open(Number(process.env.PORT ?? 7801), `--mode REB --boot rebecca:${first.stage}:${first.room}`);
const link = session.link;
const failures: string[] = [];
try {
  await link.waitFor((s) => s.play, 'gameplay', 120_000);
  for (const e of events) {
    const room = bySlug.get(e.room)!;
    const zone = spotOf(e)!;
    const problems: string[] = [];
    try {
      for (const step of [e.step, ...(e.needs ?? [])]) await link.setFlag(Bank.common, EVENT_FLAGS.get(step)!, false);
      if (e.gives) await link.setFlag(Bank.roomItems, GIVE_FLAGS.get(e.gives)!, true);
      await link.room(room.stage, room.room);
      await calm(link, room);

      if (e.needs?.length) {
        await stand(link, e.room, zone);
        const s = await work(link, e, room);
        if (done(s, e.step)) problems.push(`happened before ${e.needs.join(', ')}`);
        if (e.use && !s.items.some((it) => it.id === keyItem(e.use!).id)) problems.push('took the item before it could work');
        for (const n of e.needs) await link.setFlag(Bank.common, EVENT_FLAGS.get(n)!, true);
      }

      await stand(link, e.room, zone);
      let s = await work(link, e, room);
      if (!done(s, e.step)) throw new Error(`still not done after ${e.use ? `using the ${keyItem(e.use).name.toLowerCase()}` : 'pressing action'} at (${s.player.x}, ${s.player.z})`);
      if (e.use && s.items.some((it) => it.id === keyItem(e.use!).id)) problems.push('the item is still in her case');

      if (e.gives) {
        const id = keyItem(e.gives).id;
        await stand(link, e.room, zone);
        await link.tap(Key.action, 3);
        await link.frames(30);
        s = await calm(link, room);
        if (!s.items.some((it) => it.id === id)) problems.push(`no ${keyItem(e.gives).name.toLowerCase()} to pick up after`);
      }

      const to = e.opens && (e.opens.from ?? e.room) === e.room ? e.opens.to : undefined;
      const door = to ? read(e.room)?.doors?.find((d) => d.to === to) : undefined;
      if (to && door) {
        const target = bySlug.get(to);
        const json = read(e.room)!;
        const touch = (json.doors ?? []).filter((d) => d !== door && !opens(e.room, d.zone)).map((d) => d.zone);
        const cells = walkable(json, touch);
        const cx = (door.zone.x0 + door.zone.x1) / 2;
        const cz = (door.zone.z0 + door.zone.z1) / 2;
        // As tour.ts goes through a door: stand in one that opens and press
        // action; start a step short of a walk-through path and walk on.
        const action = opens(e.room, door.zone);
        const at = action
          ? nearest(cells, cx, cz, ([x, z]) => inside(door.zone, x, z))
          : nearest(cells, cx, cz, ([x, z]) => !inside(door.zone, x, z, 600) && inside(door.zone, x, z, 1600));
        if (!at) problems.push(`no point of the way to ${to} she can reach`);
        else {
          const [fx, fz] = action ? outward(json, door.zone) : [cx, cz];
          await link.place(at[0], at[1], headingTo(at[0], at[1], fx, fz));
          await link.frames(6);
          if (action) await link.tap(Key.action, 2);
          else await link.down(Key.up);
          s = await link.frames(60);
          await link.release();
          s = await settle(link, (st) => st.stage !== room.stage || st.room !== room.room, 30_000).catch(() => s);
          if (target && (s.stage !== target.stage || s.room !== target.room)) problems.push(`the way to ${to} did not take her there`);
        }
      }
      if (problems.length) throw new Error(problems.join('; '));
      console.log(`ok    ${e.step} (${e.room})`);
    } catch (err) {
      await link.release().catch(() => undefined);
      // Close whatever it left open (a message, the status screen) so the next jump can run.
      await settle(link, () => true, 20_000).catch(() => undefined);
      failures.push(e.step);
      console.log(`FAIL  ${e.step} (${e.room}): ${err instanceof Error ? err.message : String(err)}`);
    }
  }
} finally {
  session.end();
}
console.log(failures.length ? `${failures.length} puzzles failed` : 'every puzzle works');
process.exit(failures.length ? 1 : 0);
