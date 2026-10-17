// Play Rebecca's whole day from a new game to the save room, the way a
// player would and with nothing set by hand: no flags, no items given, no
// jumps between rooms. God mode (--god) keeps her alive and kills what she
// hits, so the run is about the route, not the fights.
//
// Act 1 is day.ts's stretches. From the gorge on, each job of the day is a
// goal (GOALS); Jev picks the next among those whose needs are done, and she
// walks there through the doors the room scripts have (world.ts). Every room
// change is checked against the door she took, and every state line for a
// jump no walk makes: those are the glitches this run is for.
//
//   TYPESAFE_API_KEY=$(ssh vault get typesafe-api-key) OVERLAY=<REB build folder> \
//     RE1_LAB_GAME_DIR='D:\Games\RE1-files' RE1_LAB_REPO_DIR='C:\Users\joell\Tools\re1-files' PORT=7811 \
//     node tools/harness/tests/playthrough.ts
//
// Without TYPESAFE_API_KEY the next goal is the nearest. RECORD=<name>
// records the window.
import path from 'node:path';
import { fetch, open, startRecording, stopRecording } from '../lab.ts';
import { DiedError, StuckError, approach, check, goTo, inControl, settle, useDoor, useFightBack, useItem } from '../flows.ts';
import { choice } from '../jev.ts';
import { Key, type GameLink } from '../link.ts';
import { Bank, flag, screen, type GameState } from '../state.ts';
import { CROW, STRETCHES, stretchNames } from '../day.ts';
import { Run } from '../scenario.ts';
import { loadWorld, route, slugAt, type Door, type Pickup, type Slug, type Zone } from '../world.ts';
import { CUT_FLAGS } from '../../rebecca/day/cutscenes.ts';
import { EVENT_FLAGS } from '../../rebecca/day/events.ts';
import { read } from './floor.ts';

const world = loadWorld();
const ADDER = 10;
/**
 * She stops to fight only what comes this close: god mode keeps her alive, and
 * a dog pacing a far corner (the woods' second) would hold her for minutes.
 */
const FIGHT_BACK = 2500;
/** Item ids (rebecca/items/items.ts). */
const ITEM = {
  rangerKeys: 57, cutters: 28, officeKey: 58, workshopKey: 59, cog: 41, jerrycan: 31, diesel: 32, crank: 30,
  switchKey: 55, quarryKey: 60, dynamite: 42, operatorKey: 56, fuses: 39, crowbar: 43, gateKey: 52, cellarKey: 53,
} as const;
/** FG_ITEM flags from 230 are her files (files/documents.ts). */
const isFile = (p: Pickup) => p.flag >= 230 && p.flag < 240;

type Goal =
  /** Pick up the item `item` (or her file, `file`) lying in `room`. */
  | { id: string; needs: string[]; kind: 'take'; room: Slug; item?: number; file?: true }
  /** A puzzle of events.ts: at its spot, use `use` or press action. */
  | { id: string; needs: string[]; kind: 'event'; room: Slug; use?: number }
  /** Open the locked way from `from` into `to` with the key in her bag. */
  | { id: string; needs: string[]; kind: 'unlock'; from: Slug; to: Slug }
  /** Go into `room` from `from` and sit through its cutscene; with `gets`, it hands her that item. */
  | { id: string; needs: string[]; kind: 'scene'; room: Slug; from?: Slug; cut: string; gets?: number; zone?: Zone }
  /** Check the thing in `room` whose words start `text`; with `cut`, that starts a cutscene. */
  | { id: string; needs: string[]; kind: 'look'; room: Slug; text: string; cut?: string }
  /** Just get to `room`. */
  | { id: string; needs: string[]; kind: 'visit'; room: Slug; from?: Slug };

