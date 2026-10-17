// What her day sounds like, checked in the game. The harness can't hear, so
// test mode says what the game loaded and played (TestMode.cpp "snd" and
// "bgm"):
//
// - Footsteps: she walks on each kind of floor and the step that plays is
//   that floor's (sound/ground.ts): gravel and its verge on the forestry
//   road, running too; the bunkhouse's boards; the bridge's planks over the
//   gorge; the mine office's rock; the flooded gallery and the creek's ford;
//   and the concrete, metal, lino and carpet of her other rooms.
// - Ambience: each room plays exactly the channels its cue gives it in the
//   music table (plan/music.ts), its music and its loops, and no loop twice
//   what the music has.
// - Doors: a wooden door and an iron one play RE1's own sounds; a walk
//   through a gate opens and shuts it; the ladder up through the hatch.
// - Chris's game keeps RE1's own: his steps are RE1's, and no loop plays.
//
//   OVERLAY=<REB build> PORT=7811 RE1_LAB_GAME_DIR='D:\Games\RE1-files' node tools/harness/tests/sound.ts [out dir]
//
// It saves a picture of her on each floor and through each door in the out
// dir, /tmp/rebecca-sound-game by default.
import { open } from '../lab.ts';
import { snapshot } from '../snapshot.ts';
import { Key, type GameLink } from '../link.ts';
import { headingTo, settle } from '../flows.ts';
import { Bank, roomLabel, type GameState } from '../state.ts';
import { dayRooms } from '../../rebecca/day/rooms.ts';
import { EVENT_FLAGS } from '../../rebecca/day/events.ts';
import { LOCK_FLAGS } from '../../rebecca/day/scripts.ts';
import { isGround, STEP_SETS, type Ground } from '../../rebecca/sound/ground.ts';
import { AMBIENCES, ambienceFile, type Ambience } from '../../rebecca/sound/ambience.ts';
import { musicTable, roomChannels } from '../../rebecca/music/table.ts';
import { CUES } from '../../rebecca/plan/music.ts';
import { day as plan } from '../../rebecca/plan/day.ts';
import { existsSync, readFileSync } from 'node:fs';
import path from 'node:path';
import { day, inside, outward, read, walkable, type Json, type Rect } from './floor.ts';

const port = Number(process.env.PORT ?? 7811);
if (!process.env.OVERLAY) throw new Error('set OVERLAY to the REB build folder the game has');

const outDir = process.argv[2] ?? '/tmp/rebecca-sound-game';
const shot = (link: GameLink, name: string) => snapshot(link, outDir, `sound-${name}`);

const failures: string[] = [];
const check = (ok: boolean, line: string, why: string) => {
  console.log(`${ok ? 'ok  ' : 'FAIL'} ${line}`);
  if (!ok) failures.push(`${line}: ${why}`);
};

const room = (slug: string) => {
  const r = dayRooms.find((d) => d.slug === slug);
  if (!r) throw new Error(`no room ${slug}`);
  return r;
};

interface Floors extends Json {
  ground: Ground;
  floors: (Rect & { kind: Ground })[];
}
const field = (o: unknown, k: string): unknown => (typeof o === 'object' && o !== null ? Reflect.get(o, k) : undefined);
const kindOf = (v: unknown): Ground | undefined => (typeof v === 'string' && isGround(v) ? v : undefined);

/** The room's records, with what its scene says is underfoot (kit.Room.ground and floor). */
function floorsOf(slug: string): Floors {
  const j = read(slug);
  const raw: unknown = JSON.parse(readFileSync(path.join(day, slug, 'renders', 'room.json'), 'utf8'));
  const ground = kindOf(field(raw, 'ground'));
  if (!j || !ground) throw new Error(`${slug}: its room.json says nothing of its floors`);
  const parts = field(raw, 'floors');
  const floors = (Array.isArray(parts) ? parts : []).map((p: unknown, i) => {
    const kind = kindOf(field(p, 'kind'));
    const [x0, z0, x1, z1] = ['x0', 'z0', 'x1', 'z1'].map((k) => field(p, k));
    if (!kind || typeof x0 !== 'number' || typeof z0 !== 'number' || typeof x1 !== 'number' || typeof z1 !== 'number') {
      throw new Error(`${slug}: floor ${i} is not a kind and a rectangle`);
    }
    return { kind, x0, z0, x1, z1 };
  });
  return { ...j, ground, floors };
}
/** The kind underfoot at (x, z), as room.ts writes the zones: the first part that holds it, else the ground. */
const kindAt = (f: Floors, x: number, z: number): Ground => f.floors.find((p) => inside(p, x, z))?.kind ?? f.ground;

/**
 * A place to walk on `kind`: a reachable spot and a heading where the next
 * `run` units are all reachable floor of that kind, clear of every door.
 */
