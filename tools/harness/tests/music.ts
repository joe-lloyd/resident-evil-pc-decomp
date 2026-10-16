// Which track each room plays. In her mode: a room of every area plays its
// cue's render, with the layers that room has; the save rooms play RE1's own
// save room music (Bgm_31, the player's own file); the ambience rooms are
// silent. The mansion's save room keeps RE1's row. Then the scripts switch
// channels as she works (plan/music.ts): opening the sluice brings the mill
// in at once and in the camp's other rooms, the generator brings the hum into
// the station, the breakers bring the line's hum in at once, the pump stops
// the mine's water at once, and her first step into the gallery switches the
// mine to the chase until she is out at the quarry. In
// Chris's game, RE1's save room still plays RE1's own track. The game
// reports each BGM channel's file and whether it plays (TestMode.cpp); the
// harness can't hear, so this is what it checks.
//
//   OVERLAY=<REB build> PORT=7801 RE1_LAB_GAME_DIR='D:\Games\RE1-decomp' node tools/harness/tests/music.ts
import { open } from '../lab.ts';
import { Key, type GameLink } from '../link.ts';
import { settle, useItem } from '../flows.ts';
import { Bank, flag, playingMusic, roomLabel, type GameState } from '../state.ts';
import { dayRooms } from '../../rebecca/day/rooms.ts';
import { EVENT_FLAGS, EVENTS, keyItem } from '../../rebecca/day/events.ts';
import { read, stand } from './floor.ts';
import { snapshot } from '../snapshot.ts';

const port = Number(process.env.PORT ?? 7801);
const shots = process.env.SHOTS ?? '/tmp/music-shots';
if (!process.env.OVERLAY) throw new Error('set OVERLAY to the REB build folder the game has');

const slot = (slug: string) => {
  const r = dayRooms.find((x) => x.slug === slug);
  if (!r) throw new Error(`no room ${slug}`);
  return [r.stage, r.room] as const;
};

/** Each room, and the files it should play: [] is silence. */
const HER_ROOMS: readonly [what: string, slug: string, files: readonly string[]][] = [
  ['the station yard', 'yard', ['Reb_station']],
  ['the tool shed, the same piece through the door', 'shed', ['Reb_station']],
  ['the cabin, a save room', 'lookout', ['Bgm_31']],
  ['the gorge footbridge, the station again', 'bridge', ['Reb_station']],
  ["the operator's booth, a save room", 'booth', ['Bgm_31']],
  ['the hollow, only the room', 'den', []],
  ['the ridge, the morning after', 'ridge', ['Reb_dawn']],
  ['the trail down, the same piece', 'trail', ['Reb_dawn']],
  ['the camp gate', 'camp-gate', ['Reb_camp']],
  ['the mill pond, with its water', 'pond', ['Reb_camp', 'Reb_camp_2']],
  ['the sawmill, the mill not running yet', 'sawmill', ['Reb_camp']],
  ["the foreman's office, a save room", 'office', ['Bgm_31']],
  ['the forestry road', 'road', ['Reb_road']],
  ['the tower top, with its wind', 'tower-top', ['Reb_road', 'Reb_road_1']],
  ['the switch house, the line not humming yet', 'switch', ['Reb_road']],
  ['the east path', 'east-path', ['Reb_quarry']],
  ['the quarry, with the wind in the pit', 'quarry', ['Reb_quarry', 'Reb_quarry_1']],
  ['the mine tunnel, still flooded', 'tunnel', ['Reb_mine', 'Reb_mine_1']],
  ['the mine office, a save room', 'mine-office', ['Bgm_31']],
  ['the mine lift, in a lab room slot RE1 gives music', 'mine-lift', ['Reb_mine']],
  ['the summit trail, in a slot RE1 gives music', 'summit-trail', ['Reb_summit']],
  ['the radio mast, with its static', 'mast', ['Reb_summit', 'Reb_summit_1']],
  ['the gondola car', 'car', ['Reb_skyway']],
  ['the valley path', 'valley-path', ['Reb_valley']],
  ['the creek, with its water', 'creek', ['Reb_valley', 'Reb_valley_1']],
  ['the crash, only the room', 'crash', []],
  ["the gardener's lodge, a save room", 'lodge', ['Bgm_31']],
  ['the estate wall', 'estate-wall', ['Reb_estate']],
  ['the cellar, under the house', 'cellar', []],
];