/** Her day after the gorge, in the plan's order (plan/day.ts); `needs` as the plan has them. */
const GOALS: Goal[] = [
  // Act 1's end: what the gondola needs.
  { id: 'gondola-dead', needs: [], kind: 'visit', room: 'platform' },
  { id: 'duty-board', needs: ['gondola-dead'], kind: 'look', room: 'booth', text: 'The duty board' },
  { id: 'hal-phone', needs: ['gondola-dead'], kind: 'look', room: 'booth', text: 'The handset', cut: 'cut-phone' },
  // Act 2, north.
  { id: 'meet-partner', needs: [], kind: 'scene', room: 'woods', from: 'yard', cut: 'cut-partner' },
  { id: 'truck-keys', needs: ['meet-partner'], kind: 'scene', room: 'den', from: 'woods', cut: 'cut-den', gets: ITEM.rangerKeys },
  { id: 'cutters', needs: ['truck-keys'], kind: 'take', room: 'yard', item: ITEM.cutters },
  { id: 'quarantine', needs: [], kind: 'take', room: 'logging-road', file: true },
  { id: 'calendar', needs: [], kind: 'take', room: 'bunkhouse', file: true },
  { id: 'office-key', needs: [], kind: 'take', room: 'mess', item: ITEM.officeKey },
  { id: 'safe', needs: ['office-key', 'calendar'], kind: 'take', room: 'office', item: ITEM.workshopKey },
  { id: 'letters', needs: ['office-key'], kind: 'take', room: 'office', file: true },
  { id: 'mill-race', needs: [], kind: 'event', room: 'pond', use: ITEM.crank },
  { id: 'crane', needs: ['mill-race'], kind: 'event', room: 'sawmill' },
  { id: 'cog', needs: ['crane', 'safe'], kind: 'take', room: 'workshop', item: ITEM.cog },
  { id: 'cut-depot', needs: ['cutters'], kind: 'unlock', from: 'camp-yard', to: 'depot' },
  { id: 'jerrycan', needs: [], kind: 'take', room: 'shed', item: ITEM.jerrycan },
  { id: 'fuel', needs: ['cut-depot', 'jerrycan'], kind: 'event', room: 'depot', use: ITEM.jerrycan },
  // Act 2, west.
  { id: 'cut-chain', needs: ['cutters'], kind: 'unlock', from: 'road', to: 'washout' },
  { id: 'generator-on', needs: ['cut-chain', 'fuel'], kind: 'event', room: 'generator', use: ITEM.diesel },
  { id: 'tower-door', needs: ['cut-chain', 'truck-keys'], kind: 'unlock', from: 'tower-foot', to: 'tower-stairs' },
  { id: 'tower-view', needs: ['tower-door'], kind: 'scene', room: 'tower-top', from: 'tower-stairs', cut: 'cut-tower' },
  { id: 'switch-key', needs: ['tower-view'], kind: 'take', room: 'tower-top', item: ITEM.switchKey },
  { id: 'walt-log', needs: ['tower-view'], kind: 'take', room: 'tower-top', file: true },
  { id: 'line-on', needs: ['switch-key', 'generator-on'], kind: 'event', room: 'switch' },
  // Act 2, east and the mine.
  { id: 'diary', needs: [], kind: 'take', room: 'cottage', file: true },
  { id: 'quarry-key', needs: [], kind: 'take', room: 'cottage', item: ITEM.quarryKey },
  { id: 'dynamite', needs: ['quarry-key'], kind: 'take', room: 'quarry-office', item: ITEM.dynamite },
  { id: 'rosters', needs: ['quarry-key'], kind: 'take', room: 'quarry-office', file: true },
  { id: 'blast', needs: ['dynamite'], kind: 'event', room: 'mine-entrance', use: ITEM.dynamite },
  { id: 'mine-map', needs: ['blast'], kind: 'take', room: 'mine-office', file: true },
  { id: 'drain', needs: ['blast', 'generator-on'], kind: 'event', room: 'junction' },
  { id: 'mine-collapse', needs: ['drain'], kind: 'scene', room: 'gallery', from: 'junction', cut: 'cut-mine-collapse' },
  { id: 'op-key', needs: ['mine-collapse'], kind: 'scene', room: 'gallery', cut: 'cut-hal', gets: ITEM.operatorKey, zone: { x: 8000, z: 3400, w: 2000, d: 7300 } },
  { id: 'lift-up', needs: ['op-key'], kind: 'event', room: 'mine-lift' },
  { id: 'summit', needs: ['lift-up'], kind: 'visit', room: 'summit-trail', from: 'mine-lift' },
  // Act 2: the gondola.
  { id: 'fuses', needs: [], kind: 'take', room: 'shed', item: ITEM.fuses },
  { id: 'fit-cog', needs: ['cog', 'hal-phone'], kind: 'event', room: 'platform', use: ITEM.cog },
  { id: 'fit-fuse', needs: ['fuses', 'hal-phone'], kind: 'event', room: 'booth', use: ITEM.fuses },
  { id: 'gondola-runs', needs: ['fit-cog', 'fit-fuse', 'line-on', 'op-key'], kind: 'event', room: 'booth', use: ITEM.operatorKey },
  // Act 3.
  { id: 'ride', needs: ['gondola-runs'], kind: 'scene', room: 'car', from: 'platform', cut: 'cut-pylon' },
  { id: 'pylon-down', needs: ['ride'], kind: 'visit', room: 'valley-path', from: 'pylon' },
  { id: 'keeper-log', needs: ['pylon-down'], kind: 'take', room: 'lower-station', file: true },
  { id: 'kevin', needs: ['pylon-down'], kind: 'scene', room: 'crash', from: 'valley-path', cut: 'cut-kevin' },
  { id: 'crowbar', needs: ['kevin'], kind: 'take', room: 'crash', item: ITEM.crowbar },
  { id: 'pry-lodge', needs: ['crowbar'], kind: 'unlock', from: 'creek', to: 'lodge' },
  { id: 'gate-key', needs: ['pry-lodge'], kind: 'take', room: 'lodge', item: ITEM.gateKey },
  { id: 'gardener-diary', needs: ['pry-lodge'], kind: 'take', room: 'lodge', file: true },
  { id: 'open-gate', needs: ['gate-key'], kind: 'unlock', from: 'estate-wall', to: 'kennels' },
  { id: 'cellar-key', needs: ['open-gate'], kind: 'take', room: 'garden-shed', item: ITEM.cellarKey },
  { id: 'bulkhead', needs: ['cellar-key'], kind: 'unlock', from: 'back-garden', to: 'cellar' },
  // Act 4.
  { id: 'push-rack', needs: ['bulkhead'], kind: 'event', room: 'cellar' },
  { id: 'sleep', needs: ['push-rack'], kind: 'scene', room: 'save', from: 'crawl', cut: 'cut-sleep' },
];

