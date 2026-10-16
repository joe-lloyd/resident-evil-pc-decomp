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
  /** Byte 0xDC, the player's collision flags (an enemy's collisionFlags): 0x04 makes records without flag 0x100 floor zones, 0x10 skips shape 5. */
  cf: number;
}

export interface Enemy {
  type: number;
  status: number;
  x: number;
  y: number;
  z: number;
  hp: number;
}

/** One BGM channel (g_SndBank): the WAV it loaded, '' for none; getSndStat (1 playing); getSndVol (hundredths of a dB, 0 loudest). */
export interface BgmChannel {
  file: string;
  playing: boolean;
  volume: number;
}

export interface Bgm {
  /** g_BGM_STATE: bits 0-2 the room row's group, 3-5 the channels on, 6-7 how it starts; 0xFF silence. */
  state: number;
  channels: BgmChannel[];
}

/** What sounds the game loaded and played (TestMode.cpp "snd"); the harness can't hear. */
export interface Sound {
  /** The footstep set under the player: the low byte of the footstep zone she stands in, -1 out of play. */
  set: number;
  /** The WAV that set's walking step loaded (entity sound slot `set`), '' for none. */
  walk: string;
  /** Footsteps played since launch, and the last one's WAV. */
  steps: number;
  step: string;
  /** The room sound set last loaded (a door record's sound byte) and its two WAVs, a door's open and close. */
  door: number;
  room: [string, string];
  /** Sounds played from those two slots since launch, and the last one's WAV. */
  sfx: number;
  last: string;
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
  /** g_message_flags: 0x100 and 0x40 gate menus and item pickups (GameLoop.cpp). */
  messageFlags: number;
  /** g_openMenuFlag: the menu state machine (0 none, 1 open, 2 init, 3 closing). */
  menuState: number;
  /** g_usedItemId: the item last used from the status screen, which a room script's testitem() compares; 0 after a room loads. -1 from a game too old to say. */
  usedItem: number;
  /** The character select's state (1 = waiting for a choice, 8 = turning the cards), -1 when it is not up. */
  selectState: number;
  /** The character on the front card: 0 Chris, 1 Jill, 2 Rebecca; -1 off the screen. */
  selectFront: number;
  banks: Uint8Array[];
  /** The music, or null from a game too old to say. */
  bgm: Bgm | null;
  /** Footsteps and room sounds, or null from a game too old to say. */
  sound: Sound | null;
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
      cf: num(p, 'cf'),
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
    messageFlags: num(msg, 'flags'),
    menuState: num(msg, 'menu'),
    usedItem: o.used === undefined ? -1 : num(o, 'used'),
    selectState: o.sel === undefined ? -1 : num(obj(o.sel, 'sel'), 'state'),
    selectFront: o.sel === undefined ? -1 : num(obj(o.sel, 'sel'), 'front'),
    banks: o.banks.map((b, i) => hexBytes(b, `banks[${i}]`)),
    bgm: o.bgm === undefined ? null : parseBgm(obj(o.bgm, 'bgm')),
    sound: o.snd === undefined ? null : parseSound(obj(o.snd, 'snd')),
  };
}

function parseSound(o: Record<string, unknown>): Sound {
  const room: unknown[] = Array.isArray(o.room) ? o.room : [];
  const [open, close] = room;
  if (room.length !== 2 || typeof open !== 'string' || typeof close !== 'string') throw new ParseError('snd.room: expected 2 files');
  return {
    set: num(o, 'set'),
    walk: str(o, 'walk'),
    steps: num(o, 'steps'),
    step: str(o, 'step'),
    door: num(o, 'door'),
    room: [open, close],
    sfx: num(o, 'sfx'),
    last: str(o, 'last'),
  };
}

function parseBgm(o: Record<string, unknown>): Bgm {
  if (!Array.isArray(o.ch) || o.ch.length !== 3) throw new ParseError('bgm.ch: expected 3 channels');
  return {
    state: num(o, 'state'),
    channels: o.ch.map((c, i) => {
      if (!Array.isArray(c) || c.length !== 3 || typeof c[0] !== 'string' || typeof c[1] !== 'number' || typeof c[2] !== 'number') {
        throw new ParseError(`bgm.ch[${i}]: expected [file, playing, volume]`);
      }
      return { file: c[0], playing: c[1] !== 0, volume: c[2] };
    }),
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

/** The WAVs playing now, by channel order; empty in silence. */
export function playingMusic(s: GameState): string[] {
  if (!s.bgm) throw new Error('this game does not report its music: build a newer one');
  return s.bgm.channels.filter((c) => c.playing && c.file !== '').map((c) => c.file);
}

/** Room as the game's file name gives it: stage 0 room 4 is ROOM104. */
export function roomLabel(s: Pick<GameState, 'stage' | 'room'>): string {
  return `${s.stage + 1}${s.room.toString(16).toUpperCase().padStart(2, '0')}`;
}
