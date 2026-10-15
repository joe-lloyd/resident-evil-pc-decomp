// Reusable ways to get the game somewhere: from launch to a playable room.
import { choice } from './jev.ts';
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
let fightBackIgnores: readonly number[] = [];

/** Fight what comes within `range` while walking, except enemy types in `ignore` (snakes: walk past them). */
export function useFightBack(range = 9000, ignore: readonly number[] = []): void {
  fightBackRange = range;
  fightBackIgnores = ignore;
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

/** Walking, or running: the run key held with forward, about twice as fast. */
export type Pace = 'walk' | 'run';

/** The keys each game has held down, so a walk changes only what it must and can hand them to the next leg. */
const heldKeys = new WeakMap<GameLink, Set<number>>();

/** Hold exactly `want`: let go of the others, press the new ones. */
async function hold(link: GameLink, want: readonly number[]): Promise<void> {
  const held = heldKeys.get(link) ?? heldKeys.set(link, new Set()).get(link)!;
  for (const k of [...held]) if (!want.includes(k)) {
    held.delete(k);
    await link.up(k);
  }
  for (const k of want) if (!held.has(k)) {
    held.add(k);
    await link.down(k);
  }
}

/** The next state line after `s`, or a fresh one if the game sends none (she stands still). */
async function after(link: GameLink, s: GameState): Promise<GameState> {
  try {
    return await link.waitFor((t) => t.frame > s.frame, 'the next frame', 300);
  } catch {
    return link.state();
  }
}

/** Frames between sending a key and seeing her answer it, over the tunnel. */
const LAG = 3;
/** Within this of the goal a run drops to a walk, so she stops where she means to. */
const BRAKE = 1500;
/**
 * A turn wider than this (about 25 degrees) is made standing; narrower ones
 * while moving. Walking, she turns about 40 angle units a frame and covers
 * about 80 game units, so a wide turn on the move is a wide curve into the
 * furniture.
 */
const STANDING_TURN = 300;

/**
 * Walk or run to within `radius` of (x, z) with tank controls, the way a
 * player does: forward held all the way, steering with left and right as she
 * goes, and only a wide turn made on the spot. Short corrections are taps of
 * a frame or two, so she doesn't weave. With `carryOn` the keys stay held at
 * the goal, for the next leg of a path. Throws StuckError when the distance
 * stops shrinking.
 */
export async function walkTo(
  link: GameLink,
  x: number,
  z: number,
  { radius = 500, timeoutMs = 30_000, pace = 'walk', carryOn = false }: { radius?: number; timeoutMs?: number; pace?: Pace; carryOn?: boolean } = {},
): Promise<GameState> {
  const deadline = Date.now() + timeoutMs;
  let best = Infinity;
  let bestFrame = 0;
  let speed = 0;
  let tapUntil = 0;
  const first = await link.state();
  let s = first;
  let prev = first;
  try {
    for (;;) {
      s = await after(link, s);
      if (screen(s) === 'transition') {
        await hold(link, []);
        s = await throughTransition(link, s);
      }
      checkAlive(s);
      // A door that fires on touch (or a scripted move) can change the room
      // mid-walk; the target means nothing in the new room.
      if (s.stage !== first.stage || s.room !== first.room) {
        await hold(link, []);
        return s;
      }
      if (fightBackRange > 0 && s.enemies.some((e) => e.hp > 0 && e.type < FIRST_NPC_TYPE && !fightBackIgnores.includes(e.type) && Math.hypot(e.x - s.player.x, e.z - s.player.z) < fightBackRange)) {
        await hold(link, []);
        await fight(link, { range: fightBackRange + 3000, ignore: fightBackIgnores });
        s = await link.state();
        best = Infinity; // fighting moves her; judge progress afresh
      }
      const frames = Math.max(1, s.frame - prev.frame);
      speed = 0.6 * speed + 0.4 * (Math.hypot(s.player.x - prev.player.x, s.player.z - prev.player.z) / frames);
      prev = s;
      const dist = Math.hypot(x - s.player.x, z - s.player.z);
      if (process.env.HARNESS_TRACE === '2') {
        console.log(`    ${pace} ${s.stage}:${s.room.toString(16)} f${s.frame} (${s.player.x}, ${s.player.z}) angle ${s.player.angle} speed ${speed.toFixed(0)} -> (${Math.round(x)}, ${Math.round(z)}) dist ${Math.round(dist)}`);
      }
      // She keeps going for LAG frames after the key comes up.
      if (dist <= radius + (carryOn ? 0 : speed * LAG)) {
        if (!carryOn) {
          await hold(link, []);
          s = await link.frames(LAG + 2);
        }
        return s;
      }
      if (Date.now() > deadline) throw new StuckError(`never reached (${x}, ${z}); ${Math.round(dist)} away`, s);
      if (dist < best - 50) {
        best = dist;
        bestFrame = s.frame;
      } else if (s.frame - bestFrame > 45) {
        throw new StuckError(`stuck ${Math.round(dist)} from (${x}, ${z}) at (${s.player.x}, ${s.player.z})`, s);
      }
      const turn = turnBetween(s.player.angle, headingTo(s.player.x, s.player.z, x, z));
      const side = turn > 0 ? Key.right : Key.left;
      if (Math.abs(turn) > STANDING_TURN) {
        await hold(link, [side]);
        continue;
      }
      const forward = pace === 'run' && dist > BRAKE ? [Key.up, Key.run] : [Key.up];
      if (Math.abs(turn) > 150) {
        await hold(link, [...forward, side]);
      } else {
        await hold(link, forward);
        // A small correction: a tap of a frame or two, then wait to see it land.
        if (Math.abs(turn) > 60 && s.frame >= tapUntil) {
          const n = Math.min(3, Math.max(1, Math.round(Math.abs(turn) / 40)));
          await link.tap(side, n);
          tapUntil = s.frame + n + LAG;
        }
      }
    }
  } catch (err) {
    await hold(link, []);
    throw err;
  }
}

/**
 * Run or walk? Jev decides from a short account of the way ahead: how far it
 * is, how many sharp corners, who is near it, how hurt she is. Without a Jev
 * key she runs, which is what a player does by default.
 */
export async function choosePace(s: GameState, path: readonly { x: number; z: number }[]): Promise<Pace> {
  if (!process.env.TYPESAFE_API_KEY) return 'run';
  const points = [{ x: s.player.x, z: s.player.z }, ...path];
  let length = 0;
  let corners = 0;
  for (let i = 1; i < points.length; i++) {
    length += Math.hypot(points[i]!.x - points[i - 1]!.x, points[i]!.z - points[i - 1]!.z);
    if (i >= 2) {
      const a = headingTo(points[i - 2]!.x, points[i - 2]!.z, points[i - 1]!.x, points[i - 1]!.z);
      const b = headingTo(points[i - 1]!.x, points[i - 1]!.z, points[i]!.x, points[i]!.z);
      if (Math.abs(turnBetween(a, b)) > 512) corners++;
    }
  }
  const metres = (u: number) => Math.round((u / UNITS_PER_METRE) * 10) / 10;
  // How close each live enemy comes to the way, in metres.
  const nearWay = (e: { x: number; z: number }) =>
    Math.min(...points.slice(1).map((p, i) => segmentDistance(e, points[i]!, p)));
  const enemies = s.enemies
    .filter((e) => e.hp > 0 && e.type < FIRST_NPC_TYPE)
    .map((e) => ({ kind: ENEMY_NAMES[e.type] ?? `enemy type ${e.type}`, metresFromHer: metres(Math.hypot(e.x - s.player.x, e.z - s.player.z)), metresFromTheWay: metres(nearWay(e)) }));
  const state = {
    game: 'Resident Evil (1996), tank controls, fixed cameras',
    her: { name: 'Rebecca', health: `${s.player.hp} of ${s.player.maxHp}` },
    way: { metres: metres(length), sharpCorners: corners },
    enemies,
  };
  try {
    const a = await choice(
      state,
      'Rebecca is about to cross part of a room to a spot she needs. Should she run or walk there? Running is about twice as fast, but she turns wide and can stop short of nothing, so she can overshoot in tight corners or brush past a monster that gets a hit in.',
      {
        run: 'Run: the way is more than a few metres and no monster is close to it, or a monster is close to her and getting away matters most.',
        walk: 'Walk: the way is short or turns sharply through a cramped space, or a monster stands right beside the way and she must pass it under control.',
      },
    );
    if (process.env.HARNESS_TRACE) console.log(`  Jev: ${a.choice} (run ${a.probabilities.run.toFixed(2)}) for ${JSON.stringify({ way: state.way, enemies })}`);
    return a.choice;
  } catch (err) {
    console.log(`  Jev could not choose a pace (${String(err).slice(0, 120)}); running`);
    return 'run';
  }
}

/** Shortest distance from `p` to the segment a-b. */
function segmentDistance(p: { x: number; z: number }, a: { x: number; z: number }, b: { x: number; z: number }): number {
  const dx = b.x - a.x;
  const dz = b.z - a.z;
  const t = Math.max(0, Math.min(1, ((p.x - a.x) * dx + (p.z - a.z) * dz) / (dx * dx + dz * dz || 1)));
  return Math.hypot(p.x - (a.x + t * dx), p.z - (a.z + t * dz));
}

/** Game units in a metre, as Rebecca's rooms are built (reb.UNITS). */
const UNITS_PER_METRE = 1700;
/** RE1's enemy types by number, for Jev's account of the room (retro-archive-explorer's scd1.ts ENEMY_NAMES). */
const ENEMY_NAMES: readonly string[] = [
  'zombie', 'zombie', 'dog (Cerberus)', 'giant spider', 'giant spider', 'crow', 'Hunter', 'wasp', 'Plant 42', 'Chimera', 'snake (Adder)', 'shark', 'Tyrant',
  'giant snake', 'Plant 42 roots', 'plant', 'Tyrant', 'zombie',
];

/**
 * If a door or a walk between rooms is playing, wait for it to finish: she
 * has no control until then. Returns the state after (perhaps in another room).
 */
async function throughTransition(link: GameLink, s: GameState): Promise<GameState> {
  if (screen(s) !== 'transition') return s;
  return link.waitFor((st) => screen(st) !== 'transition', 'the way into the next room', 60_000);
}

/** Turn on the spot until facing `angle` (within `tolerance`), re-reading each step. */
export async function face(link: GameLink, angle: number, tolerance = 100): Promise<GameState> {
  const start = await link.state();
  for (let i = 0; i < 40; i++) {
    const s = await throughTransition(link, await link.state());
    // A touch door fired as she turned: the angle meant the room she left.
    if (s.stage !== start.stage || s.room !== start.room) return s;
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
 * Use an item from the status screen, as a player does: open it, move the
 * cursor to the item (it starts on slot 0; slots run two to a row) and pick
 * USE, the first entry of the item's menu. Returns once she has control again,
 * with any message the use opened closed.
 */
export async function useItem(link: GameLink, id: number): Promise<GameState> {
  const s = await link.state();
  const slot = s.items.findIndex((it) => it.id === id);
  if (slot < 0) throw new StuckError(`she has no item ${id}`, s);
  await link.tap(Key.menu, 3);
  await link.waitFor((st) => st.menuState === 1, 'the status screen', 15_000);
  await link.frames(30);
  for (let row = 0; row < slot >> 1; row++) {
    await link.tap(Key.down, 3);
    await link.frames(8);
  }
  if (slot & 1) {
    await link.tap(Key.right, 3);
    await link.frames(8);
  }
  await link.tap(Key.action, 3); // the item's menu
  await link.frames(15);
  await link.tap(Key.action, 3); // USE
  await link.frames(30);
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
  { radius = 500, tries = 8, pace = 'walk', carryOn = false }: { radius?: number; tries?: number; pace?: Pace; carryOn?: boolean } = {},
): Promise<GameState> {
  let side = 1;
  for (let i = 0; ; i++) {
    try {
      return await walkTo(link, x, z, { radius, timeoutMs: 40_000, pace, carryOn });
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
  { radius = 400, log = false, pace }: { radius?: number; log?: boolean; pace?: Pace } = {},
): Promise<GameState> {
  const s = await link.state();
  const path = planPath(loadShapes(dataDirs, s.stage, s.room, s.player.cf), s.player.x, s.player.z, x, z);
  if (!path) throw new StuckError(`no path to (${x}, ${z}) in this room`, s);
  const chosen = pace ?? (await choosePace(s, path));
  if (log || process.env.HARNESS_TRACE) console.log(`  ${chosen} ${path.map((p) => `(${Math.round(p.x)},${Math.round(p.z)})`).join(' ')}`);
  let last = s;
  for (const [i, p] of path.entries()) {
    const end = i === path.length - 1;
    // The keys stay down between legs, so the path is one movement, not a stop at every corner.
    last = await navigate(link, p.x, p.z, { radius: end ? radius : 350, tries: 4, pace: chosen, carryOn: !end });
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
  { range = 40_000, timeoutMs = 120_000, ignore = [] }: { range?: number; timeoutMs?: number; ignore?: readonly number[] } = {},
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
        .filter((e) => e.hp > 0 && e.type < FIRST_NPC_TYPE && !ignore.includes(e.type))
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