// ---------------------------------------------------------------------------
// Watching for glitches
// ---------------------------------------------------------------------------

/** Faster than this, in game units a frame, is no walk or run: running is about 110. */
const JUMP = 400;

/** Reads every state line since the last look for jumps within a room and room changes no door explains. */
class Watch {
  private seen = 0;
  readonly glitches: string[] = [];
  /** Jumps while a scene had the controls: a scene may cut her to a new spot, so these are for a look, not failures. */
  readonly sceneCuts: string[] = [];
  private readonly link: GameLink;
  constructor(link: GameLink) {
    this.link = link;
  }

  /** Look at the lines since the last call. `door` is the door she was going through, if any. */
  look(door?: Door): void {
    const h = this.link.history;
    for (let i = Math.max(1, this.seen); i < h.length; i++) {
      const a = h[i - 1]!;
      const b = h[i]!;
      if (!a.play || !b.play) continue;
      const from = slugAt(a.stage, a.room);
      const to = slugAt(b.stage, b.room);
      if (a.stage !== b.stage || a.room !== b.room) {
        const taken = world.doors.find((d) => d.from === from && d.to === to);
        if (!taken) this.note(b, `room ${from ?? label(a)} to ${to ?? label(b)} with no door between them`);
        else if (door && (door.from !== from || door.to !== to)) this.note(b, `went for ${door.from} > ${door.to}, came out ${from} > ${to}`);
        else {
          // Where the door put her, on her first frame in the room, before any scene walks her on.
          const off = Math.hypot(b.player.x - taken.arrive.x, b.player.z - taken.arrive.z);
          if (off > 1500) this.note(b, `came through ${from} > ${to} ${Math.round(off)} units from where the door puts her`);
        }
        continue;
      }
      const frames = Math.max(1, b.frame - a.frame);
      const moved = Math.hypot(b.player.x - a.player.x, b.player.z - a.player.z);
      if (moved / frames > JUMP && moved > 1500) {
        const what = `jumped ${Math.round(moved)} units in ${frames} frames, (${a.player.x}, ${a.player.z}) to (${b.player.x}, ${b.player.z})`;
        if (inControl(a) && inControl(b)) this.note(b, what);
        else this.sceneCuts.push(`${from} f${b.frame}: ${what}`);
      }
    }
    this.seen = h.length;
  }

