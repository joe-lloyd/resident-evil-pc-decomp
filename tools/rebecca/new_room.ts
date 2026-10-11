// Rebecca's mountain trail: the first room the PC release never had.
//
//   stage 2 (files under Stage3/), room 0x12: ROOM3120.RDT, RC3120.pak, RC3121.pak
//
// The room is a courtyard room with its contents replaced, so no offset in the
// file moves. ROOM3000.RDT, the courtyard garden (same stage, outdoors), is the
// template: its header, camera records, switch-zone table, collision, walkable
// zone, footstep zone, lights and main script are overwritten in place within
// the sizes the template gives them, and the init script is assembled onto the
// end of the file with the explorer's `rae asm`. The cameras and the trail's
// extent come from the Blender scene (blender/mountain_trail.py), so the
// renders and the game's camera records cannot drift apart.
//
// Formats used here are documented in docs/RDT_FILE_FORMAT.md.
import { execFileSync } from 'node:child_process';
import { mkdirSync, mkdtempSync, readFileSync, readdirSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { readPng } from '../harness/image.ts';
import { makePak } from './pak.ts';
import { composeRoom, SLOT, type PointLight } from './rdt.ts';

const here = path.dirname(fileURLToPath(import.meta.url));

/** The room's name as files carry it: ROOM<stage + 1><room, 2 hex digits><character variant>. */
export const trailRoomFile = 'ROOM3120';
/** Stage 2 counts from 0, as the debug menu and BIO_CARD.DAT do. */
export const trailRoom = { stage: 2, room: 0x12 } as const;
/** Where a new game stands: near the top of the trail, facing down it (+Z is angle 0xC00, +X is 0, -X is 0x800, -Z is 0x400). */
export const trailStart = { x: 3500, z: 1000, angle: 0xc00 } as const;

const TEMPLATE_FILE = 'ROOM3000.RDT';
const SCENE_FILE = path.join(here, 'blender', 'mountain_trail.py');
const SCRIPT_FILE = path.join(here, 'rooms', `${trailRoomFile}.c`);
const RENDERS_DIR = path.join(here, 'rooms', 'mountain_trail');

// ---------------------------------------------------------------------------
// The scene: parsed once, at the boundary, out of the Blender script.
// ---------------------------------------------------------------------------

export interface Vec3 {
  readonly x: number;
  readonly y: number;
  readonly z: number;
}

/** A camera in game units: position, look-at target and the engine's fov value. */
export interface Camera {
  readonly from: Vec3;
  readonly to: Vec3;
  readonly fov: number;
}

export type Range = readonly [number, number];

export interface Scene {
  readonly cameras: readonly [Camera, Camera];
  readonly trailX: Range;
  readonly trailZ: Range;
}

const INT = '(-?\\d+)';
const TRIPLE = `\\(\\s*${INT},\\s*${INT},\\s*${INT}\\s*\\)`;
const CAMERA_LINE = new RegExp(`"from":\\s*${TRIPLE},\\s*"to":\\s*${TRIPLE},\\s*"fov":\\s*${INT}`, 'g');

function pythonPair(source: string, name: string): Range {
  const m = new RegExp(`^${name}\\s*=\\s*\\(\\s*${INT},\\s*${INT}\\s*\\)`, 'm').exec(source);
  if (!m) throw new Error(`${name} not found in the Blender scene`);
  return [Number(m[1]), Number(m[2])];
}

export function parseScene(source: string): Scene {
  const cameras = [...source.matchAll(CAMERA_LINE)].map((m): Camera => {
    const n = m.slice(1).map(Number);
    return {
      from: { x: n[0]!, y: n[1]!, z: n[2]! },
      to: { x: n[3]!, y: n[4]!, z: n[5]! },
      fov: n[6]!,
    };
  });
  const [first, second, ...rest] = cameras;
  if (!first || !second || rest.length > 0) throw new Error(`the scene must define two cameras, found ${cameras.length}`);
  return { cameras: [first, second], trailX: pythonPair(source, 'TRAIL_X'), trailZ: pythonPair(source, 'TRAIL_Z') };
}

/** Little-endian writer over one RDT. Out-of-range values throw instead of wrapping. */
class Cursor {
  readonly #view: DataView;
  at: number;

  constructor(view: DataView, at: number) {
    this.#view = view;
    this.at = at;
  }

  #check(value: number, min: number, max: number, what: string): void {
    if (!Number.isInteger(value) || value < min || value > max) {
      throw new RangeError(`${what} ${value} at 0x${this.at.toString(16)} is not in ${min}..${max}`);
    }
  }

  u8(value: number): this {
    this.#check(value, 0, 0xff, 'u8');
    this.#view.setUint8(this.at, value);
    this.at += 1;
    return this;
  }

  u16(value: number): this {
    this.#check(value, 0, 0xffff, 'u16');
    this.#view.setUint16(this.at, value, true);
    this.at += 2;
    return this;
  }

  i16(value: number): this {
    this.#check(value, -0x8000, 0x7fff, 'i16');
    this.#view.setInt16(this.at, value, true);
    this.at += 2;
    return this;
  }

  i32(value: number): this {
    this.#check(value, -0x80000000, 0x7fffffff, 'i32');
    this.#view.setInt32(this.at, value, true);
    this.at += 4;
    return this;
  }
}

