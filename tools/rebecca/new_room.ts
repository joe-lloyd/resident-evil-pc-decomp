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

const here = path.dirname(fileURLToPath(import.meta.url));

/** The room's name as files carry it: ROOM<stage + 1><room, 2 hex digits><character variant>. */
export const trailRoomFile = 'ROOM3120';
/** Stage 2 counts from 0, as the debug menu and BIO_CARD.DAT do. */
export const trailRoom = { stage: 2, room: 0x12 } as const;
/** Where a new game stands: near the top of the trail, facing down it (+Z is angle 0x400). */
export const trailStart = { x: 3500, z: 1000, angle: 0x400 } as const;

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

// ---------------------------------------------------------------------------
// RDT layout. Pointers in the header are file offsets (the loader adds the base).
// ---------------------------------------------------------------------------

const HDR_SPRITES = 0x00;
const HDR_CAMERAS = 0x01;
const HDR_OMODELS = 0x02;
const HDR_ITEMS = 0x03;
const HDR_AMBIENT = 0x06;
const HDR_LIGHTS = 0x0c;
const LIGHT_SIZE = 0x14;
const PTR_ZONES = 0x48;
const PTR_BOUNDS = 0x4c;
const PTR_WALK = 0x58;
const PTR_FOOTSTEPS = 0x5c;
const PTR_INIT = 0x60;
const PTR_MAIN = 0x64;
const PTR_EVENTS = 0x68;
const CAMERAS_AT = 0x94;
const CAMERA_SIZE = 0x2c;

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

/** A section of the template that is overwritten in place: where it starts and how many bytes it has. */
interface Region {
  readonly name: string;
  readonly start: number;
  readonly size: number;
}

function region(name: string, start: number, end: number): Region {
  if (end < start) throw new Error(`${name}: section ends (${end}) before it starts (${start})`);
  return { name, start, size: end - start };
}

/** Clear the region, then let `fill` write into it; throws when `fill` writes past its end. */
function overwrite(rdt: Uint8Array, view: DataView, r: Region, fill: (c: Cursor) => void): void {
  rdt.fill(0, r.start, r.start + r.size);
  const c = new Cursor(view, r.start);
  fill(c);
  const used = c.at - r.start;
  if (used > r.size) throw new Error(`${r.name} needs ${used} bytes, the template gives it ${r.size}`);
}

// ---------------------------------------------------------------------------
// The room's data
// ---------------------------------------------------------------------------

/** Twelve-bit PS1 channels, fed to setBackColor: a cool, low dawn ambient. */
const AMBIENT = [1250, 1200, 1350] as const;

/**
 * Three point lights above the trail. A point light's colour falls off with
 * the horizontal distance to the character (update_entity_lighting), and its
 * radius is the distance at which it reaches zero. Two warm sun-side lights
 * cover the two halves of the trail, a faint cool one fills the gap.
 */
const LIGHTS = [
  { x: 3500, y: -5000, z: 2500, rgb: [130, 105, 80], radius: 9000 },
  { x: 3500, y: -5000, z: 12500, rgb: [130, 105, 80], radius: 9000 },
  { x: 3500, y: -6000, z: 8000, rgb: [50, 60, 85], radius: 14000 },
] as const;

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

function wallsAround(trailX: Range, trailZ: Range): Rect[] {
  const [x0, x1] = trailX;
  const [z0, z1] = trailZ;
  const w = WALL_THICKNESS;
  return [
    { x0: x0 - w, z0: z0 - w, x1: x0, z1: z1 + w }, // west
    { x0: x1, z0: z0 - w, x1: x1 + w, z1: z1 + w }, // east
    { x0: x0 - w, z0: z0 - w, x1: x1 + w, z1: z0 }, // north, the top of the trail
    { x0: x0 - w, z0: z1, x1: x1 + w, z1: z1 + w }, // south, behind the door
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
      // MAX corner first: xMax, zMax, xMin, zMin.
      c.i16(w.x1).i16(w.z1).i16(w.x0).i16(w.z0).u16(WALL_SHAPE_PUSH_RECT).u16(WALL_FLAGS_BLOCK);
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

function writeCamera(c: Cursor, camera: Camera): void {
  c.i32(camera.from.x).i32(camera.from.y).i32(camera.from.z);
  c.i32(camera.to.x).i32(camera.to.y).i32(camera.to.z);
  c.i32(0).i32(0).i32(camera.fov); // roll, reserved, fov
}

/**
 * The room file before its init script exists: the template with every
 * section above overwritten. Pure; `template` is not modified.
 */
export function buildRoomRdt(template: Uint8Array, scene: Scene): Uint8Array {
  const rdt = Uint8Array.from(template);
  const view = new DataView(rdt.buffer);
  const ptr = (at: number): number => view.getUint32(at, true);
  const camerasIn = template[HDR_CAMERAS]!;
  if (camerasIn < scene.cameras.length) throw new Error(`the template has ${camerasIn} cameras, the scene needs ${scene.cameras.length}`);

  // Camera records, and a mask block per camera that draws nothing: a block
  // opens with its group count, and a count of 0 means no sprites and no
  // objspr pak to load (Room_LoadCameraSprites, load_room_bg_masks).
  const firstMask = Math.min(...Array.from({ length: camerasIn }, (_, i) => ptr(CAMERAS_AT + i * CAMERA_SIZE)));
  scene.cameras.forEach((camera, i) => {
    const at = CAMERAS_AT + i * CAMERA_SIZE;
    view.setInt32(ptr(at), 0, true);
    writeCamera(new Cursor(view, at + 8), camera);
  });
  rdt.fill(0, CAMERAS_AT + scene.cameras.length * CAMERA_SIZE, CAMERAS_AT + camerasIn * CAMERA_SIZE);

  rdt[HDR_SPRITES] = 0;
  rdt[HDR_CAMERAS] = scene.cameras.length;
  // No room models and no pick-ups: the init script places none.
  rdt[HDR_OMODELS] = 0;
  rdt[HDR_ITEMS] = 0;

  const ambient = new Cursor(view, HDR_AMBIENT);
  for (const channel of AMBIENT) ambient.i16(channel);
  LIGHTS.forEach((light, i) => {
    const c = new Cursor(view, HDR_LIGHTS + i * LIGHT_SIZE);
    c.i32(light.x).i32(light.y).i32(light.z);
    for (const channel of light.rgb) c.u8(channel);
    c.u8(0).u16(0).i16(light.radius); // padding, type 0 = point light, radius
  });

  overwrite(rdt, view, region('switch zones', ptr(PTR_ZONES), firstMask), (c) => writeSwitchZones(c, scene));
  overwrite(rdt, view, region('collision', ptr(PTR_BOUNDS), ptr(PTR_WALK)), (c) => writeCollision(c, scene));
  overwrite(rdt, view, region('walkable zones', ptr(PTR_WALK), ptr(PTR_FOOTSTEPS)), (c) => writeWalkZones(c, scene));
  overwrite(rdt, view, region('footstep zones', ptr(PTR_FOOTSTEPS), ptr(PTR_INIT)), writeFootsteps);
  overwrite(rdt, view, region('main script', ptr(PTR_MAIN), ptr(PTR_EVENTS)), writeEmptyMain);
  return rdt;
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