  private note(s: GameState, what: string): void {
    const line = `${slugAt(s.stage, s.room) ?? label(s)} f${s.frame}: ${what}`;
    console.log(`  GLITCH: ${line}`);
    this.glitches.push(line);
  }
}

const label = (s: { stage: number; room: number }) => `${s.stage}:${s.room.toString(16)}`;

// ---------------------------------------------------------------------------
// Getting about
// ---------------------------------------------------------------------------

const here = (s: GameState): Slug => {
  const slug = slugAt(s.stage, s.room);
  if (!slug) throw new StuckError(`she is in ${label(s)}, which is not a room of her day`, s);
  return slug;
};
const zoneOf = (r: { x0: number; z0: number; x1: number; z1: number }): Zone => ({ x: r.x0, z: r.z0, w: r.x1 - r.x0, d: r.z1 - r.z0 });
const has = (s: GameState, item: number) => s.items.some((it) => it.id === item);

class Player {
  /**
   * Doors that did not open, and when: shut until something changes (a flag
   * raised, an item got) or a minute passes, since a zombie in the doorway
   * stops a door as surely as a lock.
   */
  private closed = new Map<Door, number>();
  private progress = '';

  readonly run: Run;
  readonly watch: Watch;
  constructor(run: Run, watch: Watch) {
    this.run = run;
    this.watch = watch;
  }

  get link(): GameLink {
    return this.run.link;
  }

  /** Forget the closed doors once the flags or her bag have changed since they were closed. */
  private reopen(s: GameState): void {
    const now = [s.banks[Bank.common], s.banks[Bank.locks], s.items.map((i) => i.id).join(',')].join('|');
    if (now !== this.progress) this.closed.clear();
    this.progress = now;
    for (const [d, at] of this.closed) if (Date.now() - at > 60_000) this.closed.delete(d);
  }

  /** The way from where she is to `to`, through `via` last when given; undefined when every way is shut. */
  way(s: GameState, to: Slug, via?: Slug): Door[] | undefined {
    this.reopen(s);
    const shut = (d: Door) => this.closed.has(d) || (d.lock !== undefined && !flag(s, Bank.locks, d.lock.flag) && !has(s, d.lock.item));
    if (!via) return route(world, here(s), to, shut);
    const last = world.doors.find((d) => d.from === via && d.to === to);
    if (!last) return undefined;
    const first = route(world, here(s), via, (d) => shut(d) || d.to === to);
    return first && [...first, last];
  }

  /** Walk to `to`, door by door. Returns false when she cannot get there now. */
  async goTo(to: Slug, via?: Slug): Promise<boolean> {
    for (let tries = 0; tries < 12; tries++) {
      let s = await settle(this.link);
      if (here(s) === to && !via) return true;
      if (here(s) === to && via) {
        // In the room already but the scene wants her coming in from `via`.
        const back = world.doors.find((d) => d.from === to && d.to === via);
        if (!back || !(await this.through(back))) return false;
        continue;
      }
      const way = this.way(s, to, via);
      if (!way?.length) return false;
      if (!(await this.through(way[0]!))) continue;
      s = await this.link.state();
      if (here(s) === to) return true;
    }
    return false;
  }

  /** Go through one door; false (and the door closed for now) when it did not take her. */
  async through(door: Door): Promise<boolean> {
    const before = await this.link.state();
    this.watch.look();
    let s: GameState;
    try {
      s = await useDoor(this.link, door.zone, door.touch ? 20_000 : 15_000);
    } catch (err) {
      if (!(err instanceof StuckError) || err instanceof DiedError) throw err;
      s = await settle(this.link);
    }
    this.watch.look(door);
    const at = here(s);
    if (at === here(before)) {
      this.run.log(s, `the way to ${door.to} did not open`);
      this.closed.set(door, Date.now());
      return false;
    }
    if (at !== door.to) this.run.log(s, `went for ${door.to}, came out in ${at}`);
    else this.run.log(s, `into ${at}`);
    // Unarmed after the mine: fighting back would only stand her still.
    useFightBack(s.player.weapon > 0 ? FIGHT_BACK : 0, [CROW, ADDER]);
    await this.scavenge();
    return true;
  }

