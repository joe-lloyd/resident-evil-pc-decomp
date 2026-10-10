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