/** Encode a section: `fill` writes into a buffer of up to `max` bytes; the bytes written are returned. */
function encode(max: number, fill: (c: Cursor) => void): Uint8Array {
  const bytes = new Uint8Array(max);
  const c = new Cursor(new DataView(bytes.buffer), 0);
  fill(c);
  return bytes.slice(0, c.at);
}

// ---------------------------------------------------------------------------
// The room's data
// ---------------------------------------------------------------------------

/**
 * Twelve-bit PS1 channels, fed to setBackColor: a cool night ambient, a
 * little under the garden's (ROOM3000 uses 1167, 1087, 1056).
 */
const AMBIENT: readonly [number, number, number] = [1000, 1080, 1120];

/**
 * Three point lights above the trail. A point light's colour falls off with
 * the horizontal distance to the character (update_entity_lighting), and its
 * radius is the distance at which it reaches zero. Two cool green-white
 * lights stand where the background's key lights are, one over each half of
 * the trail, as dim as the garden's (60, 60, 60); a faint blue one fills the gap.
 */
const LIGHTS: readonly [PointLight, PointLight, PointLight] = [
  { x: 3500, y: -7000, z: 3000, rgb: [58, 68, 62], radius: 10000 },
  { x: 3500, y: -6500, z: 13000, rgb: [58, 68, 62], radius: 10000 },
  { x: 3500, y: -6000, z: 8000, rgb: [30, 36, 50], radius: 14000 },
];

// The floor is flat at Y = 0. The format has no floor-height table to fill in:
// the engine only changes a character's height inside collision records that
// carry a step value, and this room has none.

/** Walls are thick so a character cannot step through one between two frames. */
const WALL_THICKNESS = 8000;
const WALL_SHAPE_PUSH_RECT = 1;
const WALL_FLAGS_BLOCK = 0x300;

interface Rect {
  readonly x0: number;
  readonly z0: number;
  readonly x1: number;
  readonly z1: number;
}

/**
 * Four walls around the trail. Collision coordinates are unsigned (the engine
 * zero-extends them), so nothing can reach below 0: the trail starts at Z = 0,
 * which makes the north wall a line at Z = 0. That still holds, because the
 * engine grows every box by the character's radius before testing.
 */