  /** Low on rounds with a slot free: take a clip lying in this room, as a player would. */
  async scavenge(): Promise<void> {
    let s = await this.link.state();
    const ammo = s.items.filter((i) => i.id === CLIP).reduce((n, i) => n + i.qty, 0) + (s.items[s.player.weapon - 1]?.qty ?? 0);
    if (s.player.weapon <= 0 || ammo >= 30 || freeSlots(s) === 0) return;
    const clip = world.pickups.find((p) => p.room === here(s) && p.item === CLIP && flag(s, Bank.roomItems, p.flag));
    if (!clip) return;
    try {
      for (let i = 0; i < 3 && flag(s, Bank.roomItems, clip.flag); i++) s = await check(this.link, clip.zone);
      this.run.log(s, flag(s, Bank.roomItems, clip.flag) ? 'could not take the clip here' : `took a clip (${ammo} rounds before)`);
    } catch (err) {
      if (!(err instanceof StuckError) || err instanceof DiedError) throw err;
      this.run.log(err.state, `could not reach the clip: ${err.message}`);
    }
  }
}

// ---------------------------------------------------------------------------
// Goals
// ---------------------------------------------------------------------------

const pickupFor = (g: Extract<Goal, { kind: 'take' }>) =>
  world.pickups.find((p) => p.room === g.room && (g.file ? isFile(p) : p.item === g.item));

/** Whether the goal is done, read from the game. */
function done(s: GameState, g: Goal, reached: Set<string>): boolean {
  switch (g.kind) {
    case 'take': {
      const p = pickupFor(g);
      return p !== undefined && !flag(s, Bank.roomItems, p.flag);
    }
    case 'event':
      return flag(s, Bank.common, EVENT_FLAGS.get(g.id)!);
    case 'unlock': {
      const d = world.doors.find((x) => x.from === g.from && x.to === g.to)!;
      return d.lock !== undefined && flag(s, Bank.locks, d.lock.flag);
    }
    case 'scene':
      return flag(s, Bank.common, CUT_FLAGS.get(g.cut)!) && (g.gets === undefined || has(s, g.gets) || reached.has(g.id));
    case 'look':
      return g.cut ? flag(s, Bank.common, CUT_FLAGS.get(g.cut)!) : reached.has(g.id);
    case 'visit':
      return reached.has(g.id);
  }
}

// ---------------------------------------------------------------------------
// Her bag: six slots, three of them her gun, its clip and her knife at the start
// ---------------------------------------------------------------------------

const BERETTA = 0x02;
const CLIP = 0x0b;

/** What the rest of the day still needs from her bag: the items goals use, the keys of doors still locked, her gun. */
function needed(s: GameState, reached: Set<string>): Set<number> {
  const keep = new Set<number>([BERETTA, CLIP]);
  for (const g of GOALS) {
    if (done(s, g, reached)) continue;
    if (g.kind === 'event' && g.use !== undefined) keep.add(g.use);
  }
  for (const d of world.doors) if (d.lock && !flag(s, Bank.locks, d.lock.flag)) keep.add(d.lock.item);
  return keep;
}

const freeSlots = (s: GameState) => s.items.filter((i) => i.id === 0).length;

/**
 * Make a slot free: to the nearest item box, and put away the first thing she
 * carries that the day no longer needs. The box screen opens with her bag's
 * cursor on its first slot and the box's on box slot 0, whatever the box
 * holds (MainMenu.cpp main_menu and the box states). She picks the item, steps
 * the box's cursor down to its first empty slot, and action swaps them.
 */
async function stash(p: Player, reached: Set<string>): Promise<void> {
  let s = await p.link.state();
  const spare = s.items.findIndex((i) => i.id !== 0 && !needed(s, reached).has(i.id));
  if (spare < 0) throw new StuckError(`her bag is full of things the day still needs: ${s.items.map((i) => i.id).join(', ')}`, s);
  const near = [...world.boxes].sort((a, b) => (p.way(s, a.room)?.length ?? 99) - (p.way(s, b.room)?.length ?? 99))[0]!;
  p.run.log(s, `bag full: to the item box in ${near.room} to put away item ${s.items[spare]!.id}`);
  if (!(await p.goTo(near.room))) throw new StuckError(`no way to the item box in ${near.room}`, s);
  s = await approach(p.link, near.zone);
  const id = s.items[spare]!.id;
  const slot = s.items.findIndex((i) => i.id === id);
  const empty = s.box.findIndex((b) => b.id === 0);
  if (empty < 0) throw new StuckError(s.box.length ? 'the item box is full' : 'the game does not report the item box: rebuild the exe', s);
  await p.link.tap(Key.action, 3);
  s = await p.link.waitFor((st) => screen(st) === 'menu', 'the box screen', 20_000);
  await p.link.frames(30);
  // Each step of the box's list slides for 15 frames and drops a key pressed meanwhile.
  const keys = [...Array<number>(slot >> 1).fill(Key.down), ...(slot & 1 ? [Key.right] : []), Key.action, ...Array<number>(empty).fill(Key.down), Key.action];
  for (const key of keys) {
    await p.link.tap(key, 3);
    await p.link.frames(22);
  }
  s = await settle(p.link);
  if (s.items.some((i) => i.id === id)) throw new StuckError(`item ${id} is still in her bag after the box`, s);
  p.run.log(s, `put item ${id} in the box`);
}

