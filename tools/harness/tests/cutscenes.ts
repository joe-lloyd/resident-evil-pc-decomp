// Play the cutscenes of her day (rebecca/day/cutscenes.ts) in the game. Each
// starts from a checkpoint: the game jumps to its room with the scene's flag
// clear, then sets it off the way a player would (coming in, pressing action
// at the thing, walking into the spot, finishing the puzzle). The test takes a
// picture at every line and every camera cut, presses on through the lines,
// and checks that:
//   - the scene ran (its flag is set) and showed every line it has;
//   - she has her controls back afterwards: no letterbox, no camera lock,
//     her controls on, and she moves when pushed;
//   - it doesn't run again when she comes back.
//
//   OVERLAY=... PORT=7801 RE1_LAB_GAME_DIR='D:\Games\RE1-decomp' node tools/harness/tests/cutscenes.ts [<scene id> ...] [--out <dir>]
//
// Needs the engine and the overlay deployed (see the brief in REBECCA_DAY.md).
// Pictures go to <dir>/<scene id>/ (default /tmp/rebecca-cutscenes). Exits 1
// if any scene fails.
import { mkdirSync } from 'node:fs';
import path from 'node:path';
import { open } from '../lab.ts';
import { Key, type GameLink } from '../link.ts';
import { faceTowards, inControl, settle } from '../flows.ts';
import { snapshot } from '../snapshot.ts';
import { Bank, flag, messageOnScreen, type GameState } from '../state.ts';
import { dayRooms } from '../../rebecca/day/rooms.ts';
import { CUT_FLAGS, CUTSCENES } from '../../rebecca/day/cutscenes.ts';
import type { Cutscene, Rect } from '../../rebecca/day/cutscene.ts';
import { EVENT_FLAGS } from '../../rebecca/day/events.ts';
import { inside, nearest, opens, read, walkable } from './floor.ts';

const args = process.argv.slice(2);
const outAt = args.indexOf('--out');
const outDir = outAt >= 0 ? args[outAt + 1]! : '/tmp/rebecca-cutscenes';
const wanted = args.filter((a, i) => !a.startsWith('--') && i !== outAt + 1);
const scenes = CUTSCENES.filter((c) => !wanted.length || wanted.includes(c.id));
if (!scenes.length) throw new Error(`no scene called ${wanted.join(', ')}`);

/** The mansion's save room is RE1's own; her day's rooms are in day/rooms.ts. */
function roomOf(slug: string): { stage: number; room: number } {
  if (slug === 'save') return { stage: 0, room: 0 };
  const r = dayRooms.find((d) => d.slug === slug);
  if (!r) throw new Error(`no room ${slug}`);
  return r;
}

const MSF_LETTERBOX = 0x10000;
/** g_message_flags 0x100, FG_6 23: her controls. */
const controls = (s: GameState) => (s.messageFlags & 0x100) !== 0;
const free = (s: GameState) => inControl(s) && !messageOnScreen(s) && !(s.msf & MSF_LETTERBOX) && controls(s);
const ran = (s: GameState, c: Cutscene) => flag(s, Bank.common, CUT_FLAGS.get(c.id)!);
const here = (s: GameState, at: { stage: number; room: number }) => s.stage === at.stage && s.room === at.room;

/** How far ahead of her the game looks for a zone she acts on. */
const REACH = 600;

/** Stand her where pressing action reaches into the zone, facing it (as puzzles.ts does). */
async function standAt(link: GameLink, slug: string, zone: Rect): Promise<void> {
  const json = read(slug)!;
  const touch = (json.doors ?? []).filter((d) => !opens(slug, d.zone)).map((d) => d.zone);
  const cx = (zone.x0 + zone.x1) / 2;
  const cz = (zone.z0 + zone.z1) / 2;
  const at = nearest(walkable(json, touch), cx, cz, ([x, z]) => {
    const d = Math.hypot(cx - x, cz - z) || 1;
    return inside(zone, x + ((cx - x) / d) * REACH, z + ((cz - z) / d) * REACH);
  });
  if (!at) throw new Error('nowhere she can stand reaches it');
  await link.place(at[0], at[1]);
  await link.frames(6);
  await faceTowards(link, cx, cz);
}

/** The zone of the check whose text starts so, from the scene's records. */
function checkZone(slug: string, text: string): Rect {
  const c = read(slug)?.checks?.find((k) => k.text.startsWith(text));
  if (!c) throw new Error(`${slug} has no check starting "${text}"`);
  return c.zone;
}