function wallsAround(trailX: Range, trailZ: Range): Rect[] {
  const [x0, x1] = trailX;
  const [z0, z1] = trailZ;
  const w = WALL_THICKNESS;
  const low = (v: number) => Math.max(0, v);
  return [
    { x0: low(x0 - w), z0: low(z0 - w), x1: x0, z1: z1 + w }, // west
    { x0: x1, z0: low(z0 - w), x1: x1 + w, z1: z1 + w }, // east
    { x0: low(x0 - w), z0: low(z0 - w), x1: x1 + w, z1: z0 }, // north, the top of the trail
    { x0: low(x0 - w), z0: z1, x1: x1 + w, z1: z1 + w }, // south, behind the door
  ];
}

/**
 * A switch-zone record: camTo, camFrom, then the quad's corners in the order
 * the engine's edge tests need (is_entity_in_switch_zone): corner 0 at the
 * low X, low Z; 1 at low X, high Z; 2 at high X, high Z; 3 at high X, low Z.
 * The engine zero-extends the coordinates, so none may be negative.
 */
function zoneRecord(c: Cursor, camTo: number, camFrom: number, r: Rect): void {
  c.u16(camTo).u16(camFrom);
  c.u16(r.x0).u16(r.z0).u16(r.x0).u16(r.z1).u16(r.x1).u16(r.z1).u16(r.x1).u16(r.z0);
}

/**
 * The switch-zone table: one group per camera. A group's first record is a
 * header whose quad is the floor that camera shows (the engine culls entities
 * and effects outside it), the records after it are the triggers that cut to
 * another camera. The table ends with a record whose camFrom is 0xFFFF.
 */
function writeSwitchZones(c: Cursor, scene: Scene): void {
  const [x0, x1] = scene.trailX;
  const [z0, z1] = scene.trailZ;
  const margin = 1500;
  const seen: Rect = { x0: Math.max(0, x0 - margin), z0: Math.max(0, z0), x1: x1 + margin, z1: z1 + margin };
  const split = Math.round((z0 + z1) / 2);
  zoneRecord(c, 0, 0, seen);
  zoneRecord(c, 1, 0, { ...seen, z0: split }); // the lower half belongs to camera 1
  zoneRecord(c, 1, 1, seen);
  zoneRecord(c, 0, 1, { ...seen, z1: split - 1 }); // the upper half belongs to camera 0
  c.u16(0xffff).u16(0xffff);
}

/**
 * Collision: the boundary block. Every wall goes into all four quadrants, so a
 * lookup never has to reason about which quadrant a wall's inflated box
 * reaches, and the counts are simply four equal numbers.
 */
function writeCollision(c: Cursor, scene: Scene): void {
  const walls = wallsAround(scene.trailX, scene.trailZ);
  const [x0, x1] = scene.trailX;
  const [z0, z1] = scene.trailZ;
  c.i16(Math.round((x0 + x1) / 2)).i16(Math.round((z0 + z1) / 2));
  for (let quadrant = 0; quadrant < 4; quadrant++) c.i32(walls.length);
  c.i32(0);
  for (let quadrant = 0; quadrant < 4; quadrant++) {
    for (const w of walls) {
      // MAX corner first: xMax, zMax, xMin, zMin, all unsigned.
      c.u16(w.x1).u16(w.z1).u16(w.x0).u16(w.z0).u16(WALL_SHAPE_PUSH_RECT).u16(WALL_FLAGS_BLOCK);
    }
  }
}

/** The NPC navigation grid: one zone, the whole trail. */
function writeWalkZones(c: Cursor, scene: Scene): void {
  c.u8(1).u8(0);
  c.i16(scene.trailX[0]).i16(scene.trailZ[0]).i16(scene.trailX[1]).i16(scene.trailZ[1]);
  c.u16(0x03ff).u16(0); // the template's own values for the two fields the engine only parks
}

/**
 * Footstep sounds: a header word, then one catch-all zone. The low byte of the
 * last word picks the sound set (0x2d is the template's outdoor one); the scan
 * has no terminator, so the last zone has to match everywhere.
 */
function writeFootsteps(c: Cursor): void {
  c.u16(1);
  c.u16(0).u16(0).u16(0x7fbc).u16(0x7fbc).u16(0x2d);
}