/** The room a goal is worked in. */
const roomFor = (g: Goal): Slug => (g.kind === 'unlock' ? g.from : g.room);

async function work(p: Player, g: Goal, reached: Set<string>): Promise<void> {
  const { link, run } = p;
  // A pickup, or a scene that hands her something, needs a free slot.
  if ((g.kind === 'take' && !g.file) || (g.kind === 'scene' && g.gets !== undefined)) {
    if (freeSlots(await link.state()) === 0) await stash(p, reached);
  }
  const via = g.kind === 'scene' || g.kind === 'visit' ? g.from : undefined;
  if (!(await p.goTo(roomFor(g), via))) throw new StuckError(`no way to ${roomFor(g)}${via ? ` from ${via}` : ''}`, await link.state());
  let s = await settle(link);
  switch (g.kind) {
    case 'take': {
      const pick = pickupFor(g);
      if (!pick) throw new StuckError(`nothing to take in ${g.room} for ${g.id}`, s);
      for (let i = 0; i < 3 && !done(s, g, reached); i++) s = await check(link, pick.zone);
      break;
    }
    case 'event': {
      const spot = read(g.room)?.spots?.find((sp) => sp.step === g.id)?.zone;
      if (!spot) throw new StuckError(`${g.room} has no spot for ${g.id}`, s);
      for (let i = 0; i < 3 && !done(s, g, reached); i++) {
        s = await approach(link, zoneOf(spot));
        if (g.use !== undefined) {
          if (!has(s, g.use)) throw new StuckError(`${g.id} needs item ${g.use}, and she has none`, s);
          await useItem(link, g.use);
          // A room script acts a second after the status screen closes.
          await link.frames(90);
        } else {
          await link.tap(Key.action, 3);
          await link.frames(30);
        }
        s = await settle(link);
      }
      break;
    }
    case 'unlock': {
      const d = world.doors.find((x) => x.from === g.from && x.to === g.to)!;
      await p.through(d);
      s = await link.state();
      break;
    }
    case 'scene':
      if (g.zone) s = await goTo(link, run.dataDirs, g.zone.x + g.zone.w / 2, g.zone.z + g.zone.d / 2, { radius: 300 });
      s = await settle(link, undefined, 300_000);
      if (g.gets !== undefined && !has(s, g.gets)) {
        // The scene should have handed it over; else it lies there as a pickup.
        const lying = world.pickups.find((x) => x.room === g.room && x.item === g.gets);
        if (lying) {
          run.fail(`${g.cut} did not give her item ${g.gets}: picking it up instead`);
          for (let i = 0; i < 3 && !has(s, g.gets); i++) s = await check(link, lying.zone);
        }
      }
      reached.add(g.id);
      break;
    case 'look': {
      const c = read(g.room)?.checks?.find((x) => x.text.startsWith(g.text));
      if (!c) throw new StuckError(`${g.room} has nothing to check that says "${g.text}"`, s);
      s = await check(link, zoneOf(c.zone));
      s = await settle(link, undefined, 300_000);
      reached.add(g.id);
      break;
    }
    case 'visit':
      reached.add(g.id);
      break;
  }
  p.watch.look();
}

