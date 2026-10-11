// Build one of the rooms of Rebecca's day from its folder:
//
//   day/<slug>/scene.py       the Blender scene (blender/reb.py), rendered on
//                             the Blender machine into day/<slug>/renders/:
//                             cam<N>.png, cam<N>.depth.png and room.json
//   day/<slug>/room.c         init and main scripts (`rae asm` text)
//   day/<slug>/room.msg.txt   messages (`rae msg` text), optional
//
// and its spec below. Out come the room file, a background pak per camera and
// a mask pak per camera that has masks, under REB/Stage<stage + 1>/ and
// REB/objspr/.
import { execFileSync } from 'node:child_process';
import { existsSync, mkdirSync, mkdtempSync, readFileSync, readdirSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { readPng } from '../../harness/image.ts';
import { animFileName, buildAnim, type AnimLayer } from '../bganim.ts';
import { buildMasks, maskPakName } from '../masks.ts';
import { autoFloors, readDepth } from './floors.ts';
import { makePak } from '../pak.ts';
import { composeRoom, itemModel, SLOT, type PointLight, type Vec3 } from '../rdt.ts';

const here = path.dirname(fileURLToPath(import.meta.url));

type Rect = { readonly x0: number; readonly z0: number; readonly x1: number; readonly z1: number };

export interface DayRoom {
  readonly slug: string;
  /** Stage counted from 0 (the room's files are under Stage<stage + 1>/), room id. */
  readonly stage: number;
  readonly room: number;
  /** The base-game room whose sound bank, effects and player animations it uses. */
  readonly donor: string;
  readonly ambient: readonly [number, number, number];
  readonly lights: readonly [PointLight, PointLight, PointLight];
  /**
   * The part of the floor each camera shows, one or more rectangles that do
   * not overlap another camera's; walking into one cuts to it. 'auto' works
   * them out from the scene (floors.ts).
   */
  readonly cameraFloor: readonly (Rect | readonly Rect[])[] | 'auto';
  /** Footstep sound set (the low byte of the footstep zone record; 0x2D is outdoor earth). */
  readonly footsteps: number;
  /**
   * Item models the room's pick-ups use, in slot order (item_aot_set's model
   * index): a base-game room and the slot its own item_aot_set uses.
   */
  readonly itemModels?: readonly { readonly from: string; readonly index: number }[];
}

interface RoomJson {
  cameras: { from: [number, number, number]; to: [number, number, number]; fov: number }[];
  walls: { shape: 'box' | 'circle'; x0: number; z0: number; x1: number; z1: number; name: string }[];
  /** The walkable floor; walls go round it, leaving the exits open. */
  bounds: Rect;
  /** Floor that is not there, inside the bounds (a gorge either side of a bridge): walls too. */
  voids?: Rect[];
  exits?: Rect[];
  exit?: Rect;
  /** Looping animation: cam<N>.a<k>.png for k = 1 .. frames - 1, cam<N>.png being frame 0. */
  anim?: { frames: number; ticks: number };
  /** Changes of state: cam<N>.s-<name>.png, shown while the flag is set. */
  states?: { name: string; bank: 0 | 1; bit: number }[];
}

export const fileStem = (r: Pick<DayRoom, 'stage' | 'room'>) =>
  `ROOM${r.stage + 1}${r.room.toString(16).toUpperCase().padStart(2, '0')}0`;

// ---------------------------------------------------------------------------
// Sections
// ---------------------------------------------------------------------------

class Writer {
  readonly bytes: number[] = [];
  u16(v: number): this {
    if (!Number.isInteger(v) || v < 0 || v > 0xffff) throw new RangeError(`u16 ${v}`);
    this.bytes.push(v & 0xff, v >> 8);
    return this;
  }
  i16(v: number): this {
    if (!Number.isInteger(v) || v < -0x8000 || v > 0x7fff) throw new RangeError(`i16 ${v}`);
    return this.u16(v & 0xffff);
  }
  i32(v: number): this {
    const b = new Uint8Array(4);
    new DataView(b.buffer).setInt32(0, v, true);
    this.bytes.push(...b);
    return this;
  }
  u8(v: number): this {
    this.bytes.push(v & 0xff);
    return this;
  }
  out(): Uint8Array {
    return Uint8Array.from(this.bytes);
  }
}

const clampRect = (r: Rect): Rect => ({ x0: Math.max(0, r.x0), z0: Math.max(0, r.z0), x1: Math.max(0, r.x1), z1: Math.max(0, r.z1) });

/** Switch-zone record: camTo, camFrom, then corners (low X, low Z), (low X, high Z), (high X, high Z), (high X, low Z). */
function zoneRecord(w: Writer, camTo: number, camFrom: number, r: Rect): void {
  const c = clampRect(r);
  w.u16(camTo).u16(camFrom).u16(c.x0).u16(c.z0).u16(c.x0).u16(c.z1).u16(c.x1).u16(c.z1).u16(c.x1).u16(c.z0);
}

/**
 * One group per camera: a header whose quad is the floor that camera shows
 * (the engine culls entities outside it), then a trigger into every other
 * camera's floor. The table ends with camFrom 0xFFFF.
 */
function switchZones(floors: readonly (Rect | readonly Rect[])[], bounds: Rect): Uint8Array {
  const w = new Writer();
  const margin = 1500;
  const seen: Rect = { x0: bounds.x0 - margin, z0: bounds.z0 - margin, x1: bounds.x1 + margin, z1: bounds.z1 + margin };
  floors.forEach((_, from) => {
    zoneRecord(w, from, from, seen);
    floors.forEach((floor, to) => {
      if (to !== from) for (const r of [floor].flat()) zoneRecord(w, to, from, r);
    });
  });
  w.u16(0xffff).u16(0xffff);
  return w.out();
}

const WALL = 8000;
const PUSH_RECT = 1;
const PUSH_CIRCLE = 3;
const BLOCKS = 0x300;

/** The walls round the bounds, with the exits left open, plus the scene's tagged walls. */
function walls(json: RoomJson): { shape: number; r: Rect }[] {
  const { x0, z0, x1, z1 } = json.bounds;
  const exits = [...(json.exits ?? []), ...(json.exit ? [json.exit] : [])];
  // Each side is a strip; an exit cuts it in two where it crosses.
  const sides: Rect[] = [
    { x0: x0 - WALL, z0: z0 - WALL, x1: x0, z1: z1 + WALL },
    { x0: x1, z0: z0 - WALL, x1: x1 + WALL, z1: z1 + WALL },
    { x0: x0 - WALL, z0: z0 - WALL, x1: x1 + WALL, z1: z0 },
    { x0: x0 - WALL, z0: z1, x1: x1 + WALL, z1: z1 + WALL },
  ];
  const cut = (r: Rect, e: Rect): Rect[] => {
    if (e.x1 <= r.x0 || e.x0 >= r.x1 || e.z1 <= r.z0 || e.z0 >= r.z1) return [r];
    const vertical = r.x1 - r.x0 < r.z1 - r.z0;
    return vertical
      ? [{ ...r, z1: e.z0 }, { ...r, z0: e.z1 }].filter((p) => p.z1 > p.z0)
      : [{ ...r, x1: e.x0 }, { ...r, x0: e.x1 }].filter((p) => p.x1 > p.x0);
  };
  let strips = sides;
  for (const e of exits) strips = strips.flatMap((r) => cut(r, e));
  return [
    ...strips.map((r) => ({ shape: PUSH_RECT, r: clampRect(r) })),
    ...json.walls.map((wl) => ({ shape: wl.shape === 'circle' ? PUSH_CIRCLE : PUSH_RECT, r: clampRect(wl) })),
    ...(json.voids ?? []).map((r) => ({ shape: PUSH_RECT, r: clampRect(r) })),
  ];
}

/** The boundary block: every wall in all four quadrants. */
function collision(json: RoomJson): Uint8Array {
  const list = walls(json);
  const w = new Writer();
  const { x0, z0, x1, z1 } = json.bounds;
  w.i16(Math.round((x0 + x1) / 2)).i16(Math.round((z0 + z1) / 2));
  for (let q = 0; q < 4; q++) w.i32(list.length);
  w.i32(0);
  for (let q = 0; q < 4; q++) {
    for (const { shape, r } of list) w.u16(r.x1).u16(r.z1).u16(r.x0).u16(r.z0).u16(shape).u16(BLOCKS);
  }
  return w.out();
}

/** The NPC navigation grid: one zone, the whole floor. */
function walkZones(bounds: Rect): Uint8Array {
  return new Writer().u8(1).u8(0).i16(bounds.x0).i16(bounds.z0).i16(bounds.x1).i16(bounds.z1).u16(0x03ff).u16(0).out();
}

/** One catch-all footstep zone: the scan has no terminator. */
function footstepZones(sound: number): Uint8Array {
  return new Writer().u16(1).u16(0).u16(0).u16(0x7fbc).u16(0x7fbc).u16(sound).out();
}

/** A script section holding one procedure that only returns; `rae asm` writes the room's own. */
const emptyScript = () => new Writer().u16(4).u8(0).u8(0).u16(0).out();

function findFile(dir: string, name: string): string {
  const hit = readdirSync(dir).find((f) => f.toLowerCase() === name.toLowerCase());
  if (!hit) throw new Error(`${name} not found in ${dir}`);
  return path.join(dir, hit);
}

/** Build the room into `<outDir>/REB/`. Returns the paths written, relative to REB/. */
export function buildDayRoom(spec: DayRoom, baseDir: string, outDir: string, raeCli: string): string[] {
  const dir = path.join(here, spec.slug);
  const renders = path.join(dir, 'renders');
  const json = JSON.parse(readFileSync(path.join(renders, 'room.json'), 'utf8')) as RoomJson;
  if (spec.cameraFloor !== 'auto' && json.cameras.length !== spec.cameraFloor.length) {
    throw new Error(`${spec.slug}: the scene has ${json.cameras.length} cameras, the spec gives floor for ${spec.cameraFloor.length}`);
  }
  // The player's position is a signed 16-bit pair: past 0x7FFF she wraps to the far side of the world.
  if (Math.max(json.bounds.x1, json.bounds.z1) > 0x7fff) {
    throw new Error(`${spec.slug}: the floor reaches ${Math.max(json.bounds.x1, json.bounds.z1)}; rooms must stay under 32768 game units`);
  }
  const [donorStage, donorFile] = spec.donor.split('/') as [string, string];
  const donor = readFileSync(findFile(findFile(baseDir, donorStage), donorFile));
  const stem = fileStem(spec);
  const stageDir = `Stage${spec.stage + 1}`;
  const outStage = path.join(outDir, 'REB', stageDir);
  const outMasks = path.join(outDir, 'REB', 'objspr');
  mkdirSync(outStage, { recursive: true });
  const written: string[] = [];

  const depths = json.cameras.map((_, i) => {
    const file = path.join(renders, `cam${i}.depth.png`);
    return existsSync(file) ? readDepth(file) : undefined;
  });
  const floors = spec.cameraFloor === 'auto' ? autoFloors({ ...json, walls: [...json.walls, ...(json.voids ?? [])] }, depths) : spec.cameraFloor;
  const cameras = json.cameras.map((c, i) => {
    const background = readPng(path.join(renders, `cam${i}.png`));
    const depth = depths[i];
    const masks = depth ? buildMasks(background, depth) : undefined;
    const pak = `RC${stem.slice(4, 7)}${i}.pak`;
    writeFileSync(path.join(outStage, pak), makePak(background));
    written.push(`${stageDir}/${pak}`);
    if (masks?.pak) {
      mkdirSync(outMasks, { recursive: true });
      const name = maskPakName(spec.stage, spec.room, i);
      writeFileSync(path.join(outMasks, name), masks.pak);
      written.push(`objspr/${name}`);
    }
    const layers: AnimLayer[] = [];
    if (json.anim && json.anim.frames > 1) {
      const frames = [background];
      for (let k = 1; k < json.anim.frames; k++) frames.push(readPng(path.join(renders, `cam${i}.a${k}.png`)));
      layers.push({ frames, ticks: json.anim.ticks });
    }
    for (const st of json.states ?? []) {
      layers.push({ frames: [readPng(path.join(renders, `cam${i}.s-${st.name}.png`))], ticks: 0, when: { bank: st.bank, bit: st.bit, value: true } });
    }
    const anim = buildAnim(background, layers);
    if (anim) {
      mkdirSync(outMasks, { recursive: true });
      const name = animFileName(spec.stage, spec.room, i);
      writeFileSync(path.join(outMasks, name), anim);
      written.push(`objspr/${name}`);
    }
    const v = (p: [number, number, number]): Vec3 => ({ x: p[0], y: p[1], z: p[2] });
    return { from: v(c.from), to: v(c.to), fov: c.fov, maskBlock: masks?.block };
  });

  const baseRoom = (from: string) => {
    const [stage, file] = from.split('/') as [string, string];
    return readFileSync(findFile(findFile(baseDir, stage), file));
  };
  const rdt = composeRoom(donor, {
    cameras,
    itemModels: spec.itemModels?.map((m) => itemModel(baseRoom(m.from), m.index)),
    ambient: spec.ambient,
    lights: spec.lights,
    sections: {
      [SLOT.switchZones]: switchZones(floors, json.bounds),
      [SLOT.collision]: collision(json),
      [SLOT.walkZones]: walkZones(json.bounds),
      [SLOT.footsteps]: footstepZones(spec.footsteps),
      [SLOT.init]: emptyScript(),
      [SLOT.main]: emptyScript(),
      // No event scripts: the donor's belong to its own room. The table is its
      // terminating zero dword.
      [SLOT.events]: new Uint8Array(4),
    },
  });

  // Scripts, then messages, by the explorer's assembler and message writer.
  const work = mkdtempSync(path.join(tmpdir(), 'reb-day-'));
  try {
    const run = (args: string[]) => execFileSync(process.execPath, [raeCli, ...args], { stdio: ['ignore', 'ignore', 'inherit'] });
    const composed = path.join(work, 'composed.rdt');
    const scripted = path.join(work, 'scripted.rdt');
    writeFileSync(composed, rdt);
    const out = path.join(outStage, `${stem}.RDT`);
    const messages = path.join(dir, 'room.msg.txt');
    if (existsSync(messages)) {
      run(['asm', path.join(dir, 'room.c'), composed, scripted]);
      // --force: the room's own messages replace the donor's, which nothing here can show.
      run(['msg-set', messages, scripted, out, '--force']);
    } else {
      run(['asm', path.join(dir, 'room.c'), composed, out]);
    }
    written.push(`${stageDir}/${stem}.RDT`);
  } finally {
    rmSync(work, { recursive: true, force: true });
  }
  return written;
}