function walkOn(slug: string, kind: Ground, run: number): { x: number; z: number; tx: number; tz: number } {
  const f = floorsOf(slug);
  const cells = walkable(f, (f.doors ?? []).map((d) => d.zone));
  const free = new Set(cells.map(([x, z]) => `${x},${z}`));
  const ok = (x: number, z: number) => kindAt(f, x, z) === kind && cells.some(([cx, cz]) => Math.abs(cx - x) <= 125 && Math.abs(cz - z) <= 125);
  let best: { x: number; z: number; tx: number; tz: number; score: number } | undefined;
  for (const [x, z] of cells) {
    if (!free.has(`${x},${z}`) || kindAt(f, x, z) !== kind) continue;
    for (let a = 0; a < 8; a++) {
      const dx = Math.cos((a * Math.PI) / 4), dz = Math.sin((a * Math.PI) / 4);
      let len = 0;
      while (len < run + 400 && ok(x + dx * (len + 125), z + dz * (len + 125))) len += 125;
      if (len < run) continue;
      // Keep well inside the kind: the start's distance to its edge counts too.
      const score = len + Math.min(...[-1, 1].map((s) => { let n = 0; while (n < 1500 && ok(x - dz * s * (n + 125), z + dx * s * (n + 125))) n += 125; return n; }));
      if (!best || score > best.score) best = { x, z, tx: Math.round(x + dx * run), tz: Math.round(z + dz * run), score };
    }
  }
  if (!best) throw new Error(`${slug}: nowhere to walk ${run} units on ${kind}`);
  return { x: best.x, z: best.z, tx: best.tx, tz: best.tz };
}

async function goToRoom(link: GameLink, slug: string): Promise<GameState> {
  const r = room(slug);
  let s = await link.state();
  if (s.stage !== r.stage || s.room !== r.room) s = await link.room(r.stage, r.room);
  return settle(link, (x) => x.stage === r.stage && x.room === r.room);
}

/** Walk (or run) from (x, z) towards (tx, tz) for `frames`, and say what she stood on and the steps that played. */
async function steps(link: GameLink, x: number, z: number, tx: number, tz: number, frames: number, pace: 'walk' | 'run', name: string): Promise<{ under: Set<string>; played: number; last: string; at: GameState }> {
  await link.place(x, z, headingTo(x, z, tx, tz));
  let s = await link.frames(6);
  const before = s.sound!.steps;
  const under = new Set<string>();
  await link.down(Key.up);
  if (pace === 'run') await link.down(Key.run);
  for (let k = 0; k < frames; k += 5) {
    s = await link.frames(5);
    under.add(s.sound!.walk);
    if (k === 20) await shot(link, name);
  }
  await link.release();
  s = await link.frames(4);
  return { under, played: s.sound!.steps - before, last: s.sound!.step, at: s };
}

/** She walks a stretch of `kind` in `slug`, and the floor's own step plays. */
async function footsteps(
  link: GameLink,
  what: string,
  slug: string,
  kind: Ground,
  { pace = 'walk', run = 1500, at }: { pace?: 'walk' | 'run'; run?: number; at?: { x: number; z: number; tx: number; tz: number } } = {},
): Promise<void> {
  await goToRoom(link, slug);
  const w = at ?? walkOn(slug, kind, run);
  if (kindAt(floorsOf(slug), w.x, w.z) !== kind || kindAt(floorsOf(slug), w.tx, w.tz) !== kind) throw new Error(`${slug}: (${w.x}, ${w.z}) to (${w.tx}, ${w.tz}) is not all ${kind}`);
  const want = pace === 'run' ? STEP_SETS[kind].run : STEP_SETS[kind].walk;
  const r = await steps(link, w.x, w.z, w.tx, w.tz, pace === 'run' ? 30 : 45, pace, `${slug}-${kind}-${pace}`);
  const line = `${what}: ${pace} on ${kind} in ${roomLabel(r.at)}, from (${w.x}, ${w.z}): ${r.played} steps, the last ${r.last || '-'}, under her ${[...r.under].join('/')}`;
  check(r.played > 0 && r.last.toLowerCase() === want.toLowerCase() && [...r.under].every((u) => u.toLowerCase() === STEP_SETS[kind].walk.toLowerCase()), line, `expected ${want}`);
}

/** The music channels playing: [channel, file]. */
const channels = (s: GameState) => s.bgm!.channels.flatMap((c, i) => (c.playing && c.file ? [[i, c.file] as const] : []));

// The table as build.ts makes it: a sketch's channel plays once its render exists.
const renders = path.join(day, '..', 'music', 'renders');
const table = musicTable(CUES, plan.places, dayRooms, (sketch) => existsSync(path.join(renders, `${sketch}.wav`)));