/** The next goal: Jev's pick of the ready ones, or the nearest without a key. */
async function next(p: Player, s: GameState, ready: Goal[]): Promise<Goal> {
  const hops = (g: Goal) => p.way(s, roomFor(g))?.length ?? 99;
  const near = [...ready].sort((a, b) => hops(a) - hops(b));
  if (!process.env.TYPESAFE_API_KEY || near.length === 1) return near[0]!;
  const options = Object.fromEntries(near.slice(0, 6).map((g) => [g.id, `${g.kind} in ${roomFor(g)}, ${hops(g)} doors away`]));
  try {
    const a = await choice(
      { room: here(s), carrying: s.items.filter((i) => i.id).map((i) => i.id), hp: s.player.hp },
      'Rebecca is playing through a survival horror day. Pick the job she should do next: prefer the nearest, and a job that unlocks others over a side file.',
      options,
    );
    if (process.env.HARNESS_TRACE) console.log(`  jev: ${a.choice} (${a.confidence.toFixed(2)})`);
    return ready.find((g) => g.id === a.choice) ?? near[0]!;
  } catch (err) {
    console.log(`  jev: ${(err as Error).message}; taking the nearest`);
    return near[0]!;
  }
}

// ---------------------------------------------------------------------------

const overlay = process.env.OVERLAY;
if (!overlay) throw new Error('set OVERLAY to the REB build folder');

useFightBack(FIGHT_BACK, [CROW, ADDER]);
const session = await open(Number(process.env.PORT ?? 7811), `--mode REB --god --boot rebecca`);
const record = process.env.RECORD;
const remoteVideo = record ? `${process.env.RE1_LAB_GAME_DIR ?? 'D:\\Games\\RE1-decomp'}\\${record}.mp4` : undefined;
if (remoteVideo) startRecording(remoteVideo);
const run = new Run(session.link, overlay);
const watch = new Watch(session.link);
const player = new Player(run, watch);
const reached = new Set<string>();
const failed = new Map<string, number>();
/** Fresh starts on the goals she gave up on, once nothing else is left: a door a zombie held may open later. */
let secondWinds = 3;
try {
  let s = await session.link.waitFor((st) => st.play, 'gameplay', 180_000);
  if (!s.god) run.fail('god mode is off: the exe is older than --god');
  for (const name of stretchNames) {
    await STRETCHES[name]!.play(run);
    watch.look();
  }
  for (;;) {
    s = await settle(session.link);
    const left = GOALS.filter((g) => !done(s, g, reached) && (failed.get(g.id) ?? 0) < 2);
    const ready = left.filter((g) => g.needs.every((n) => reached.has(n) || done(s, GOALS.find((x) => x.id === n)!, reached)));
    if (!ready.length && failed.size && secondWinds-- > 0) {
      run.log(s, `trying again: ${[...failed.keys()].join(', ')}`);
      failed.clear();
      continue;
    }
    if (!left.length) break;
    if (!ready.length) {
      run.fail(`stuck: nothing left she can do; still to do ${left.map((g) => g.id).join(', ')}`);
      break;
    }
    const g = await next(player, s, ready);
    run.log(s, `goal: ${g.id} (${g.kind} in ${roomFor(g)})`);
    try {
      await work(player, g, reached);
      s = await session.link.state();
      if (done(s, g, reached)) {
        reached.add(g.id);
        run.log(s, `done: ${g.id}`);
      } else {
        failed.set(g.id, (failed.get(g.id) ?? 0) + 1);
        run.log(s, `not done: ${g.id} (try ${failed.get(g.id)}); carrying ${s.items.map((i) => i.id).join(', ')}`);
        await run.picture(`play-${g.id}-${failed.get(g.id)}`);
      }
    } catch (err) {
      if (!(err instanceof StuckError) || err instanceof DiedError) throw err;
      failed.set(g.id, (failed.get(g.id) ?? 0) + 1);
      run.log(err.state, `stuck on ${g.id}: ${err.message}`);
      await run.picture(`play-${g.id}-stuck-${failed.get(g.id)}`);
    }
  }
  for (const [id, n] of failed) if (n >= 2 && !reached.has(id)) run.fail(`gave up on ${id}`);
  if (!reached.has('sleep')) run.fail('the day never reached the save room');
  for (const line of watch.glitches) run.fail(`glitch: ${line}`);
  for (const line of watch.sceneCuts) console.log(`  scene cut: ${line}`);
  await run.picture('play-end');
  run.finish();
} catch (err) {
  await run.crashed();
  throw err;
} finally {
  if (remoteVideo) {
    const local = path.join(run.out, `${record}.mp4`);
    fetch(stopRecording(remoteVideo), local);
    console.log(`video: ${local}`);
  }
  session.end();
}