const failures: string[] = [];
const same = (a: readonly string[], b: readonly string[]) => a.length === b.length && a.every((f, i) => f.toLowerCase() === b[i]!.toLowerCase());
const describe = (s: GameState) => s.bgm!.channels.map((c) => `${c.file || '-'}${c.playing ? ' playing' : ''}${c.file ? ` at ${c.volume}` : ''}`).join(', ');

/** Wait for the room's music to settle on `files`; silence must hold for two seconds. */
async function expectMusic(link: GameLink, what: string, files: readonly string[]): Promise<GameState> {
  let s = await link.state();
  const deadline = Date.now() + 15_000;
  let heard = 0;
  while (Date.now() < deadline) {
    s = await link.frames(10);
    heard = same(playingMusic(s), files) ? heard + 1 : 0;
    if (heard >= (files.length ? 2 : 6)) break;
  }
  const ok = heard > 0 && same(playingMusic(s), files);
  const muted = s.bgm!.channels.some((c) => c.playing && c.volume <= -9999);
  console.log(`${ok && !muted ? 'ok  ' : 'FAIL'} ${roomLabel(s)} ${what}: state ${s.bgm!.state.toString(16)}, ${describe(s)}`);
  if (!ok) failures.push(`${what} (${roomLabel(s)}) plays [${playingMusic(s).join(', ')}], not [${files.join(', ')}]`);
  if (muted) failures.push(`${what} (${roomLabel(s)}) plays at -9999, which is silent`);
  return s;
}

async function go(link: GameLink, slug: string): Promise<void> {
  const [st, rm] = slot(slug);
  const s = await link.state();
  if (s.stage === st && s.room === rm) return;
  await link.room(st, rm);
  await settle(link, (x) => x.stage === st && x.room === rm);
}

/** Do a step of day/events.ts in its room as she would: stand at its spot, then use its item or press action. */
async function work(link: GameLink, step: string): Promise<void> {
  const e = EVENTS.find((x) => x.step === step)!;
  await go(link, e.room);
  const zone = read(e.room)!.spots!.find((sp) => sp.step === step)!.zone;
  await stand(link, e.room, zone);
  if (e.use) {
    const id = keyItem(e.use).id;
    if (!(await link.state()).items.some((it) => it.id === id)) await link.give(id, 1);
    await useItem(link, id);
    // The script waits a second after the status screen closes before it acts.
    await link.frames(90);
  } else {
    await link.tap(Key.action, 3);
    await link.frames(30);
  }
  const [st, rm] = slot(e.room);
  await settle(link, (x) => x.stage === st && x.room === rm);
  if (!flag(await link.state(), Bank.common, EVENT_FLAGS.get(step)!)) failures.push(`${step} did not happen`);
}