/**
 * In `slug`, the game plays exactly the channels the music table gives the
 * room, its music and its loops, and `loops` are the loops among them. Each
 * loop's file sits 10 dB under the music (sound/ambience.ts), and its channel
 * must not lift it over.
 */
async function ambience(link: GameLink, what: string, slug: string, loops: readonly Ambience[]): Promise<void> {
  const r = table.rooms.find((x) => x.slug === slug);
  if (!r) throw new Error(`${slug} has no row in the music table`);
  const want = roomChannels(table, r);
  const isLoop = (f: string) => AMBIENCES.some((a) => ambienceFile(a).toLowerCase() === f.toLowerCase());
  const tableLoops = want.flatMap(([, f]) => (isLoop(f) ? [f] : []));
  if (JSON.stringify(tableLoops) !== JSON.stringify(loops.map(ambienceFile))) throw new Error(`${slug}: the table gives it the loops [${tableLoops.join(', ')}]`);
  await goToRoom(link, slug);
  const key = (l: readonly (readonly [number, string])[]) => JSON.stringify(l.map(([c, f]) => [c, f.toLowerCase()]));
  let s = await link.frames(30);
  for (let k = 0; k < 10 && key(channels(s)) !== key(want); k++) s = await link.frames(15);
  const vol = (c: number) => s.bgm!.channels[c]!.volume;
  const music = channels(s).filter(([, f]) => !isLoop(f)).map(([c]) => vol(c));
  const under = channels(s).every(([c, f]) => !isLoop(f) || music.every((v) => vol(c) <= v));
  const line = `${what}: ${roomLabel(s)} plays ${channels(s).map(([c, f]) => `${c}:${f} at ${vol(c)}`).join(', ') || 'nothing'} (state ${s.bgm!.state.toString(16)})`;
  check(key(channels(s)) === key(want) && under, line, `expected ${want.map(([c, f]) => `${c}:${f}`).join(', ') || 'nothing'}, its loops no louder than its music`);
}

/** Through a door that opens: stand in it, press action, and see what the door played. */
async function door(
  link: GameLink,
  what: string,
  from: string,
  to: string,
  sounds: readonly string[],
  { target = room(to), skip = false }: { target?: { stage: number; room: number }; skip?: boolean } = {},
): Promise<void> {
  await goToRoom(link, from);
  const f = floorsOf(from);
  const d = f.doors!.find((x) => x.to === to)!;
  const cx = Math.round((d.zone.x0 + d.zone.x1) / 2), cz = Math.round((d.zone.z0 + d.zone.z1) / 2);
  const [ox, oz] = outward(f, d.zone);
  const before = (await link.state()).sound!.sfx;
  await link.place(cx, cz, headingTo(cx, cz, ox, oz));
  await link.frames(6);
  await link.tap(Key.action, 2);
  const heard = new Set<string>();
  let s = await link.state();
  let set = -1;
  let files: readonly string[] = [];
  // The game keeps its last eight sounds, and a look comes every few frames, so none is missed.
  let count = before;
  let pressed = false;
  let stepsAfter = 0;
  for (let k = 0; k < 300; k++) {
    s = await link.frames(1);
    if (k === 15) await shot(link, `${from}-${to}${skip ? '-skipped' : ''}`);
    const fresh = s.sound!.sfx - count;
    if (fresh > s.sound!.recent.length) console.log(`  (${fresh} sounds since the last look, past the ${s.sound!.recent.length} the game keeps)`);
    if (fresh > 0) {
      count = s.sound!.sfx;
      for (const f of s.sound!.recent.slice(-fresh)) {
        heard.add(f);
        if (pressed && /^St_path/i.test(f)) stepsAfter++;
      }
      set = s.sound!.door;
      files = s.sound!.room;
      // Pressing run at her first step skips the walk: its first ten pictures have shown, and the gate is still open.
      if (skip && [...heard].some((f) => /^St_path/i.test(f)) && !pressed) {
        pressed = true;
        await link.tap(Key.run, 2);
      }
    }
    if (s.stage === target.stage && s.room === target.room && s.play && !(s.msf & 0x04000080)) break;
  }
  s = await settle(link);
  const arrived = s.stage === target.stage && s.room === target.room;
  const skipped = !skip || (pressed && stepsAfter <= 1);
  const line = `${what}: ${from} to ${to}${arrived ? '' : ` (still in ${roomLabel(s)})`}${skip ? `, ${stepsAfter} steps after run was pressed` : ''}, sound set ${set} [${files.join(', ')}], played ${count - before}: ${[...heard].join(', ') || 'nothing'}`;
  check(arrived && skipped && sounds.every((x) => heard.has(x)), line, `expected ${sounds.join(' and ')}${skip ? ', and the walk cut short' : ''}`);
}

