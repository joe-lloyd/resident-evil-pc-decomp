// Reusable ways to get the game somewhere: from launch to a playable room.
import { Key, type GameLink } from './link.ts';
import { blocked, loadShapes, planPath } from './room-map.ts';
import { MSF, messageOnScreen, screen, type GameState } from './state.ts';

export type Character = 'chris' | 'jill';

/** The player can move: gameplay running, no message, menu, movie or transition. */
export function inControl(s: GameState): boolean {
  return screen(s) === 'gameplay' && !(s.msf & (MSF.cameraLock | MSF.fadeActive));
}

/**
 * Title screen to the first moment the player has control, pressing through
 * the intro text, menus, the opening movie and the opening cutscene.
 * The title screen reports title == 1 (g_titleMode).
 */
export async function newGame(link: GameLink, character: Character = 'chris'): Promise<GameState> {
  // The intro text before the title waits for a key on a fresh launch.
  // Enter skips it and does nothing on the title screen itself.
  const titleBy = Date.now() + 180_000;
  while (!(await link.frames(20)).title) {
    if (Date.now() > titleBy) throw new Error('the title screen never appeared');
    await link.tap(Key.enter, 3);
  }
  await link.frames(30);
  await link.tap(Key.action, 3); // PRESS START BUTTON
  await link.frames(45);
  await link.tap(Key.action, 3); // NEW GAME
  await link.frames(90);
  if (character === 'jill') {
    await link.tap(Key.right, 3);
    await link.frames(45);
  }
  await link.tap(Key.action, 3); // choose the character

  // Press on through the movie and the scripted opening until the player
  // stands in a room with nothing on screen for a full second.
  const deadline = Date.now() + 240_000;
  let calm = 0;
  for (;;) {
    if (Date.now() > deadline) throw new Error('never got control after a new game');
    const s = await link.frames(15);
    if (inControl(s) && !messageOnScreen(s)) {
      // Three calm looks (45 frames): a room script opens its arrival
      // message a moment after the room starts playing.
      if (++calm >= 3) return s;
      continue;
    }
    calm = 0;
    // Movies and messages advance on the action key; scripted cameras pass
    // on their own, and an extra press there is harmless.
    await link.tap(s.fmv ? Key.run : Key.action, 3);
  }
}

/**
 * Press through messages and scripted scenes until the player has control in
 * a room matching `where`, for at least two checks in a row.
 */
export async function settle(
  link: GameLink,
  where: (s: GameState) => boolean = () => true,
  timeoutMs = 120_000,
): Promise<GameState> {
  const deadline = Date.now() + timeoutMs;
  let calm = 0;
  for (;;) {
    if (Date.now() > deadline) throw new Error('the player never got control');
    const s = await link.frames(15);
    if (where(s) && inControl(s) && !messageOnScreen(s)) {
      // Three calm looks (45 frames): a room script opens its arrival
      // message a moment after the room starts playing.
      if (++calm >= 3) return s;
      continue;
    }
    calm = 0;
    if (messageOnScreen(s)) await link.tap(Key.action, 3);
    // An item pickup or the status screen: back out with cancel.
    else if (screen(s) === 'menu') await link.tap(Key.run, 3);
  }
}

/**
 * Folders holding Stage1..Stage7 room files for path planning, the overlay
 * build first so its changed rooms win. Tests set it with useRoomData.
 */
let roomDataDirs: string[] = [process.env.RE1_DATA ?? '/tmp/re1-pc'];

export function useRoomData(dirs: string[]): void {
  roomDataDirs = dirs;
}

/** When on, walking stops to shoot any live enemy that comes within this range. */
let fightBackRange = 0;

export function useFightBack(range = 9000): void {
  fightBackRange = range;
}

export class StuckError extends Error {
  readonly state: GameState;
  constructor(message: string, state: GameState) {
    super(message);
    this.state = state;
  }
}

/**
 * The angle (0-4095) the player must face to head towards (x, z). The player
 * moves along (cos a, -sin a) with a = angle * 2pi / 4096, measured in game.
 */
export function headingTo(fromX: number, fromZ: number, x: number, z: number): number {
  const a = Math.atan2(-(z - fromZ), x - fromX);
  return Math.round(((a * 2048) / Math.PI + 4096) % 4096);
}

/** Signed shortest turn from `from` to `to`, in (-2048, 2048]. */
export function turnBetween(from: number, to: number): number {
  let d = (to - from) % 4096;
  if (d > 2048) d -= 4096;
  if (d <= -2048) d += 4096;
  return d;
}

/**
 * Walk to within `radius` of (x, z) with tank controls: turn to face the
 * target, walk a few frames, look again. Right turns raise the angle, at about
 * 200 units a frame. Throws StuckError when the distance stops shrinking.
 */
