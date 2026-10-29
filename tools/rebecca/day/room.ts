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
import { look } from './look.ts';
import { keyItemModels, type ItemSpot, type PickupModel } from '../items/items.ts';
import { ownPickup } from '../items/tmd.ts';
import { EVENT_FLAGS, itemModelSlots } from './events.ts';
import { lockFlag } from './scripts.ts';
import { animFileName, buildAnim, type AnimLayer } from '../bganim.ts';
import { buildMasks, maskPakName } from '../masks.ts';
import { readDepth } from './floors.ts';
import { roomZones, type Quad } from './camera-zones.ts';
import { occluders, standableIn } from '../occluders.ts';
import { makePak } from '../pak.ts';
import { composeRoom, model, scaleModel, SLOT, type PointLight, type Vec3 } from '../rdt.ts';
import { GROUNDS, isGround, stepSlots, type Floors, type Ground } from '../sound/ground.ts';

const here = path.dirname(fileURLToPath(import.meta.url));

type Rect = { readonly x0: number; readonly z0: number; readonly x1: number; readonly z1: number };

export type Hour = 'dawn' | 'morning' | 'noon' | 'afternoon' | 'dusk' | 'night';

/**
 * How the game lights her in the room: given outright, or worked out from the
 * hour and whether she is indoors (lightingFor), placed round the floor.
 */
export type Lighting =
  | { readonly ambient: readonly [number, number, number]; readonly lights: readonly [PointLight, PointLight, PointLight] }
  | { readonly hour: Hour; readonly inside: boolean };

export type DayRoom = DayRoomBase & Lighting;

interface DayRoomBase {
  readonly slug: string;
  /** Stage counted from 0 (the room's files are under Stage<stage + 1>/), room id. */
  readonly stage: number;
  readonly room: number;
  /** The base-game room whose sound bank, effects and player animations it uses. */
  readonly donor: string;
  /**
   * The part of the floor each camera shows, one or more rectangles that do
   * not overlap another camera's: where several cameras would do, camera-zones.ts
   * gives these the floor. 'auto' lets the scene decide (floors.ts).
   */
  readonly cameraFloor: readonly (Rect | readonly Rect[])[] | 'auto';
  /**
   * Item models the room's pick-ups use, in slot order (item_aot_set's model
   * index): a base-game room and the slot its own item_aot_set uses, or one
   * of her items' own (items/models.py).
   */
  readonly itemModels?: readonly PickupModel[];
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
  /**
   * Changes of state: cam<N>.s-<name>.png, shown while the flag is set. Bit
   * -1: the flag of the plan step `name`, a puzzle's (events.ts) or a lock's
   * (scripts.ts). With `loop`, cam<N>.s-<name>.a<k>.png loop with the room's
   * anim where rendered; with `motion`, cam<N>.m-<name>.<k>.png play once
   * as it happens, then the state.
   */
  states?: { name: string; bank: 0 | 1 | 2; bit: number; motion?: { frames: number; ticks: number }; loop?: boolean }[];
  /** A save room: where kit.item_box put the item box, whose lid is RE1's own (ITEM_BOX_LID). */
  saves?: { lid: { x: number; y: number; z: number; angle: number; scale?: number } } | null;
  /** Where the scene puts the key items she finds here (kit.Room.item). */
  items?: ItemSpot[];
  /** What the floor is underfoot (kit.Room.ground), and the parts of it that are something else (kit.Room.floor): her footsteps (sound/ground.ts). */
  ground?: string;
  floors?: (Rect & { kind: string })[];
}

/** The item box's lid, the same object in every RE1 save room: model 0 of the mansion's 1F save room. */
const ITEM_BOX_LID = { from: 'Stage1/ROOM1000.RDT', index: 0 } as const;

/** The sun or the room's lamps, the sky, and light thrown back off the ground, for the hour. */
const HOURS: Record<Hour, { ambient: [number, number, number]; key: [number, number, number]; sky: [number, number, number]; bounce: [number, number, number] }> = {
  dawn: { ambient: [1050, 950, 960], key: [85, 60, 50], sky: [45, 45, 60], bounce: [30, 28, 28] },
  morning: { ambient: [1150, 1100, 1050], key: [95, 85, 70], sky: [55, 62, 75], bounce: [30, 32, 30] },
  noon: { ambient: [1150, 1140, 1120], key: [85, 85, 82], sky: [55, 58, 66], bounce: [32, 32, 30] },
  afternoon: { ambient: [1120, 1060, 1000], key: [95, 78, 58], sky: [50, 54, 66], bounce: [32, 28, 24] },
  dusk: { ambient: [950, 800, 760], key: [95, 50, 30], sky: [35, 30, 50], bounce: [24, 18, 18] },
  night: { ambient: [700, 720, 840], key: [40, 48, 70], sky: [20, 24, 40], bounce: [14, 14, 18] },
};