// Her mode.
{
  const [stage, room] = slot(HER_ROOMS[0]![1]);
  const session = await open(port, `--mode REB --boot rebecca:${stage}:${room}`);
  try {
    const link = session.link;
    await settle(link, (s) => s.stage === stage && s.room === room);
    for (const step of ['mill-race', 'generator-on', 'line-on', 'drain']) await link.setFlag(Bank.common, EVENT_FLAGS.get(step)!, false);
    // This tests her music, not her fights: the pond's zombie would grab her
    // at the sluice. Every enemy of her day has a kill flag in 186-254 of
    // bank 3 (day/foes.ts), and a set one keeps it out of its room.
    for (let f = 186; f <= 254; f++) await link.setFlag(3, f, true);
    for (const [what, slug, files] of HER_ROOMS) {
      await go(link, slug);
      await expectMusic(link, what, files);
    }
    await link.room(0, 0);
    await settle(link, (x) => x.stage === 0 && x.room === 0);
    await expectMusic(link, "the mansion's save room, on RE1's own row", ['Bgm_31']);

    // The sluice: the mill joins at once in the pond, and plays in the sawmill after.
    await go(link, 'pond');
    await expectMusic(link, 'the pond before the sluice', ['Reb_camp', 'Reb_camp_2']);
    await work(link, 'mill-race');
    await expectMusic(link, 'the pond, the sluice open: the mill joins', ['Reb_camp', 'Reb_camp_1', 'Reb_camp_2']);
    console.log(`     ${await snapshot(link, shots, 'music-pond-sluice')}`);
    await go(link, 'sawmill');
    await expectMusic(link, 'the sawmill, the mill running', ['Reb_camp', 'Reb_camp_1']);
    await go(link, 'mess');
    await expectMusic(link, 'the mess, out of earshot of the mill', ['Reb_camp']);

    // The generator: the hum joins the station the next time she is there.
    await work(link, 'generator-on');
    await expectMusic(link, 'the generator hut, running', ['Reb_road']);
    await go(link, 'yard');
    await expectMusic(link, 'the station yard, the power on: the hum joins', ['Reb_station', 'Reb_station_1']);
    await go(link, 'shed');
    await expectMusic(link, 'the tool shed, the hum through the door', ['Reb_station', 'Reb_station_1']);

    // The breakers: the line hums at once in the switch house, and on the line track.
    await work(link, 'line-on');
    await expectMusic(link, 'the switch house, the breakers up: the line hums', ['Reb_road', 'Reb_road_2']);
    console.log(`     ${await snapshot(link, shots, 'music-switch-line')}`);
    await go(link, 'line-track');
    await expectMusic(link, 'the line track, humming', ['Reb_road', 'Reb_road_2']);
    await go(link, 'road');
    await expectMusic(link, 'the forestry road, out of earshot of the line', ['Reb_road']);

    // The pump: the mine's water stops at once in the junction, and in the tunnel.
    await go(link, 'junction');
    await expectMusic(link, 'the junction, flooded', ['Reb_mine', 'Reb_mine_1']);
    await work(link, 'drain');
    await expectMusic(link, 'the junction, the pump running: the water stops', ['Reb_mine']);
    console.log(`     ${await snapshot(link, shots, 'music-junction-drain')}`);
    await go(link, 'tunnel');
    await expectMusic(link, 'the tunnel, drained', ['Reb_mine']);

    // The mine: her first step into the gallery switches its rooms to the chase.
    await go(link, 'gallery');
    await expectMusic(link, 'the gallery, the floor giving way: the chase', ['Reb_chase']);
    console.log(`     ${await snapshot(link, shots, 'music-gallery-chase')}`);
    await go(link, 'junction');
    await expectMusic(link, 'the junction, still chased', ['Reb_chase']);
    await go(link, 'tunnel');
    await expectMusic(link, 'the tunnel, still chased', ['Reb_chase']);
    await go(link, 'quarry');
    await expectMusic(link, 'the quarry, out of the mine', ['Reb_quarry', 'Reb_quarry_1']);
    await go(link, 'tunnel');
    await expectMusic(link, 'the tunnel again: the mine, drained, not the chase', ['Reb_mine']);

    // RE1's tracks loop; so does ours. The station's file is 96 s: in the yard
    // past its end, it must still be playing.
    await go(link, 'yard');
    await expectMusic(link, 'the station yard again', ['Reb_station', 'Reb_station_1']);
    const until = Date.now() + 100_000;
    while (Date.now() < until) await link.frames(150);
    await expectMusic(link, 'the station yard, 100 s on: the loop', ['Reb_station', 'Reb_station_1']);
  } finally {
    session.end();
  }
}

// Chris's game, on RE1's own table: the first time in RE1's save room his
// meeting with Rebecca plays Bgm_13; back in the room afterwards, the save
// room music, Bgm_31.
{
  const session = await open(port, '--boot chris:0:0');
  try {
    const link = session.link;
    await settle(link, (s) => s.stage === 0 && s.room === 0);
    await expectMusic(link, "Chris meets Rebecca in RE1's save room", ['Bgm_13']);
    await link.room(0, 3);
    await settle(link, (s) => s.stage === 0 && s.room === 3);
    await link.room(0, 0);
    await settle(link, (s) => s.stage === 0 && s.room === 0);
    await expectMusic(link, "Chris back in RE1's save room", ['Bgm_31']);
  } finally {
    session.end();
  }
}

if (failures.length) {
  console.error(`FAIL\n  ${failures.join('\n  ')}`);
  process.exit(1);
}
console.log('PASS');