/** A main script that does nothing: one procedure holding `return`, then the end marker. */
function writeEmptyMain(c: Cursor): void {
  c.u16(4).u8(0).u8(0); // size 4: itself plus the two-byte `return`
  c.u16(0);
}

/** An init script that does nothing; `rae asm` writes the room's own over it. */
function writeEmptyInit(c: Cursor): void {
  writeEmptyMain(c);
}

/**
 * The room file before its init script exists: the template's sound bank,
 * effects and player animations, with the trail's cameras, lights, zones,
 * collision and an empty main script (rdt.ts). Pure; `template` is not modified.
 */
export function buildRoomRdt(template: Uint8Array, scene: Scene): Uint8Array {
  return composeRoom(template, {
    cameras: scene.cameras.map((c) => ({ from: c.from, to: c.to, fov: c.fov })),
    ambient: AMBIENT,
    lights: LIGHTS,
    sections: {
      [SLOT.switchZones]: encode(4096, (c) => writeSwitchZones(c, scene)),
      [SLOT.collision]: encode(4096, (c) => writeCollision(c, scene)),
      [SLOT.walkZones]: encode(64, (c) => writeWalkZones(c, scene)),
      [SLOT.footsteps]: encode(64, writeFootsteps),
      [SLOT.init]: encode(16, writeEmptyInit),
      [SLOT.main]: encode(16, writeEmptyMain),
    },
  });
}

// ---------------------------------------------------------------------------
// Files
// ---------------------------------------------------------------------------

function findFile(dir: string, name: string): string {
  const hit = readdirSync(dir).find((f) => f.toLowerCase() === name.toLowerCase());
  if (!hit) throw new Error(`${name} not found in ${dir}`);
  return path.join(dir, hit);
}

/**
 * Write the room's three files into `<outDir>/REB/Stage3/`. `baseDir` holds the
 * player's own Stage3/ROOM3000.RDT, which the room is built from; nothing of
 * it is shipped as is. Returns the paths written, relative to REB/.
 */
export function buildTrailRoom(baseDir: string, outDir: string, raeCli: string): string[] {
  const scene = parseScene(readFileSync(SCENE_FILE, 'utf8'));
  const template = readFileSync(findFile(findFile(baseDir, 'Stage3'), TEMPLATE_FILE));
  const outStage = path.join(outDir, 'REB', 'Stage3');
  mkdirSync(outStage, { recursive: true });

  const work = mkdtempSync(path.join(tmpdir(), 'reb-room-'));
  try {
    const base = path.join(work, `${trailRoomFile}.RDT`);
    writeFileSync(base, buildRoomRdt(template, scene));
    execFileSync(process.execPath, [raeCli, 'asm', SCRIPT_FILE, base, path.join(outStage, `${trailRoomFile}.RDT`)], {
      stdio: ['ignore', 'ignore', 'inherit'],
    });
  } finally {
    rmSync(work, { recursive: true, force: true });
  }

  const written = [`Stage3/${trailRoomFile}.RDT`];
  scene.cameras.forEach((_, i) => {
    const pak = `RC${trailRoomFile.slice(4, 7)}${i}.pak`;
    writeFileSync(path.join(outStage, pak), makePak(readPng(path.join(RENDERS_DIR, `cam${i}.png`))));
    written.push(`Stage3/${pak}`);
  });
  return written;
}

if (process.argv[1] === fileURLToPath(import.meta.url)) {
  const [baseDir, outDir] = process.argv.slice(2);
  const raeCli = process.env.RAE_CLI;
  if (!baseDir || !outDir || !raeCli) {
    console.error('usage: RAE_CLI=<retro-archive-explorer>/scripts/cli.mjs node tools/rebecca/new_room.ts <USA dir> <out dir>');
    process.exit(1);
  }
  for (const f of buildTrailRoom(baseDir, outDir, raeCli)) console.log(`REB/${f}`);
}
