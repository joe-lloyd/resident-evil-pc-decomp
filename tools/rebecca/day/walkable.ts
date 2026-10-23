// Does the floor her collision gives her match the pictures? Each camera's
// depth of every surface (cam<N>.zall.png) is turned back into points in
// the room. On the floor a camera shows her on (floors.ts), a cell she can
// stand on is wrong where:
//
//   solid    the camera draws a surface between her knee and her head within
//            her body's reach: she would stand in a wall, a door, a trunk;
//   no floor the camera sees past where the floor would be: a drop, the sky.
//
// It also lists the doors that open which she can walk on past (into the
// building, round behind the door), the arrivals that put her in a wall, and
// the zones she cannot set off from anywhere she can stand.
//
//   node tools/rebecca/day/walkable.ts [--map] [--renders <dir>] [--day <dir>] [slug ...]
//
// No slug checks every room with renders. To compare a before and after,
// --renders reads <dir>/<slug>.json for the room.json (the pictures stay the
// renders' own) and --day reads the scripts from another checkout's day/. Outdoors the knee is higher: the grass comes up past it, and she
// walks through grass (blender reb.py floor_probe ignores it the same way).
import { existsSync, readFileSync, readdirSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { FRAME_H, FRAME_W } from '../masks.ts';
import { autoFloors, project, readDepth, type Rect } from './floors.ts';
import { dayRooms } from './rooms.ts';

type V3 = [number, number, number];
export interface Camera {
  readonly from: V3;
  readonly to: V3;
  readonly fov: number;
}

/** Grid cells this many game units across (10 cm). */
export const CELL = 170;
/** A surface higher than this above the floor is in her way, indoors and out (game units: 35 cm and 90 cm). */
export const KNEE_INSIDE = 600;
export const KNEE_OUTSIDE = 1530;
/** The top of her head. */
const HEAD = 2700;
/** Pixels of surface a cell needs before it counts as solid: one stray leaf or fly is not a wall. */
const HITS = 3;
/** The floor under her feet is missing where a camera sees this far past it. */
const PAST = 500;
/** Her body's half-width: a surface this near her centre is drawn through her. */
const BODY = 260;
/** The engine keeps her centre this far from a wall (tools/harness/room-map.ts). */
export const RADIUS = 380;
/** How far ahead of her the action button probes (check_action_object). */
const REACH = 600;

const sub = (a: V3, b: V3): V3 => [a[0] - b[0], a[1] - b[1], a[2] - b[2]];
const cross = (a: V3, b: V3): V3 => [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];
const norm = (a: V3): V3 => {
  const l = Math.hypot(...a);
  return [a[0] / l, a[1] / l, a[2] / l];
};

/** The game point a pixel shows at view depth `d`: floors.ts project's inverse. */
export function unproject(cam: Camera, px: number, py: number, d: number): V3 {
  const fwd = norm(sub(cam.to, cam.from));
  const right = norm(cross(fwd, [0, -1, 0]));
  const up = cross(right, fwd);
  const a = (px + 0.5 - 160) / cam.fov;
  const b = (120 - py - 0.5) / cam.fov;
  return [0, 1, 2].map((k) => cam.from[k]! + d * (fwd[k]! + right[k]! * a + up[k]! * b)) as V3;
}

/** What one camera draws over a grid of floor cells. */
export interface Seen {
  readonly x0: number;
  readonly z0: number;
  readonly cols: number;
  readonly rows: number;
  /** Per cell: the camera draws something solid standing there. */
  readonly solid: Uint8Array;
  /** Per cell: the camera sees past where the floor would be. */
  readonly past: Uint8Array;
}

/** What camera `cam` draws (its depth of every surface, `all`) over the floor cells of `area`. */
export function seenBy(cam: Camera, all: Float32Array, area: Rect, knee: number): Seen {
  const x0 = area.x0;
  const z0 = area.z0;
  const cols = Math.ceil((area.x1 - area.x0) / CELL);
  const rows = Math.ceil((area.z1 - area.z0) / CELL);
  const hits = new Uint16Array(cols * rows);
  const past = new Uint8Array(cols * rows);
  for (let py = 0; py < FRAME_H; py++) {
    for (let px = 0; px < FRAME_W; px++) {
      const d = all[py * FRAME_W + px]!;
      if (!Number.isFinite(d)) continue;
      const p = unproject(cam, px, py, d);
      if (-p[1] < knee || -p[1] > HEAD) continue;
      const i = Math.floor((p[0] - x0) / CELL);
      const j = Math.floor((p[2] - z0) / CELL);
      if (i >= 0 && j >= 0 && i < cols && j < rows) hits[j * cols + i]!++;
    }
  }
  for (let j = 0; j < rows; j++) {
    for (let i = 0; i < cols; i++) {
      const s = project(cam, [x0 + (i + 0.5) * CELL, 0, z0 + (j + 0.5) * CELL]);
      if (!s) continue;
      const px = Math.floor(s.x);
      const py = Math.floor(s.y);
      if (px < 0 || py < 0 || px >= FRAME_W || py >= FRAME_H) continue;
      if (all[py * FRAME_W + px]! > s.z + PAST) past[j * cols + i] = 1;
    }
  }
  const solid = new Uint8Array(cols * rows);
  for (let k = 0; k < solid.length; k++) solid[k] = hits[k]! >= HITS ? 1 : 0;
  return { x0, z0, cols, rows, solid, past };
}

type Shape = Rect & { shape?: 'box' | 'circle'; name?: string };
type Arrive = { x: number; z: number; angle: number };
export interface RoomJson {
  cameras: Camera[];
  bounds: Rect;
  walls: Shape[];
  voids?: Rect[];
  exits?: Rect[];
  exit?: Rect;
  doors?: { to: string; zone: Rect; arrive: Arrive; walk?: boolean; touch?: boolean }[];
  checks?: { zone: Rect; text: string }[];
  spots?: { step: string; zone: Rect }[];
  items?: { step: string; x: number; z: number }[];
}

const inRect = (r: Rect, x: number, z: number, grow = 0) => x > r.x0 - grow && x < r.x1 + grow && z > r.z0 - grow && z < r.z1 + grow;

/**
 * Can her centre stand at (x, z) by the room's collision (room.ts walls): in
 * the bounds or an exit, and clear of every wall by her radius? A circle
 * wall is a circle, as the engine pushes it.
 */
export function walkableBy(json: RoomJson): (x: number, z: number) => boolean {
  const b = json.bounds;
  const exits = [...(json.exits ?? []), ...(json.exit ? [json.exit] : [])];
  const solid: Shape[] = [...json.walls, ...(json.voids ?? [])];
  const inner = { x0: b.x0 + RADIUS, z0: b.z0 + RADIUS, x1: b.x1 - RADIUS, z1: b.z1 - RADIUS };
  // An exit cuts the wall along the floor's edge (room.ts walls): she walks
  // out through it, kept her radius from its sides.
  const ways = exits.map((e) =>
    e.x1 - e.x0 < e.z1 - e.z0
      ? { x0: e.x0 - RADIUS, z0: e.z0 + RADIUS, x1: e.x1 + RADIUS, z1: e.z1 - RADIUS }
      : { x0: e.x0 + RADIUS, z0: e.z0 - RADIUS, x1: e.x1 - RADIUS, z1: e.z1 + RADIUS },
  );
  return (x, z) =>
    (inRect(inner, x, z) || ways.some((e) => inRect(e, x, z))) &&
    !solid.some((w) =>
      w.shape === 'circle' ? Math.hypot(x - (w.x0 + w.x1) / 2, z - (w.z0 + w.z1) / 2) < (w.x1 - w.x0) / 2 + RADIUS : inRect(w, x, z, RADIUS),
    );
}

/** The cells she can walk to from where she comes in (`seeds`, the arrivals); every walkable cell when nothing leads in. */
function reachable(seeds: readonly { x: number; z: number }[], can: (x: number, z: number) => boolean, x0: number, z0: number, cols: number, rows: number): Uint8Array {
  const at = (i: number, j: number) => [x0 + (i + 0.5) * CELL, z0 + (j + 0.5) * CELL] as const;
  const out = new Uint8Array(cols * rows);
  if (!seeds.length) {
    for (let k = 0; k < out.length; k++) out[k] = can(...at(k % cols, Math.floor(k / cols))) ? 1 : 0;
    return out;
  }
  const queue: number[] = [];
  for (const s of seeds) {
    // The nearest walkable cell to where the door puts her: the engine pushes her there.
    let best = -1;
    let bestD = 2 * RADIUS;
    const si = Math.floor((s.x - x0) / CELL);
    const sj = Math.floor((s.z - z0) / CELL);
    for (let j = Math.max(0, sj - 6); j <= Math.min(rows - 1, sj + 6); j++) {
      for (let i = Math.max(0, si - 6); i <= Math.min(cols - 1, si + 6); i++) {
        const [x, z] = at(i, j);
        const d = Math.hypot(x - s.x, z - s.z);
        if (d < bestD && can(x, z)) [best, bestD] = [j * cols + i, d];
      }
    }
    if (best >= 0 && !out[best]) {
      out[best] = 1;
      queue.push(best);
    }
  }
  while (queue.length) {
    const k = queue.pop()!;
    const i = k % cols;
    const j = (k - i) / cols;
    for (const [di, dj] of [[1, 0], [-1, 0], [0, 1], [0, -1]] as const) {
      const ni = i + di;
      const nj = j + dj;
      if (ni < 0 || nj < 0 || ni >= cols || nj >= rows) continue;
      const nk = nj * cols + ni;
      if (out[nk] || !can(...at(ni, nj))) continue;
      out[nk] = 1;
      queue.push(nk);
    }
  }
  return out;
}

export interface CameraReport {
  /** Cells of the camera's floor she can walk to. */
  readonly cells: number;
  /** Of those, the ones the camera draws a solid surface through her on. */
  readonly solid: number;
  /** And the ones it draws no floor under. */
  readonly hole: number;
}

export interface Report {
  readonly cameras: CameraReport[];
  /** Doors that open, which she can walk on past. */
  readonly doors: string[];
  /** Arrivals where the room's walls hold her centre. */
  readonly arrivals: string[];
  /** Doors, checks, spots and pickups she cannot set off from anywhere she can stand. */
  readonly zones: string[];
  readonly map: string;
}

/** What the room's script and its neighbours' make of it (readScript). */
export interface Script {
  /** Where the doors into the room put her. */
  readonly arrivals: readonly { from: string; x: number; z: number }[];
  /**
   * The zones of its own script: `her` fires where she stands (a door that
   * opens), `ahead` where the point REACH in front of her falls (the action
   * button, an item used, a walk she leaves by). `door` names where a door
   * takes her; `touch` is a walk she leaves by as she walks into it.
   */
  readonly zones: readonly { what: string; zone: Rect; at: 'her' | 'ahead'; door?: string; touch?: boolean }[];
}

/**
 * The room's collision against what its cameras draw: `seen[c]` is camera
 * c's view of the floor (seenBy over the room's bounds), `floors[c]` the floor
 * it shows her on (room.ts switch zones), and `script` its doors and zones.
 */
export function check(json: RoomJson, seen: readonly (Seen | undefined)[], floors: readonly (Rect | readonly Rect[])[], script: Script): Report {
  const can = walkableBy(json);
  const b = json.bounds;
  const x0 = b.x0;
  const z0 = b.z0;
  const cols = Math.ceil((b.x1 - b.x0) / CELL);
  const rows = Math.ceil((b.z1 - b.z0) / CELL);
  // Where she can go: the bounds, and out through the exits a hand-written
  // room leaves in them, on a grid lined up with the cameras'.
  const exits = [...(json.exits ?? []), ...(json.exit ? [json.exit] : [])];
  const pad = (lo: number, out: number) => Math.ceil(Math.max(0, lo - out) / CELL);
  const [pl, pt] = [pad(x0, Math.min(x0, ...exits.map((e) => e.x0))), pad(z0, Math.min(z0, ...exits.map((e) => e.z0)))];
  const [pr, pb] = [pad(Math.max(b.x1, ...exits.map((e) => e.x1)), b.x1), pad(Math.max(b.z1, ...exits.map((e) => e.z1)), b.z1)];
  const [ax0, az0, acols, arows] = [x0 - pl * CELL, z0 - pt * CELL, cols + pl + pr, rows + pt + pb];
  const around = reachable(script.arrivals, can, ax0, az0, acols, arows);
  const reach = new Uint8Array(cols * rows);
  for (let j = 0; j < rows; j++) for (let i = 0; i < cols; i++) reach[j * cols + i] = around[(j + pt) * acols + i + pl]!;
  const body = Math.round(BODY / CELL);
  const cams = json.cameras.map(() => ({ cells: 0, solid: 0, hole: 0 }));
  const lines: string[] = [];
  for (let j = 0; j < rows; j++) {
    let row = '';
    for (let i = 0; i < cols; i++) {
      if (!reach[j * cols + i]) {
        row += ' ';
        continue;
      }
      const x = x0 + (i + 0.5) * CELL;
      const z = z0 + (j + 0.5) * CELL;
      const c = floors.findIndex((f) => [f].flat().some((r) => x >= r.x0 && x < r.x1 && z >= r.z0 && z < r.z1));
      const s = c >= 0 ? seen[c] : undefined;
      if (!s) {
        row += '?';
        continue;
      }
      cams[c]!.cells++;
      let solid = false;
      for (let dj = -body; dj <= body && !solid; dj++) {
        for (let di = -body; di <= body && !solid; di++) {
          const ii = i + di;
          const jj = j + dj;
          if (ii >= 0 && jj >= 0 && ii < s.cols && jj < s.rows && s.solid[jj * s.cols + ii]) solid = true;
        }
      }
      const hole = !solid && s.past[j * s.cols + i] === 1;
      if (solid) cams[c]!.solid++;
      if (hole) cams[c]!.hole++;
      row += solid ? '#' : hole ? 'o' : String(c);
    }
    lines.push(row);
  }
  const walk = (x: number, z: number) => {
    const i = Math.floor((x - ax0) / CELL);
    const j = Math.floor((z - az0) / CELL);
    return i >= 0 && j >= 0 && i < acols && j < arows && around[j * acols + i] === 1;
  };
  /** Somewhere she can stand inside `r`, grown by `grow` (and a cell, for the grid's coarseness). */
  const standsIn = (r: Rect, reachBy: number) => {
    const grow = reachBy + CELL;
    for (let x = r.x0 - grow + CELL / 2; x < r.x1 + grow; x += CELL / 2) for (let z = r.z0 - grow + CELL / 2; z < r.z1 + grow; z += CELL / 2) if (walk(x, z)) return true;
    return false;
  };
  const doors: string[] = [];
  const zones: string[] = [];
  const arrivals = script.arrivals.filter((a) => !can(a.x, a.z)).map((a) => `from ${a.from} at (${a.x}, ${a.z})`);
  /** How far the nearest floor she can reach is from `r`. */
  const gapTo = (r: Rect) => {
    let best = Infinity;
    for (let k = 0; k < around.length; k++) {
      if (!around[k]) continue;
      const x = ax0 + ((k % acols) + 0.5) * CELL;
      const z = az0 + (Math.floor(k / acols) + 0.5) * CELL;
      best = Math.min(best, Math.hypot(Math.max(r.x0 - x, 0, x - r.x1), Math.max(r.z0 - z, 0, z - r.z1)));
    }
    return best;
  };
  for (const z of script.zones) {
    if (!standsIn(z.zone, z.at === 'her' ? 0 : REACH)) zones.push(`${z.what} at (${z.zone.x0}, ${z.zone.z0})-(${z.zone.x1}, ${z.zone.z1}), floor ${Math.round(gapTo(z.zone))} away`);
    if (!z.door || z.touch) continue;
    // A door that opens: floor on past it, from where she comes back in
    // through it (else from the room's middle toward the edge it is on), is
    // a way round it.
    const cx = (z.zone.x0 + z.zone.x1) / 2;
    const cz = (z.zone.z0 + z.zone.z1) / 2;
    const back = script.arrivals.find((a) => a.from === z.door);
    const [ux, uz] = back
      ? [cx - back.x, cz - back.z].map((v) => v / (Math.hypot(cx - back.x, cz - back.z) || 1))
      : ([
          [z.zone.x0 - b.x0, -1, 0],
          [b.x1 - z.zone.x1, 1, 0],
          [z.zone.z0 - b.z0, 0, -1],
          [b.z1 - z.zone.z1, 0, 1],
        ] as const).reduce((p, q) => (q[0] < p[0] ? q : p)).slice(1);
    const half = Math.max(Math.abs((z.zone.x1 - z.zone.x0) * ux!), Math.abs((z.zone.z1 - z.zone.z0) * uz!)) / 2;
    for (let t = half + 300; t <= half + 1500; t += CELL) {
      if (walk(cx + ux! * t, cz + uz! * t)) {
        doors.push(`${z.door}: she walks ${Math.round(t - half)} units past it, to (${Math.round(cx + ux! * t)}, ${Math.round(cz + uz! * t)})`);
        break;
      }
    }
  }
  return { cameras: cams, doors, arrivals, zones, map: lines.join('\n') };
}

const here = path.dirname(fileURLToPath(import.meta.url));
const BUILT_INSIDE = new Set(['lookout', 'shed']);

/** ROOM_31A: stage 3 counted from 1, room 0x1A. */
const slugOf = (token: string) => {
  const m = /^ROOM_([0-9A-F])([0-9A-F]{2})$/.exec(token);
  return m ? dayRooms.find((r) => r.stage === parseInt(m[1]!, 16) - 1 && r.room === parseInt(m[2]!, 16))?.slug : undefined;
};
const callArgs = (line: string, call: string) => {
  const m = new RegExp(`\\b${call}\\((.*)\\);`).exec(line.replace(/\/\*.*?\*\//g, ''));
  return m ? m[1]!.split(',').map((x) => x.trim()) : undefined;
};

/**
 * The room's doors and zones as the game has them: its script's init
 * (room.c in `day`, the generated and the hand-written alike), and the
 * arrivals of every room's doors into it.
 */
export function readScript(slug: string, day = here): Script {
  const init = (s: string) => {
    const f = path.join(day, s, 'room.c');
    if (!existsSync(f)) return [];
    const text = readFileSync(f, 'utf8');
    return text.slice(0, text.indexOf('// main procedure')).split('\n');
  };
  const arrivals: { from: string; x: number; z: number }[] = [];
  for (const other of readdirSync(day)) {
    for (const line of init(other)) {
      const d = callArgs(line, 'door_aot_set');
      if (d && slugOf(d[10]!) === slug) arrivals.push({ from: other, x: Number(d[11]), z: Number(d[13]) });
    }
  }
  const msgFile = path.join(day, slug, 'room.msg.txt');
  const msgs = existsSync(msgFile) ? readFileSync(msgFile, 'utf8').split('\n') : [];
  const text = (id: number) => (msgs.find((l) => l.startsWith(`${id - 128}:`)) ?? '').replace(/^\d+: /, '').replace(/\\[a-z]\{?\d*\}?|\\[no]/g, ' ').replace(/\s+/g, ' ').trim().slice(0, 32);
  const zones: Script['zones'][number][] = [];
  for (const line of init(slug)) {
    const zoneOf = (a: string[]) => ({ x0: +a[1]!, z0: +a[2]!, x1: +a[1]! + +a[3]!, z1: +a[2]! + +a[4]! });
    const d = callArgs(line, 'door_aot_set');
    if (d) {
      const flag = Number(d.at(-1));
      zones.push({ what: `the door to ${slugOf(d[10]!) ?? d[10]}`, zone: zoneOf(d), at: flag & 0x40 ? 'her' : 'ahead', door: slugOf(d[10]!) ?? d[10], touch: (flag & 0x80) === 0 });
      continue;
    }
    const it = callArgs(line, 'item_aot_set');
    if (it) {
      zones.push({ what: `the pickup of item ${it[5]}`, zone: zoneOf(it), at: 'ahead' });
      continue;
    }
    const a = callArgs(line, 'aot_set');
    if (a) {
      const what = a[5] === 'SCE_MESSAGE' ? `"${text(Number(a[7]))}"` : a[5] === 'SCE_USEITEM' ? 'an item used' : a[5] === 'SCE_ITEMBOX' ? 'the item box' : a[5] === 'SCE_TYPEWRITER' ? 'the typewriter' : a[5]!;
      zones.push({ what, zone: zoneOf(a), at: Number(a[6]) & 0x40 ? 'her' : 'ahead' });
    }
  }
  return { arrivals, zones };
}

/** Check one room from its renders; `record` reads its room.json from elsewhere, `day` its scripts. */
export function checkRoom(slug: string, record?: string, day?: string): Report {
  const renders = path.join(here, slug, 'renders');
  const json = JSON.parse(readFileSync(record ?? path.join(renders, 'room.json'), 'utf8')) as RoomJson;
  const spec = dayRooms.find((r) => r.slug === slug);
  const inside = spec && 'inside' in spec ? spec.inside : BUILT_INSIDE.has(slug);
  const knee = inside ? KNEE_INSIDE : KNEE_OUTSIDE;
  const read = (name: string) => {
    const f = path.join(renders, name);
    return existsSync(f) ? readDepth(f) : undefined;
  };
  const seen = json.cameras.map((cam, i) => {
    const all = read(`cam${i}.zall.png`);
    return all && seenBy(cam, all, json.bounds, knee);
  });
  // The floor each camera shows her on, as room.ts works it out.
  const depths = json.cameras.map((_, i) => read(`cam${i}.depth.png`));
  const floors = !spec || spec.cameraFloor === 'auto' ? autoFloors({ ...json, walls: [...json.walls, ...(json.voids ?? [])] }, depths) : spec.cameraFloor;
  return check(json, seen, floors, readScript(slug, day));
}

if (process.argv[1] === fileURLToPath(import.meta.url)) {
  const args = process.argv.slice(2);
  const showMap = args.includes('--map');
  const at = args.indexOf('--renders');
  const recordDir = at >= 0 ? args[at + 1] : undefined;
  const dayAt = args.indexOf('--day');
  const dayDir = dayAt >= 0 ? args[dayAt + 1] : undefined;
  const named = args.filter((a, i) => !a.startsWith('--') && !(at >= 0 && i === at + 1) && !(dayAt >= 0 && i === dayAt + 1));
  const slugs = named.length ? named : readdirSync(here).filter((s) => existsSync(path.join(here, s, 'renders', 'room.json'))).sort();
  const pct = (n: number, of: number) => `${((n / Math.max(1, of)) * 100).toFixed(1)}%`;
  for (const slug of slugs) {
    const record = recordDir ? path.join(recordDir, `${slug}.json`) : undefined;
    if (record && !existsSync(record)) continue;
    const r = checkRoom(slug, record, dayDir);
    const all = r.cameras.reduce((a, c) => ({ cells: a.cells + c.cells, solid: a.solid + c.solid, hole: a.hole + c.hole }), { cells: 0, solid: 0, hole: 0 });
    const cams = r.cameras.map((c, i) => `cam${i} ${pct(c.solid + c.hole, c.cells)}`).join(' ');
    console.log(`${slug}: solid ${pct(all.solid, all.cells)}, no floor ${pct(all.hole, all.cells)} of ${all.cells} cells (${cams}); doors walked past ${r.doors.length}, arrivals in a wall ${r.arrivals.length}, zones out of reach ${r.zones.length}`);
    for (const d of r.doors) console.log(`  past the door to ${d}`);
    for (const a of r.arrivals) console.log(`  arrival in a wall: ${a}`);
    for (const z of r.zones) console.log(`  out of reach: ${z}`);
    if (showMap) console.log(r.map);
  }
}