export async function walkTo(
  link: GameLink,
  x: number,
  z: number,
  { radius = 500, timeoutMs = 30_000 }: { radius?: number; timeoutMs?: number } = {},
): Promise<GameState> {
  const deadline = Date.now() + timeoutMs;
  let best = Infinity;
  let sinceBest = 0;
  const first = await link.state();
  for (;;) {
    let s = await link.state();
    checkAlive(s);
    // A door that fires on touch (or a scripted move) can change the room
    // mid-walk; the target means nothing in the new room.
    if (s.stage !== first.stage || s.room !== first.room) return s;
    if (fightBackRange > 0 && s.enemies.some((e) => e.hp > 0 && e.type < FIRST_NPC_TYPE && Math.hypot(e.x - s.player.x, e.z - s.player.z) < fightBackRange)) {
      await fight(link, { range: fightBackRange + 3000 });
      s = await link.state();
      best = Infinity; // fighting moves her; judge progress afresh
    }
    const dist = Math.hypot(x - s.player.x, z - s.player.z);
    if (process.env.HARNESS_TRACE === '2') {
      console.log(`    walk ${s.stage}:${s.room.toString(16)} (${s.player.x}, ${s.player.z}) angle ${s.player.angle} hp ${s.player.hp} ${screen(s)} msf ${s.msf.toString(16)} -> (${Math.round(x)}, ${Math.round(z)}) dist ${Math.round(dist)} enemies ${JSON.stringify(s.enemies.map((e) => [e.type, e.hp, e.x, e.z]))}`);
    }
    if (dist <= radius) return s;
    if (Date.now() > deadline) throw new StuckError(`never reached (${x}, ${z}); ${Math.round(dist)} away`, s);
    if (dist < best - 50) {
      best = dist;
      sinceBest = 0;
    } else if (++sinceBest > 12) {
      throw new StuckError(`stuck ${Math.round(dist)} from (${x}, ${z}) at (${s.player.x}, ${s.player.z})`, s);
    }
    const turn = turnBetween(s.player.angle, headingTo(s.player.x, s.player.z, x, z));
    if (Math.abs(turn) > 150) {
      await face(link, headingTo(s.player.x, s.player.z, x, z));
    } else {
      await link.tap(Key.up, dist > 2500 ? 10 : 4);
      await link.frames(dist > 2500 ? 10 : 5);
    }
  }
}

/** Turn on the spot until facing `angle` (within `tolerance`), re-reading each step. */
export async function face(link: GameLink, angle: number, tolerance = 100): Promise<GameState> {
  for (let i = 0; i < 40; i++) {
    const s = await link.state();
    const turn = turnBetween(s.player.angle, angle);
    if (Math.abs(turn) <= tolerance) return s;
    await link.tap(turn > 0 ? Key.right : Key.left, Math.abs(turn) > 600 ? 3 : 1);
    await link.frames(4);
  }
  throw new StuckError(`could not face ${angle}`, await link.state());
}

/** Face the point (x, z). */
export async function faceTowards(link: GameLink, x: number, z: number): Promise<GameState> {
  const s = await link.state();
  return face(link, headingTo(s.player.x, s.player.z, x, z));
}

type Zone = { x: number; z: number; w: number; d: number };

/**
 * Walk up to a zone (a door, a switch, a piano): to the open spot inside it
 * nearest to the player, or, when it lies wholly inside a wall or furniture,
 * to the open spot just outside it nearest its middle. Then face its middle,
 * where the engine's action probe (600 ahead) lands. Returns the state, which
 * may be in another room if a touch door fired on the way.
 */
export async function approach(link: GameLink, zone: Zone): Promise<GameState> {
  const start = await link.state();
  const cx = zone.x + zone.w / 2;
  const cz = zone.z + zone.d / 2;
  const shapes = loadShapes(roomDataDirs, start.stage, start.room, start.player.cf);
  const reach = 350;
  const toZone = (x: number, z: number) =>
    Math.hypot(Math.max(zone.x - x, 0, x - (zone.x + zone.w)), Math.max(zone.z - z, 0, z - (zone.z + zone.d)));
  let target = { x: cx, z: cz };
  let inside = Infinity;
  let outside = Infinity;
  let outsideTarget: { x: number; z: number } | undefined;
  for (let x = zone.x - reach; x < zone.x + zone.w + reach; x += 150) {
    for (let z = zone.z - reach; z < zone.z + zone.d + reach; z += 150) {
      if (blocked(shapes, x, z)) continue;
      const off = toZone(x, z);
      if (off === 0) {
        const d = Math.hypot(x - start.player.x, z - start.player.z);
        if (d < inside) {
          inside = d;
          target = { x, z };
        }
      } else if (off <= reach) {
        const d = Math.hypot(x - cx, z - cz);
        if (d < outside) {
          outside = d;
          outsideTarget = { x, z };
        }
      }
    }
  }
  if (inside === Infinity && outsideTarget) target = outsideTarget;
  let arrived: GameState;
  try {
    arrived = await goTo(link, roomDataDirs, target.x, target.z, { radius: 250 });
  } catch (err) {
    // Furniture objects block her where the room's collision map does not;
    // stuck close to the zone is close enough for the action probe.
    if (!(err instanceof StuckError) || err instanceof DiedError || toZone(err.state.player.x, err.state.player.z) > 800) throw err;
    arrived = err.state;
  }
  if (arrived.stage !== start.stage || arrived.room !== start.room) return arrived;
  return faceTowards(link, cx, cz);
}