// Her mode.
{
  const first = room('road');
  const session = await open(port, `--mode REB --boot rebecca:${first.stage}:${first.room}`);
  try {
    const link = session.link;
    await link.waitFor((s) => s.play, 'gameplay', 120_000);
    // Every way open and every enemy kept out: this is about the sound, not the fights.
    for (const f of EVENT_FLAGS.values()) await link.setFlag(Bank.common, f, true);
    for (const f of [...LOCK_FLAGS, 60]) await link.setFlag(Bank.locks, f, true);
    for (let f = 186; f <= 254; f++) await link.setFlag(Bank.enemies, f, true);

    await footsteps(link, 'gravel', 'road', 'gravel');
    await footsteps(link, 'gravel, running', 'road', 'gravel', { pace: 'run', run: 2500 });
    await footsteps(link, "earth, the road's verge", 'road', 'earth');
    await footsteps(link, 'boards', 'bunkhouse', 'boards');
    // The bridge's records name no doors (its own room.c has them), so no walkable floor to search: the deck's middle, along it.
    await footsteps(link, "boards, the bridge's planks over the gorge", 'bridge', 'boards', { at: { x: 10200, z: 14500, tx: 10200, tz: 18000 } });
    await footsteps(link, 'rock, the mine', 'mine-office', 'rock', { run: 1200 });
    await footsteps(link, 'water, the flooded gallery', 'gallery', 'water');
    await footsteps(link, "water, the creek's ford", 'creek', 'water', { run: 1000 });
    // Her rooms' other floors, RE1's own steps for each.
    await footsteps(link, "concrete, the workshop's slab", 'workshop', 'concrete', { run: 1000 });
    await footsteps(link, "metal, the mine lift's cage", 'mine-lift', 'metal', { run: 600 });
    await footsteps(link, "lino, the operator's booth", 'booth', 'lino', { run: 800 });
    await footsteps(link, "carpet, the gondola car", 'car', 'carpet', { run: 600 });

    // Each room plays its cue's channels and no other: one owner for each sound (docs/REBECCA_SOUND.md).
    await ambience(link, 'the station yard: its music has the wind, so no loop', 'yard', []);
    await ambience(link, 'the shed, indoors: the music alone', 'shed', []);
    await ambience(link, 'the woods: the music and the forest', 'woods', ['forest']);
    await ambience(link, "the tower top: the road's music and its wind layer, no loop", 'tower-top', []);
    await ambience(link, "the mine junction: the music, the water and the mine's air", 'junction', ['mine']);
    await ambience(link, 'the gondola car: the music and the gale', 'car', ['gale']);
    await ambience(link, 'the valley path: the music and dusk', 'valley-path', ['dusk']);
    await ambience(link, 'the hollow: the forest alone', 'den', ['forest']);
    await ambience(link, 'the estate wall: the music and the night', 'estate-wall', ['night']);
    await ambience(link, 'the cellar: the cellar alone', 'cellar', ['cellar']);
    await ambience(link, "the operator's booth, a save room: no loop", 'booth', []);

    await door(link, 'a wooden door', 'bunkhouse', 'camp-yard', ['Dr_wd01']);
    await door(link, 'an iron door', 'junction', 'tunnel', ['Dr_mtl01']);
    await door(link, 'the gate in the estate wall', 'estate-wall', 'kennels', ['Dr_gat01', 'Dr_gat02']);
    await door(link, "the road's gate, the walk skipped: it still shuts", 'road', 'washout', ['Dr_gat01', 'Dr_gat02'], { skip: true });
    await door(link, 'the ladder up to the top of the tower', 'tower-stairs', 'tower-top', ['Ladder01']);
    // Last: the hatch comes up in the mansion's save room, a room of RE1's own.
    await door(link, 'the hatch up into the save room', 'crawl', 'save', ['Ladder01'], { target: { stage: 0, room: 0 } });
  } finally {
    session.end();
  }
}

// Chris's game: RE1's own steps and no loops, in the mansion's save room and the courtyard.
{
  const session = await open(port, '--boot chris:0:0');
  try {
    const link = session.link;
    let s = await settle(link, (x) => x.stage === 0 && x.room === 0);
    const r = await steps(link, s.player.x, s.player.z, s.player.x, s.player.z + 3000, 40, 'walk', 'chris');
    check(r.played > 0 && /^ft_/i.test(r.last), `Chris in ${roomLabel(r.at)}: ${r.played} steps, the last ${r.last || '-'}, set ${r.at.sound!.set}`, "expected RE1's own step");
    s = await link.frames(30);
    check(channels(s).every(([, f]) => !/^Reb_/i.test(f)), `Chris in ${roomLabel(s)} plays ${channels(s).map(([c, f]) => `${c}:${f}`).join(', ') || 'nothing'}`, 'expected none of hers');
  } finally {
    session.end();
  }
}

if (failures.length) {
  console.error(`FAIL\n  ${failures.join('\n  ')}`);
  process.exit(1);
}
console.log('PASS');
