// Reusable ways to get the game somewhere: from launch to a playable room.
import { Key, type GameLink } from './link.ts';
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
      if (++calm >= 2) return s;
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
      if (++calm >= 2) return s;
      continue;
    }
    calm = 0;
    if (messageOnScreen(s)) await link.tap(Key.action, 3);
  }
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
  for (;;) {
    const s = await link.state();
    const dist = Math.hypot(x - s.player.x, z - s.player.z);
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

/**
 * Go through a door: walk into its zone (the box door_aot_set gives), face
 * into it and press action until the room changes.
 */
export async function useDoor(
  link: GameLink,
  zone: { x: number; z: number; w: number; d: number },
  timeoutMs = 60_000,
): Promise<GameState> {
  const start = await link.state();
  const cx = zone.x + zone.w / 2;
  const cz = zone.z + zone.d / 2;
  // Door zones run into the wall, so aim for the nearest point just inside the
  // zone rather than its middle, then face the middle (the door).
  const inset = 250;
  const tx = Math.min(Math.max(start.player.x, zone.x + inset), zone.x + zone.w - inset);
  const tz = Math.min(Math.max(start.player.z, zone.z + inset), zone.z + zone.d - inset);
  await walkTo(link, tx, tz, { radius: 200 });
  await faceTowards(link, cx, cz);
  const deadline = Date.now() + timeoutMs;
  for (;;) {
    await link.tap(Key.action, 3);
    const s = await link.frames(20);
    if (s.room !== start.room || s.stage !== start.stage) return settle(link, (st) => st.room === s.room && st.stage === s.stage);
    if (Date.now() > deadline) throw new StuckError('the door never opened', s);
    // Face a little to each side in case the door is not straight ahead.
    await link.tap(Key.left, 1);
  }
}