/** Walk up to a zone, press action once and let whatever opens close. */
export async function check(link: GameLink, zone: Zone): Promise<GameState> {
  await approach(link, zone);
  await link.tap(Key.action, 3);
  await link.frames(20);
  return settle(link);
}

/**
 * Go through a door: walk up to its zone (the box door_aot_set gives), face
 * into it and press action until the room changes.
 */
export async function useDoor(
  link: GameLink,
  zone: Zone,
  timeoutMs = 60_000,
): Promise<GameState> {
  const start = await link.state();
  const cx = zone.x + zone.w / 2;
  const cz = zone.z + zone.d / 2;
  const arrived = await approach(link, zone);
  if (arrived.stage !== start.stage || arrived.room !== start.room) {
    return settle(link, (st) => st.room === arrived.room && st.stage === arrived.stage);
  }
  const deadline = Date.now() + timeoutMs;
  for (;;) {
    await link.tap(Key.action, 3);
    const s = await link.frames(20);
    if (s.room !== start.room || s.stage !== start.stage) {
      if (process.env.HARNESS_TRACE) console.log(`  door: ${start.stage}:${start.room.toString(16)} -> ${s.stage}:${s.room.toString(16)} from (${start.player.x}, ${start.player.z})`);
      return settle(link, (st) => st.room === s.room && st.stage === s.stage);
    }
    if (Date.now() > deadline) throw new StuckError('the door never opened', s);
    if (messageOnScreen(s) || screen(s) === 'menu') {
      // Something other than the door answered (an item, a note): take it,
      // close whatever opened, face the door again.
      await settle(link);
      await faceTowards(link, cx, cz);
      continue;
    }
    // Face a little to each side in case the door is not straight ahead.
    await link.tap(Key.left, 1);
  }
}

/**
 * walkTo with detours: when the straight line is blocked, back off, try a
 * heading 60 degrees to either side for a short walk, and go again. Rooms are
 * mostly corridors and furniture, so this gets round corners without a map.
 */
export async function navigate(
  link: GameLink,
  x: number,
  z: number,
  { radius = 500, tries = 8 }: { radius?: number; tries?: number } = {},
): Promise<GameState> {
  let side = 1;
  for (let i = 0; ; i++) {
    try {
      return await walkTo(link, x, z, { radius, timeoutMs: 40_000 });
    } catch (err) {
      if (!(err instanceof StuckError) || i >= tries) throw err;
      const s = err.state;
      const direct = headingTo(s.player.x, s.player.z, x, z);
      await link.tap(Key.down, 8);
      await link.frames(10);
      await face(link, (direct + side * 683 + 4096) % 4096);
      await link.tap(Key.up, 15);
      await link.frames(18);
      side = -side;
    }
  }
}

/**
 * Walk to (x, z) along a path planned from the room's collision data
 * (room-map.ts). `dataDirs` are the folders holding Stage1..Stage7 room files,
 * the overlay first. Falls back to detours between waypoints.
 */
export async function goTo(
  link: GameLink,
  dataDirs: string[],
  x: number,
  z: number,
  { radius = 400, log = false }: { radius?: number; log?: boolean } = {},
): Promise<GameState> {
  const s = await link.state();
  const path = planPath(loadShapes(dataDirs, s.stage, s.room, s.player.cf), s.player.x, s.player.z, x, z);
  if (!path) throw new StuckError(`no path to (${x}, ${z}) in this room`, s);
  if (log) console.log(`  path ${path.map((p) => `(${Math.round(p.x)},${Math.round(p.z)})`).join(' ')}`);
  let last = s;
  for (const [i, p] of path.entries()) {
    last = await navigate(link, p.x, p.z, { radius: i === path.length - 1 ? radius : 350, tries: 4 });
    if (last.stage !== s.stage || last.room !== s.room) return last;
  }
  return last;
}