/** Set the scene off as a player would. */
async function trigger(link: GameLink, c: Cutscene, at: { stage: number; room: number }): Promise<void> {
  const t = c.trigger;
  switch (t.on) {
    case 'enter':
      await link.room(at.stage, at.room);
      return;
    case 'check':
      await standAt(link, c.room, checkZone(c.room, t.check));
      await link.tap(Key.action, 3);
      return;
    case 'zone':
      await link.place(Math.round((t.zone.x0 + t.zone.x1) / 2), Math.round((t.zone.z0 + t.zone.z1) / 2));
      return;
    case 'step':
      await link.setFlag(Bank.common, EVENT_FLAGS.get(t.step)!, true);
      return;
    default: {
      const never: never = t;
      throw new Error(`unknown trigger ${JSON.stringify(never)}`);
    }
  }
}

/** Push her about and see that she moves: forward, else back. */
async function moves(link: GameLink): Promise<boolean> {
  for (const key of [Key.up, Key.down]) {
    const before = await link.state();
    await link.down(key);
    await link.frames(20);
    await link.up(key);
    const after = await link.frames(5);
    if (Math.hypot(after.player.x - before.player.x, after.player.z - before.player.z) > 100) return true;
  }
  return false;
}

const lines = (c: Cutscene) => c.beats.filter((b) => b.kind === 'say').length;

// Boot in the ranger's cabin, which has no scene, so none starts before its checkpoint.
const cabin = roomOf('lookout');
const session = await open(Number(process.env.PORT ?? 7801), `--mode REB --boot rebecca:${cabin.stage}:${cabin.room}`);
const link = session.link;
const failures: string[] = [];
try {
  await link.waitFor((s) => s.play, 'gameplay', 120_000);
  await settle(link, () => true, 30_000);
  for (const c of scenes) {
    const at = roomOf(c.room);
    const dir = path.join(outDir, c.id);
    mkdirSync(dir, { recursive: true });
    const problems: string[] = [];
    try {
      // The checkpoint: in its room, the scene not yet run.
      await link.setFlag(Bank.common, CUT_FLAGS.get(c.id)!, false);
      if (c.trigger.on === 'step') await link.setFlag(Bank.common, EVENT_FLAGS.get(c.trigger.step)!, false);
      await link.room(at.stage, at.room);
      await settle(link, (s) => here(s, at), 60_000);
      await snapshot(link, dir, `${c.id}-00-before`);

      await trigger(link, c, at);
      // Press on through it, a picture at each line and each cut.
      const seen = new Set<number>();
      let shots = 1;
      let camera = -1;
      let calm = 0;
      const deadline = Date.now() + 240_000;
      for (;;) {
        if (Date.now() > deadline) throw new Error(`still in the scene after 4 minutes (${seen.size} lines seen)`);
        const s = await link.frames(10);
        if (ran(s, c) && free(s)) {
          if (++calm >= 3) break;
          continue;
        }
        calm = 0;
        const name = (what: string) => `${c.id}-${String(shots++).padStart(2, '0')}-${what}`;
        if (s.camera !== camera && !messageOnScreen(s)) {
          camera = s.camera;
          await snapshot(link, dir, name(`cam${camera}`));
        }
        if (messageOnScreen(s)) {
          if (!seen.has(s.messageId)) {
            seen.add(s.messageId);
            await link.frames(30); // let the text type out
            await snapshot(link, dir, name(`line${s.messageId}`));
          }
          await link.tap(Key.action, 3);
        }
      }
      const s = await link.state();
      await snapshot(link, dir, `${c.id}-99-after`);
      if (!ran(s, c)) problems.push('its flag was never set');
      if (seen.size < lines(c)) problems.push(`showed ${seen.size} of its ${lines(c)} lines`);
      if (!here(s, at)) problems.push('left its room');
      if (!(await moves(link))) problems.push("she doesn't move when pushed");

      // Back again: it doesn't run twice.
      await link.room(at.stage, at.room);
      const again = await settle(link, (st) => here(st, at), 60_000);
      if (c.trigger.on !== 'enter') await trigger(link, c, at);
      await link.frames(60);
      const later = await link.state();
      if (later.msf & MSF_LETTERBOX) problems.push('it ran again');
      void again;
    } catch (err) {
      problems.push(String(err instanceof Error ? err.message : err));
    }
    console.log(`${problems.length ? 'FAIL' : 'ok  '}  ${c.id} (${c.room})${problems.length ? `: ${problems.join('; ')}` : ''}`);
    if (problems.length) failures.push(c.id);
    // Close anything a repeat opened before the next scene.
    await settle(link, () => true, 30_000).catch(() => undefined);
  }
} finally {
  session.end();
}
console.log(failures.length ? `FAIL: ${failures.join(', ')}` : 'PASS');
process.exitCode = failures.length ? 1 : 0;