export function lightingFor(hour: Hour, inside: boolean, b: Rect): { ambient: [number, number, number]; lights: [PointLight, PointLight, PointLight] } {
  const h = HOURS[hour];
  const cx = Math.round((b.x0 + b.x1) / 2);
  const cz = Math.round((b.z0 + b.z1) / 2);
  const span = Math.max(b.x1 - b.x0, b.z1 - b.z0, 3400);
  const shade = (c: readonly number[], k: number) => c.map((v) => Math.round(v * k)) as [number, number, number];
  if (inside) {
    // A lamp overhead, daylight from a window, a dim fill.
    return {
      ambient: shade(h.ambient, 0.8),
      lights: [
        { x: cx, y: -2400, z: cz, rgb: [110, 80, 50], radius: Math.round(span * 1.4) },
        { x: b.x1, y: -2200, z: b.z0, rgb: shade(h.key, 0.7), radius: Math.round(span * 1.6) },
        { x: cx, y: -3200, z: b.z1, rgb: [32, 34, 40], radius: Math.round(span * 2) },
      ],
    };
  }
  return {
    ambient: h.ambient,
    lights: [
      { x: b.x1 + span, y: -span, z: b.z0 - span / 2, rgb: h.key, radius: span * 4 },
      { x: cx, y: -span, z: cz, rgb: h.sky, radius: span * 4 },
      { x: cx, y: 1700, z: cz, rgb: h.bounce, radius: span * 2 },
    ],
  };
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

/** A rect cut to what the file can hold: a wall reaching past it still blocks everything beyond the floor. */
const clamp16 = (v: number) => Math.min(0xffff, Math.max(0, v));
const clampRect = (r: Rect): Rect => ({ x0: clamp16(r.x0), z0: clamp16(r.z0), x1: clamp16(r.x1), z1: clamp16(r.z1) });

/** Switch-zone record: camTo, camFrom, then the four corners, clockwise seen from above with Z up (camera-zones.ts). */
function zoneRecord(w: Writer, camTo: number, camFrom: number, q: Quad): void {
  w.u16(camTo).u16(camFrom);
  for (const [x, z] of q) w.u16(clamp16(x)).u16(clamp16(z));
}

const rectQuad = (r: Rect): Quad => [[r.x0, r.z0], [r.x0, r.z1], [r.x1, r.z1], [r.x1, r.z0]];

/**
 * One group per camera: a header whose quad is the floor that camera shows
 * (the engine culls entities outside it), then the trigger quads of every
 * other camera (camera-zones.ts). The table ends with camFrom 0xFFFF.
 */
/** The flag that shows a scene's change of state: its own, or the puzzle's (events.ts) or the lock's (scripts.ts) its name is the step of. */
function stateFlag(slug: string, st: NonNullable<RoomJson['states']>[number]): NonNullable<AnimLayer['when']> {
  if (st.bit >= 0) return { bank: st.bank, bit: st.bit, value: true };
  const event = EVENT_FLAGS.get(st.name);
  if (event !== undefined) return { bank: 1, bit: event, value: true };
  const lock = lockFlag(st.name);
  if (lock !== undefined) return { bank: 2, bit: lock, value: true };
  throw new Error(`${slug}: state ${st.name} is no puzzle step of events.ts and no lock of scripts.ts`);
}

function switchZones(zones: readonly (readonly Quad[])[], bounds: Rect): Uint8Array {
  const w = new Writer();
  const margin = 1500;
  const seen = rectQuad({ x0: bounds.x0 - margin, z0: bounds.z0 - margin, x1: bounds.x1 + margin, z1: bounds.z1 + margin });
  zones.forEach((_, from) => {
    zoneRecord(w, from, from, seen);
    zones.forEach((quads, to) => {
      if (to !== from) for (const q of quads) zoneRecord(w, to, from, q);
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

/**
 * The room's floors, as its scene says (renders/room.json). A room.json from
 * before scenes said is all earth, with a warning: `render.ts --records
 * <slug>` writes it again.
 */
export function roomFloors(slug: string, json: Pick<RoomJson, 'ground' | 'floors'>): Floors {
  const kind = (k: string | undefined, what: string): Ground => {
    if (k === undefined || !isGround(k)) throw new Error(`${slug}: ${what} is ${JSON.stringify(k)}, not one of ${GROUNDS.join(', ')}`);
    return k;
  };
  if (json.ground === undefined) {
    console.warn(`${slug}: room.json says nothing of its floors, so her steps there are all earth (run day/render.ts --records ${slug})`);
    return { ground: 'earth', parts: [] };
  }
  return {
    ground: kind(json.ground, 'the ground'),
    parts: (json.floors ?? []).map((f, i) => ({ kind: kind(f.kind, `floor ${i}`), x0: f.x0, z0: f.z0, x1: f.x1, z1: f.z1 })),
  };
}

/**
 * The footstep zones: each part of the floor that is something else, then a
 * catch-all for the room's own ground, since the scan has no terminator. A
 * zone's low byte is the footstep set's first slot (sound/ground.ts).
 */
function footstepZones(floors: Floors): Uint8Array {
  const slots = stepSlots(floors);
  const w = new Writer().u16(floors.parts.length + 1);
  for (const p of floors.parts) w.u16(p.x0).u16(p.z0).u16(p.x1 - p.x0).u16(p.z1 - p.z0).u16(slots.get(p.kind)!);
  return w.u16(0).u16(0).u16(0x7fbc).u16(0x7fbc).u16(slots.get(floors.ground)!).out();
}

/** A script section holding one procedure that only returns; `rae asm` writes the room's own. */
const emptyScript = () => new Writer().u16(4).u8(0).u8(0).u16(0).out();

function findFile(dir: string, name: string): string {
  const hit = readdirSync(dir).find((f) => f.toLowerCase() === name.toLowerCase());
  if (!hit) throw new Error(`${name} not found in ${dir}`);
  return path.join(dir, hit);
}

/** Build the room into `<outDir>/REB/`. Returns the paths written, relative to REB/, and the room's floors. */
export function buildDayRoom(spec: DayRoom, baseDir: string, outDir: string, raeCli: string): { written: string[]; floors: Floors } {
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
  const scene = { ...json, walls: [...json.walls, ...(json.voids ?? [])] };
  const zones = roomZones(scene, depths, spec.cameraFloor === 'auto' ? undefined : spec.cameraFloor);
  const standable = standableIn(json);
  const cameras = json.cameras.map((c, i) => {
    const background = look(readPng(path.join(renders, `cam${i}.png`)));
    // The masks: what the scene tags as foreground, and every surface in
    // front of where she can stand on this camera's floor (occluders.ts).
    const zall = path.join(renders, `cam${i}.zall.png`);
    const tagged = depths[i];
    // Where this camera can be on screen with her: its triggers and the gap round them.
    const found = existsSync(zall) ? occluders(c, readDepth(zall), [json.bounds], (x, z) => standable(x, z) && zones.holds(i, x, z)) : undefined;
    const depth = found && tagged ? found.map((d, k) => Math.min(d, tagged[k]!)) : (found ?? tagged);
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
      for (let k = 1; k < json.anim.frames; k++) frames.push(look(readPng(path.join(renders, `cam${i}.a${k}.png`))));
      layers.push({ frames, ticks: json.anim.ticks });
    }
    // Each state over the loop, then each one's motion over every state: as
    // it plays it shows the whole change, so nothing jumps ahead of it.
    const motions: AnimLayer[] = [];
    for (const st of json.states ?? []) {
      const when = stateFlag(spec.slug, st);
      const shot = (suffix: string) => path.join(renders, `cam${i}.${suffix}.png`);
      const after = look(readPng(shot(`s-${st.name}`)));
      const loop = st.loop && json.anim && existsSync(shot(`s-${st.name}.a1`));
      const frames = loop ? [after, ...Array.from({ length: json.anim!.frames - 1 }, (_, k) => look(readPng(shot(`s-${st.name}.a${k + 1}`))))] : [after];
      layers.push({ frames, ticks: loop ? json.anim!.ticks : 0, when });
      if (st.motion && existsSync(shot(`m-${st.name}.1`))) {
        const between = Array.from({ length: st.motion.frames - 1 }, (_, k) => look(readPng(shot(`m-${st.name}.${k + 1}`))));
        motions.push({ frames: [...between, after], ticks: st.motion.ticks, when, once: true });
      }
    }
    layers.push(...motions);
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

  const underfoot = roomFloors(spec.slug, json);
  const baseRoom = (from: string) => {
    const [stage, file] = from.split('/') as [string, string];
    return readFileSync(findFile(findFile(baseDir, stage), file));
  };
  const rdt = composeRoom(donor, {
    cameras,
    itemModels: itemModelSlots(spec.itemModels ?? [], json.items ?? [], spec.slug).map((m) =>
      'empty' in m ? {} : 'own' in m ? ownPickup(m.own) : model(baseRoom(m.from), 'item', m.index),
    ),
    // A save room's item box: RE1's own lid, object model 0 of the mansion's save room.
    objectModels: json.saves ? [scaleModel(model(baseRoom(ITEM_BOX_LID.from), 'object', ITEM_BOX_LID.index), json.saves.lid.scale ?? 1)] : undefined,
    ...('hour' in spec ? lightingFor(spec.hour, spec.inside, json.bounds) : { ambient: spec.ambient, lights: spec.lights }),
    sections: {
      [SLOT.switchZones]: switchZones(zones.zones, json.bounds),
      [SLOT.collision]: collision(json),
      [SLOT.walkZones]: walkZones(json.bounds),
      [SLOT.footsteps]: footstepZones(underfoot),
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
  return { written, floors: underfoot };
}