/** The player died (health 0 or the game's dead flag). */
export class DiedError extends StuckError {}

function checkAlive(s: GameState): void {
  if (s.player.hp <= 0 || (s.msf & MSF.playerDead) !== 0) throw new DiedError(`she died in room ${s.stage}:${s.room.toString(16)}`, s);
}

/**
 * Shoot every live enemy within `range` (the default covers any room), nearest
 * first, one step at a time: face it with aim released, hold aim, fire.
 * RE1 turns the held aim onto the nearest enemy in front by itself. A target
 * out of shooting range is waited for, since dogs charge; one that does not
 * come closer within a few seconds is walked towards. A zombie in grabbing
 * distance is backed away from. When three shots in a row
 * leave its health unchanged she turns to it again. Returns the shots fired.
 * Needs a gun equipped.
 */
/** Item 0x0B, the Beretta's ammunition. */
const CLIP = 0x0b;
/** Enemies that leap about, so most shots at range miss: the dog (2) and the Hunter (6). */
const LEAPERS = [2, 6];
/** Types from 32 up are people (Chris 32, Rebecca 35, Wesker 36, Richard 39), not enemies. */
const FIRST_NPC_TYPE = 32;

export async function fight(
  link: GameLink,
  { range = 40_000, timeoutMs = 120_000 }: { range?: number; timeoutMs?: number } = {},
): Promise<number> {
  const deadline = Date.now() + timeoutMs;
  let shots = 0;
  let aiming = false;
  let misses = 0;
  let waitedFrom: { d: number; at: number } | undefined;
  const release = async () => {
    if (aiming) await link.up(Key.aim);
    aiming = false;
  };
  try {
    for (;;) {
      const s = await link.state();
      checkAlive(s);
      const live = s.enemies
        .filter((e) => e.hp > 0 && e.type < FIRST_NPC_TYPE)
        .map((e) => ({ e, d: Math.hypot(e.x - s.player.x, e.z - s.player.z) }))
        .filter((t) => t.d <= range)
        .sort((a, b) => a.d - b.d);
      if (live.length === 0) return shots;
      if (Date.now() > deadline) throw new StuckError(`${live.length} enemies still standing`, s);
      const { e: target, d } = live[0];
      const off = Math.abs(turnBetween(s.player.angle, headingTo(s.player.x, s.player.z, target.x, target.z)));
      if (process.env.HARNESS_TRACE) console.log(`    fight type ${target.type} hp ${target.hp} at ${Math.round(d)} off ${off} her hp ${s.player.hp} shots ${shots}`);

      // Dogs and Hunters leap about and most shots at them miss until they
      // close in; zombies walk straight on and can be hit from further away.
      const shootRange = LEAPERS.includes(target.type) ? 3500 : 7000;
      if (d > shootRange) {
        // Out of reach: wait aimed for it to come, then go to it.
        if (!waitedFrom || d < waitedFrom.d - 500) waitedFrom = { d, at: Date.now() };
        if (Date.now() - waitedFrom.at < 4000) {
          if (!aiming || off > 300) {
            await release();
            await faceTowards(link, target.x, target.z).catch(() => undefined);
            await link.down(Key.aim);
            aiming = true;
          }
          await link.frames(6);
        } else {
          await release();
          await faceTowards(link, target.x, target.z).catch(() => undefined);
          await link.tap(Key.up, 12);
          await link.frames(12);
        }
        continue;
      }
      waitedFrom = undefined;
      // player.weapon is the 1-based slot of the gun in hand.
      const rounds = (s.items[s.player.weapon - 1]?.qty ?? 0) + s.items.filter((it) => it.id === CLIP).reduce((n, it) => n + it.qty, 0);
      if (rounds === 0) throw new StuckError(`out of ammo with ${live.length} enemies standing`, s);
      if (!LEAPERS.includes(target.type) && d < 1800) {
        // Close enough to grab her: step back before the next shot.
        await release();
        await faceTowards(link, target.x, target.z).catch(() => undefined);
        await link.tap(Key.down, 10);
        await link.frames(10);
        continue;
      }
      if (!aiming || off > 500 || misses >= 3) {
        await release();
        await faceTowards(link, target.x, target.z).catch(() => undefined);
        await link.down(Key.aim);
        aiming = true;
        misses = 0;
        await link.frames(6);
      }
      const before = target.hp;
      await link.tap(Key.action, 3);
      shots++;
      const after = await link.frames(16);
      const same = after.enemies.find((e) => e.type === target.type && Math.hypot(e.x - target.x, e.z - target.z) < 2500);
      misses = same && same.hp === before ? misses + 1 : 0;
    }
  } finally {
    await release();
  }
}
