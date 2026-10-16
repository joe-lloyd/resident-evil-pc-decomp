// The rooms of Rebecca's day changing in front of her. For every change of
// state a scene renders (kit.Room.state, day/<slug>/renders/room.json), work
// what causes it the way a player does and take pictures from the camera that
// shows it best: before, as it happens, once she has control again, and after
// she comes back into the room. Checks that the change is on screen where the
// renders put it, and that it stays.
//
//   node tools/harness/tests/changes.ts [<state> ...]      (default: every state)
//
// Pictures go to $OUT (default /tmp/reb-changes-shots), named
// <state>-<n>-<moment>.png. Look at them: the test can only tell that the
// picture changed where the renders did, not that it reads.
//
// Needs the engine and the overlay deployed. Prints a line per change and
// exits 1 if any fails.
import { existsSync, mkdirSync, readFileSync } from 'node:fs';
import path from 'node:path';
import { open, fetch } from '../lab.ts';
import { Key, type GameLink } from '../link.ts';
import { faceTowards, headingTo, settle, useItem } from '../flows.ts';
import { readBmp, readPng, writePng, type Image } from '../image.ts';
import { Bank, flag, type GameState } from '../state.ts';
import { dayRooms, type DayRoom } from '../../rebecca/day/rooms.ts';
import { autoFloors, readDepth } from '../../rebecca/day/floors.ts';
import { changedRects } from '../../rebecca/bganim.ts';
import { to555 } from '../../rebecca/pak.ts';
import { EVENT_FLAGS, EVENTS, keyItem } from '../../rebecca/day/events.ts';
import { lockFlag } from '../../rebecca/day/scripts.ts';
import { day, inside, nearest, opens, outward, read, walkable, type Rect } from './floor.ts';

const out = process.env.OUT ?? '/tmp/reb-changes-shots';
const remoteDir = process.env.RE1_LAB_SHOT_DIR ?? 'C:\\Users\\joell\\Tools\\wintool';
mkdirSync(out, { recursive: true });

interface StateJson {
  name: string;
  bank: number;
  bit: number;
}
interface RoomJson {
  cameras: unknown[];
  walls: Rect[];
  voids?: Rect[];
  bounds: Rect;
  states?: StateJson[];
}

/** How a change is caused: an event of events.ts, a key item used on a locked way, or the yard's winch. */
type Cause =
  | { kind: 'event'; step: string }
  | { kind: 'lock'; to: string; item: number }
  | { kind: 'use'; item: number; zone: Rect };

interface Change {
  name: string;
  room: DayRoom;
  /** The flag that shows it, as the game's banks number them. */
  bank: number;
  bit: number;
  cause: Cause;
  /** The camera whose background changes most, and where (320x240). */
  camera: number;
  rects: { x: number; y: number; w: number; h: number }[];
}

/** The hand-written yard's winch: the crank used on it drags the pine clear (yard/room.c). */
const HAND: Record<string, Cause> = {
  pine: { kind: 'use', item: 30, zone: { x0: 19210, z0: 17170, x1: 20910, z1: 19550 } },
};

const to15 = (img: Image) => {
  const o = new Uint16Array(img.width * img.height);
  for (let i = 0; i < o.length; i++) o[i] = to555(img.rgb[i * 3]!, img.rgb[i * 3 + 1]!, img.rgb[i * 3 + 2]!);
  return o;
};

