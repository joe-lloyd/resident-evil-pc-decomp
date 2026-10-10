// The game's test-mode state line, parsed once at the boundary, plus the pure
// readings the tests use. Field meanings: src/game/TestMode.cpp and
// docs/TEST_MODE.md.

export interface Player {
  id: number;
  x: number;
  y: number;
  z: number;
  angle: number;
  hp: number;
  maxHp: number;
  weapon: number;
}

export interface Enemy {
  type: number;
  status: number;
  x: number;
  y: number;
  z: number;
  hp: number;
}

export interface GameState {
  frame: number;
  /** game_loop's inner loop ran this frame: the game is in a room, not a menu screen. */
  play: boolean;
  msf: number;
  msf2: number;
  title: number;
  fmv: boolean;
  debugMenu: boolean;
  stage: number;
  room: number;
  camera: number;
  cut: number;
  charModel: number;
  player: Player;
  items: { id: number; qty: number }[];
  enemies: Enemy[];
  messageChoice: number;
  messageId: number;
  banks: Uint8Array[];
}

export type Reply =
  | { t: 'state'; state: GameState }
  | { t: 'ack'; cmd: string; ok: boolean; frame: number }
  | { t: 'pong'; token: string; frame: number };

class ParseError extends Error {}

function obj(v: unknown, what: string): Record<string, unknown> {
  if (typeof v !== 'object' || v === null || Array.isArray(v)) throw new ParseError(`${what}: not an object`);
  return v as Record<string, unknown>;
}

function num(o: Record<string, unknown>, key: string): number {
  const v = o[key];
  if (typeof v !== 'number' || !Number.isFinite(v)) throw new ParseError(`${key}: not a number`);
  return v;
}

function str(o: Record<string, unknown>, key: string): string {
  const v = o[key];
  if (typeof v !== 'string') throw new ParseError(`${key}: not a string`);
  return v;
}

function numbers(v: unknown, what: string, length: number): number[] {
  if (!Array.isArray(v) || v.length !== length || !v.every((n) => typeof n === 'number')) {
    throw new ParseError(`${what}: expected ${length} numbers`);
  }
  return v as number[];
}

function hexBytes(v: unknown, what: string): Uint8Array {
  if (typeof v !== 'string' || v.length % 2 !== 0 || !/^[0-9a-f]*$/.test(v)) throw new ParseError(`${what}: bad hex`);
  return Uint8Array.from(v.match(/../g) ?? [], (h) => parseInt(h, 16));
}

function parseGameState(o: Record<string, unknown>): GameState {
  const p = obj(o.player, 'player');
  const msg = obj(o.msg, 'msg');
  if (!Array.isArray(o.items) || !Array.isArray(o.enemies) || !Array.isArray(o.banks)) {
    throw new ParseError('items, enemies and banks must be arrays');
  }
  return {
    frame: num(o, 'frame'),
    play: num(o, 'play') !== 0,
    msf: parseInt(str(o, 'msf'), 16),
    msf2: parseInt(str(o, 'msf2'), 16),
    title: num(o, 'title'),
    fmv: num(o, 'fmv') !== 0,
    debugMenu: num(o, 'dbg') !== 0,
    stage: num(o, 'stage'),
    room: num(o, 'room'),
    camera: num(o, 'cam'),
    cut: num(o, 'cut'),
    charModel: num(o, 'charModel'),
    player: {
      id: num(p, 'id'),
      x: num(p, 'x'),
      y: num(p, 'y'),
      z: num(p, 'z'),
      angle: num(p, 'angle'),
      hp: num(p, 'hp'),
      maxHp: num(p, 'maxHp'),
      weapon: num(p, 'weapon'),
    },
    items: o.items.map((it, i) => {
      const [id, qty] = numbers(it, `items[${i}]`, 2);
      return { id, qty };
    }),
    enemies: o.enemies.map((e, i) => {
      const [type, status, x, y, z, hp] = numbers(e, `enemies[${i}]`, 6);
      return { type, status, x, y, z, hp };
    }),
    messageChoice: num(msg, 'choice'),
    messageId: num(msg, 'id'),
    banks: o.banks.map((b, i) => hexBytes(b, `banks[${i}]`)),
  };
}

/** Parse one line from the game. Throws on anything that is not a known reply. */
export function parseReply(line: string): Reply {
  const o = obj(JSON.parse(line), 'reply');
  const t = str(o, 't');
  switch (t) {
    case 'state':
      return { t, state: parseGameState(o) };
    case 'ack':
      return { t, cmd: str(o, 'cmd'), ok: num(o, 'ok') === 1, frame: num(o, 'frame') };
    case 'pong':
      return { t, token: str(o, 'token'), frame: num(o, 'frame') };
    default:
      throw new ParseError(`unknown reply type ${t}`);
  }
}

// --- Readings ----------------------------------------------------------------

/**
 * Main state flags, from src/Globals.h. MSF_GAMEPLAY_ACTIVE (0x02000000) is
 * left out on purpose: game_loop clears it as soon as its frame loop starts,
 * so it does not mean "in gameplay"; use GameState.play.
 */
export const MSF = {
  doorTransition: 0x00000080,
  menuPending: 0x00007f00,
  menuActive: 0x00008000,
  voicePlaying: 0x00020000,
  fmvRequest: 0x00040000,
  cameraLock: 0x00100000,
  charVariant: 0x00800000,
  playerDead: 0x01000000,
  roomTransition: 0x04000000,
  fadeActive: 0x20000000,
} as const;

/** Script flag banks, numbered as cmd_bit_test numbers them. */
export const Bank = {
  scenario: 0,
  common: 1,
  locks: 2,
  enemies: 3,
  system: 4,
  mainState: 5,
  message: 6,
  roomItems: 7,
  room: 8,
  itemUse: 9,
} as const;

/** A script flag, using the game's bit order: index 0 is the top bit of word 0. */
export function flag(s: GameState, bank: number, index: number): boolean {
  const bytes = s.banks[bank];
  const at = (index >> 5) * 4;
  if (!bytes || at + 4 > bytes.length) throw new RangeError(`flag ${bank}:${index} is outside the bank`);
  const word = (bytes[at] | (bytes[at + 1] << 8) | (bytes[at + 2] << 16) | (bytes[at + 3] << 24)) >>> 0;
  return ((word >>> (31 - (index & 31))) & 1) === 1;
}

export function messageOnScreen(s: GameState): boolean {
  return (s.messageChoice & 0x80) !== 0;
}

export type Screen = 'movie' | 'dead' | 'transition' | 'message' | 'menu' | 'debug-menu' | 'gameplay' | 'other';

/** What the player is looking at, from the flags. Order matters: the first match wins. */
export function screen(s: GameState): Screen {
  if (s.fmv) return 'movie';
  if (s.msf & MSF.playerDead) return 'dead';
  if (s.msf & (MSF.doorTransition | MSF.roomTransition)) return 'transition';
  if (messageOnScreen(s)) return 'message';
  if (s.msf & (MSF.menuActive | MSF.menuPending)) return 'menu';
  if (s.debugMenu) return 'debug-menu';
  if (s.play) return 'gameplay';
  return 'other';
}

/** Room as the game's file name gives it: stage 0 room 4 is ROOM104. */
export function roomLabel(s: Pick<GameState, 'stage' | 'room'>): string {
  return `${s.stage + 1}${s.room.toString(16).toUpperCase().padStart(2, '0')}`;
}