/** The lock a door's record carries in its room script: 0x80 | the g_LocksFlags bit. */
function lockOf(slug: string, toRoom: DayRoom): { bit: number; item: number } | undefined {
  const c = readFileSync(path.join(day, slug, 'room.c'), 'utf8');
  const name = `ROOM_${toRoom.stage + 1}${toRoom.room.toString(16).toUpperCase().padStart(2, '0')}`;
  for (const m of c.matchAll(/door_aot_set\(([^;]*)\);/g)) {
    const a = m[1]!.replace(/\/\*.*?\*\//g, '').split(',').map((t) => t.trim());
    if (a[10] === name && Number(a[9]) & 0x80) return { bit: Number(a[9]) & 0x3f, item: Number(a[15]) };
  }
  return undefined;
}

function changes(): Change[] {
  const bySlug = new Map(dayRooms.map((r) => [r.slug, r]));
  const list: Change[] = [];
  for (const room of dayRooms) {
    const file = path.join(day, room.slug, 'renders', 'room.json');
    if (!existsSync(file)) continue;
    const json = JSON.parse(readFileSync(file, 'utf8')) as RoomJson;
    for (const st of json.states ?? []) {
      let cause: Cause | undefined = HAND[st.name];
      let bank = st.bank;
      let bit = st.bit;
      const event = EVENTS.find((e) => e.step === st.name);
      if (event && bit < 0) {
        cause = { kind: 'event', step: event.step };
        bit = EVENT_FLAGS.get(event.step)!;
      }
      // A key item on a lock: the lock's flag, as room.ts shows it by.
      const lock = bit < 0 ? lockFlag(st.name) : undefined;
      if (lock !== undefined) [bank, bit] = [Bank.locks, lock];
      const lockTo = (read(room.slug)?.doors ?? []).map((d) => bySlug.get(d.to)).find((r) => r && bank === Bank.locks && lockOf(room.slug, r)?.bit === bit);
      if (lockTo) cause = { kind: 'lock', to: lockTo.slug, item: lockOf(room.slug, lockTo)!.item };
      if (!cause) throw new Error(`${room.slug}: nothing in this test causes state ${st.name}`);
      // The camera whose picture the change moves most.
      let best = { camera: -1, area: 0, rects: [] as Change['rects'] };
      json.cameras.forEach((_, i) => {
        const base = to15(readPng(path.join(day, room.slug, 'renders', `cam${i}.png`)));
        const after = to15(readPng(path.join(day, room.slug, 'renders', `cam${i}.s-${st.name}.png`)));
        const rects = changedRects(base, [after]);
        const area = rects.reduce((n, r) => n + r.w * r.h, 0);
        if (area > best.area) best = { camera: i, area, rects };
      });
      if (best.camera < 0) throw new Error(`${room.slug}: state ${st.name} changes no camera's picture`);
      list.push({ name: st.name, room, bank, bit, cause, camera: best.camera, rects: best.rects });
    }
  }
  return list;
}

/** A point on the floor of `camera`, as the room's camera switch zones have it (day/room.ts). */
function cameraFloor(room: DayRoom, camera: number): Rect[] {
  if (room.cameraFloor !== 'auto') {
    const f = room.cameraFloor[camera];
    if (!f) throw new Error(`${room.slug} has no camera ${camera}`);
    return 'x0' in f ? [f] : [...f];
  }
  const renders = path.join(day, room.slug, 'renders');
  const json = JSON.parse(readFileSync(path.join(renders, 'room.json'), 'utf8'));
  const depths = json.cameras.map((_: unknown, i: number) => {
    const f = path.join(renders, `cam${i}.depth.png`);
    return existsSync(f) ? readDepth(f) : undefined;
  });
  return autoFloors({ ...json, walls: [...json.walls, ...(json.voids ?? [])] }, depths)[camera]!;
}

/**
 * The room's floor records. A hand-written room's scene records no doors, and
 * walkable() starts from where doors bring her in: start it from the place
 * she works the change instead.
 */
function floorOf(c: Change) {
  const json = read(c.room.slug)!;
  if (json.doors?.length || c.cause.kind !== 'use') return json;
  const z = c.cause.zone;
  return { ...json, doors: [{ to: '', zone: { x0: -1, z0: -1, x1: -1, z1: -1 }, arrive: { x: (z.x0 + z.x1) / 2, z: (z.z0 + z.z1) / 2 } }] };
}

/** Stand her somewhere the game shows from `camera`. */
async function onCamera(link: GameLink, c: Change): Promise<GameState> {
  const json = floorOf(c);
  const touch = (json.doors ?? []).filter((d) => d.to && !opens(c.room.slug, d.zone)).map((d) => d.zone);
  const cells = walkable(json, touch);
  const floor = cameraFloor(c.room, c.camera);
  const tries = floor
    .map((r) => nearest(cells, (r.x0 + r.x1) / 2, (r.z0 + r.z1) / 2, ([x, z]) => inside(r, x, z, -300)))
    .filter((p): p is [number, number] => p !== undefined);
  for (const [x, z] of tries) {
    await link.place(x, z);
    const s = await link.frames(20);
    if (s.camera === c.camera) return s;
  }
  throw new Error(`could not stand her where camera ${c.camera} shows her`);
}

/** How far ahead of her the game looks for a zone she acts on (update_player_position). */
const REACH = 600;

/** Stand her where the point she reaches falls in `zone`, facing its middle. */
async function stand(link: GameLink, c: Change, zone: Rect): Promise<void> {
  const slug = c.room.slug;
  const json = floorOf(c);
  const touch = (json.doors ?? []).filter((d) => d.to && !opens(slug, d.zone)).map((d) => d.zone);
  const cx = (zone.x0 + zone.x1) / 2;
  const cz = (zone.z0 + zone.z1) / 2;
  const reaches = ([x, z]: [number, number]) => {
    const d = Math.hypot(cx - x, cz - z) || 1;
    return inside(zone, x + ((cx - x) / d) * REACH, z + ((cz - z) / d) * REACH);
  };
  const at = nearest(walkable(json, touch), cx, cz, reaches);
  if (!at) throw new Error('nowhere she can walk to reaches the spot');
  await link.place(at[0], at[1]);
  await link.frames(6);
  await faceTowards(link, cx, cz);
}

/** Do what causes the change, and return the moment it is done: before any line it brings is closed. */
async function cause(link: GameLink, c: Change): Promise<void> {
  const k = c.cause;
  if (k.kind === 'event') {
    const e = EVENTS.find((x) => x.step === k.step)!;
    for (const n of e.needs ?? []) await link.setFlag(Bank.common, EVENT_FLAGS.get(n)!, true);
    const zone = read(c.room.slug)!.spots!.find((sp) => sp.step === e.step)!.zone;
    await stand(link, c, zone);
    if (e.use) {
      const id = keyItem(e.use).id;
      if (!(await link.state()).items.some((it) => it.id === id)) await link.give(id, 1);
      await useItem(link, id, false);
    } else {
      await link.tap(Key.action, 3);
    }
    return;
  }
  if (k.kind === 'use') {
    if (!(await link.state()).items.some((it) => it.id === k.item)) await link.give(k.item, 1);
    await stand(link, c, k.zone);
    await useItem(link, k.item, false);
    return;
  }
  // A key item on a locked way: stand in the door's zone facing out and press action.
  const json = read(c.room.slug)!;
  const door = json.doors!.find((d) => d.to === k.to)!;
  if (!(await link.state()).items.some((it) => it.id === k.item)) await link.give(k.item, 1);
  const touch = json.doors!.filter((d) => d !== door && !opens(c.room.slug, d.zone)).map((d) => d.zone);
  const cx = (door.zone.x0 + door.zone.x1) / 2;
  const cz = (door.zone.z0 + door.zone.z1) / 2;
  const at = nearest(walkable(json, touch), cx, cz, ([x, z]) => inside(door.zone, x, z));
  if (!at) throw new Error(`nowhere in the way to ${k.to} she can stand`);
  const [fx, fz] = outward(json, door.zone);
  await link.place(at[0], at[1], headingTo(at[0], at[1], fx, fz));
  await link.frames(6);
  await link.tap(Key.action, 2);
}

/** Mean difference, 0-255, between two game frames over the change's rects (320x240 rects on the 640x480 frame). */
function difference(a: Image, b: Image, rects: Change['rects']): number {
  const sx = a.width / 320;
  const sy = a.height / 240;
  let sum = 0;
  let n = 0;
  for (const r of rects) {
    for (let y = Math.floor(r.y * sy); y < (r.y + r.h) * sy; y++) {
      for (let x = Math.floor(r.x * sx); x < (r.x + r.w) * sx; x++) {
        const i = (y * a.width + x) * 3;
        sum += Math.abs(a.rgb[i]! - b.rgb[i]!) + Math.abs(a.rgb[i + 1]! - b.rgb[i + 1]!) + Math.abs(a.rgb[i + 2]! - b.rgb[i + 2]!);
        n += 3;
      }
    }
  }
  return n ? sum / n : 0;
}

/** Shots are saved on the game machine as they are taken and fetched afterwards, so a quick run of them stays quick. */
const taken: { remote: string; local: string }[] = [];
async function shot(link: GameLink, c: Change, i: number, moment: string): Promise<string> {
  const name = `${c.name}-${i}-${moment}`;
  const remote = `${remoteDir}\\${name}.bmp`;
  await link.shot(remote);
  taken.push({ remote, local: path.join(out, `${name}.png`) });
  return path.join(out, `${name}.png`);
}
function fetchShots(): void {
  for (const t of taken.splice(0)) {
    const bmp = t.local.replace(/\.png$/, '.bmp');
    fetch(t.remote, bmp);
    writePng(t.local, readBmp(bmp));
  }
}

const wanted = process.argv.slice(2);
const list = changes().filter((c) => !wanted.length || wanted.includes(c.name));
if (!list.length) throw new Error(`no change named ${wanted.join(', ')}`);
const first = list[0]!.room;
const session = await open(Number(process.env.PORT ?? 7801), `--mode REB --boot rebecca:${first.stage}:${first.room}`);
const link = session.link;
const failures: string[] = [];
try {
  await link.waitFor((s) => s.play, 'gameplay', 120_000);
  // The pictures are of the rooms, not her fights: every enemy of her day has
  // a kill flag in 186-254 (day/foes.ts), and a set one keeps it out.
  for (let f = 186; f <= 254; f++) await link.setFlag(Bank.enemies, f, true);
  for (const c of list) {
    const here = (s: GameState) => s.stage === c.room.stage && s.room === c.room.room;
    try {
      await link.setFlag(c.bank, c.bit, false);
      await link.room(c.room.stage, c.room.room);
      await settle(link, here);
      await onCamera(link, c);
      const before = await shot(link, c, 0, 'before');
      await cause(link, c);
      // As it happens: a picture every half second for three seconds, closing nothing.
      for (let k = 1; k <= 6; k++) {
        await link.frames(15);
        await shot(link, c, k, 'during');
      }
      let s = await settle(link, here);
      if (!flag(s, c.bank, c.bit)) throw new Error(`the flag (bank ${c.bank}, ${c.bit}) is still clear`);
      s = await onCamera(link, c);
      const after = await shot(link, c, 7, 'after');
      // Into the room again: the change stays.
      await link.room(c.room.stage, c.room.room);
      await settle(link, here);
      await onCamera(link, c);
      const again = await shot(link, c, 8, 'again');
      fetchShots();
      const [b, a, g] = [before, after, again].map((p) => readPng(p));
      const moved = difference(b!, a!, c.rects);
      const kept = difference(a!, g!, c.rects);
      const note = `camera ${c.camera}, ${moved.toFixed(1)} changed, ${kept.toFixed(1)} after coming back`;
      if (moved < 6) throw new Error(`the picture barely changed where the renders do (${note})`);
      if (kept > moved / 2) throw new Error(`it did not stay changed (${note})`);
      console.log(`ok    ${c.name} (${c.room.slug}): ${note}`);
    } catch (err) {
      fetchShots();
      await link.release().catch(() => undefined);
      await settle(link, () => true, 20_000).catch(() => undefined);
      failures.push(c.name);
      console.log(`FAIL  ${c.name} (${c.room.slug}): ${err instanceof Error ? err.message : String(err)}`);
    }
  }
} finally {
  session.end();
}
console.log(failures.length ? `${failures.length} changes failed; pictures in ${out}` : `every change shows; pictures in ${out}`);
process.exit(failures.length ? 1 : 0);
