// node --test tools/rebecca/music/table.test.ts
import assert from 'node:assert/strict';
import { test } from 'node:test';
import { CUES } from '../plan/music.ts';
import { day } from '../plan/day.ts';
import { dayRooms } from '../day/rooms.ts';
import { EVENTS } from '../day/events.ts';
import { cueStep, musicFile, musicSwitches, musicTable, roomChannels, setRoomStates } from './table.ts';

const withYard = (sketch: string) => sketch === 'yard';

test("every save room plays RE1's Bgm_31, and the mansion's is left to RE1's own row", () => {
  const t = musicTable(CUES, day.places, dayRooms, withYard);
  const save = t.groups.findIndex((g) => g.channels[0]?.file === 'Bgm_31');
  assert.deepEqual(t.groups[save], { cue: 'save', channels: [{ file: 'Bgm_31' }] });
  const saveRooms = t.rooms.filter((r) => r.group === save).map((r) => `${r.slug} ${r.stage}:${r.room.toString(16)}`);
  assert.deepEqual(saveRooms, ['lookout 2:14', 'office 3:12', 'booth 2:19', 'mine-office 4:1d', 'lodge 1:1d']);
  assert.equal(t.rooms.some((r) => r.place === 'save'), false);
});

test('a new cue plays its render once it exists, and only its loops before', () => {
  const station = (rendered: (s: string) => boolean) => {
    const t = musicTable(CUES, day.places, dayRooms, rendered);
    return t.rooms.filter((r) => r.cue === 'station').map((r) => roomChannels(t, r).map(([, f]) => f).join(' '));
  };
  assert.deepEqual(station(withYard), ['Reb_station', 'Reb_station Reb_amb_forest', 'Reb_station', 'Reb_station']);
  assert.deepEqual(station(() => false), ['', 'Reb_amb_forest', '', '']);
});

test('every one of her rooms has a row, so none keeps the row of the RE1 room whose slot it took', () => {
  const t = musicTable(CUES, day.places, dayRooms, withYard);
  assert.equal(t.rooms.length, dayRooms.length);
  // The mine lift is in a lab room's slot (stage 4 room 9), whose RE1 row has music.
  const lift = t.rooms.find((r) => r.slug === 'mine-lift')!;
  assert.deepEqual([lift.stage, lift.room, lift.cue, lift.state], [4, 9, 'mine', 0x20]);
  assert.deepEqual(roomChannels(t, lift), [[2, 'Reb_amb_mine']]);
  // A room whose cue has nothing to play yet is silent.
  const top = t.rooms.find((r) => r.slug === 'tower-top')!;
  assert.deepEqual([top.group, top.state], [null, 0xff]);
});

test('music.dat: the header, a group per cue with a file, and a row per room', () => {
  const t = musicTable(CUES, day.places, dayRooms, withYard);
  const bytes = musicFile(t);
  assert.equal(new TextDecoder().decode(bytes.subarray(0, 4)), 'RBM1');
  // The station, the mine, the line down, the valley, the two quiet cues, the grounds the shed and the save rooms.
  assert.deepEqual([bytes[4], bytes[5]], [9, dayRooms.length]);
  assert.equal(bytes.length, 8 + 9 * 52 + dayRooms.length * 6);
  const name = (g: number, ch: number) => new TextDecoder().decode(bytes.subarray(8 + g * 52 + ch * 16, 8 + g * 52 + ch * 16 + 16)).replace(/\0+$/, '');
  const station = t.groups.findIndex((g) => g.cue === 'station');
  assert.deepEqual([name(station, 0), name(station, 1), name(station, 2)], ['Reb_station', '', 'Reb_amb_forest']);
  assert.deepEqual([...bytes.subarray(8 + station * 52 + 48, 8 + station * 52 + 51)], [1, 0, 1]);
  const rows = bytes.subarray(8 + 9 * 52);
  const yard = t.rooms.findIndex((r) => r.slug === 'yard');
  assert.deepEqual([...rows.subarray(yard * 6, yard * 6 + 6)], [2, 0x15, t.rooms[yard]!.group, 0xff, 0xff, 0xff]);
});

test("the card: a room with music starts its channel, a silent room is 0xFF, other rooms aren't touched", () => {
  const t = musicTable(CUES, day.places, dayRooms, withYard);
  const card = new Uint8Array(1052).fill(0x40);
  setRoomStates(card, t);
  const at = (stage: number, room: number) => card[0x33c + stage * 32 + room];
  assert.equal(at(2, 0x15), 0x08); // the yard, the station's music
  assert.equal(at(2, 0x14), 0x08); // the cabin, the save room's
  assert.equal(at(2, 0x1a), 0x28); // the woods, the station's music and the forest
  assert.equal(at(2, 0x1b), 0x08); // the den, only the room: the forest
  assert.equal(at(3, 0x1e), 0xff); // the tower top, its music not rendered
  assert.equal(at(0, 0x00), 0x40); // the mansion's save room: RE1's own
});

const all = () => true;

test('a layer joins when its step happens: the generator hum in every room of the station', () => {
  const t = musicTable(CUES, day.places, dayRooms, all);
  const station = t.groups.find((g) => g.cue === 'station')!;
  assert.deepEqual(station.channels.map((c) => c?.file), ['Reb_station', 'Reb_station_1', 'Reb_amb_forest']);
  assert.deepEqual(t.rooms.filter((r) => r.cue === 'station').map((r) => r.state), [0x08, 0x28, 0x08, 0x08]);
  const gen = musicSwitches(CUES, t).steps.find((s) => s.step === 'generator-on')!;
  assert.deepEqual(gen.writes.map((w) => [w.slug, w.stage, w.room, w.state]), [
    ['yard', 2, 0x15, 0x18], ['woods', 2, 0x1a, 0x38], ['bridge', 2, 0x17, 0x18], ['platform', 2, 0x18, 0x18], ['shed', 2, 0x16, 0x38],
  ]);
  // The generator is on the road, not in the station: nothing starts where she stands.
  assert.equal(gen.now.some((n) => n.slug === 'generator'), false);
});

test('a layer only in some rooms: the mill in four of the camp, the water in the pond', () => {
  const t = musicTable(CUES, day.places, dayRooms, all);
  const state = (slug: string) => t.rooms.find((r) => r.slug === slug)!.state;
  assert.deepEqual([state('pond'), state('sawmill'), state('mess')], [0x28, 0x08, 0x08]);
  const mill = musicSwitches(CUES, t).steps.find((s) => s.step === 'mill-race')!;
  assert.deepEqual(mill.writes.map((w) => [w.slug, w.state]), [['camp-yard', 0x18], ['sawmill', 0x18], ['pond', 0x38], ['flume', 0x18]]);
  assert.deepEqual(mill.now.filter((n) => n.slug === 'pond'), [{ slug: 'pond', channel: 1, on: true }]);
});

test('a layer goes when its step happens: the pump stops the mine water', () => {
  const t = musicTable(CUES, day.places, dayRooms, all);
  const drain = musicSwitches(CUES, t).steps.find((s) => s.step === 'drain')!;
  // The mine's own loop, its air and timber, goes on.
  assert.deepEqual(drain.writes.map((w) => [w.slug, w.state]), [['tunnel', 0x28], ['junction', 0x28]]);
  assert.deepEqual(drain.now.filter((n) => n.slug === 'junction'), [{ slug: 'junction', channel: 1, on: false }]);
});

test('the chase takes over the mine as its rows\' second group, and the mine comes back after', () => {
  const t = musicTable(CUES, day.places, dayRooms, all);
  const chase = t.groups.findIndex((g) => g.cue === 'chase');
  const mine = t.groups.findIndex((g) => g.cue === 'mine');
  const tunnel = t.rooms.find((r) => r.slug === 'tunnel')!;
  assert.deepEqual([tunnel.group, tunnel.takeover, tunnel.state], [mine, chase, 0x38]);
  const rows = musicFile(t).subarray(8 + t.groups.length * 52);
  const at = t.rooms.indexOf(tunnel);
  assert.deepEqual([...rows.subarray(at * 6, at * 6 + 6)], [4, 0x1c, mine, chase, 0xff, 0xff]);
  const [over] = musicSwitches(CUES, t).takeovers;
  assert.equal(over!.cue, 'chase');
  assert.deepEqual(over!.start.map((w) => [w.slug, w.state]), [['mine-entrance', 0x09], ['tunnel', 0x09], ['junction', 0x09], ['gallery', 0x09], ['mine-lift', 0x09]]);
  assert.deepEqual(over!.ends, ['quarry', 'summit-trail']);
  assert.equal(over!.back.step, 'drain');
  assert.deepEqual(over!.back.before.map((w) => w.state), [0x08, 0x38, 0x38, 0x28, 0x28]);
  assert.deepEqual(over!.back.after.map((w) => w.state), [0x08, 0x28, 0x28, 0x28, 0x28]);
});

test('every step a channel switches at is a puzzle a room script does (day/events.ts)', () => {
  for (const c of CUES) {
    const step = cueStep(c);
    if (step) assert.ok(EVENTS.some((e) => e.step === step), `${c.id} switches at ${step}`);
  }
});

test('one owner for each sound: a room plays its music and the layers and loops its cue gives it, and no sound twice', () => {
  const t = musicTable(CUES, day.places, dayRooms, all);
  const plays = (slug: string) => roomChannels(t, t.rooms.find((r) => r.slug === slug)!).map(([n, f]) => `${n}:${f}`).join(' ');
  assert.deepEqual(
    Object.fromEntries(['ridge', 'yard', 'woods', 'shed', 'camp-yard', 'pond', 'tower-top', 'east-path', 'quarry', 'mine-entrance', 'tunnel', 'gallery', 'mine-lift', 'mast', 'car', 'valley-path', 'creek', 'lower-station', 'den', 'crash', 'estate-wall', 'garden-shed', 'cellar', 'lodge'].map((s) => [s, plays(s)])),
    {
      // The dawn's, the station's, the road's and the summit's music have the wind in them: no wind loop.
      ridge: '0:Reb_dawn',
      yard: '0:Reb_station',
      woods: '0:Reb_station 2:Reb_amb_forest',
      shed: '0:Reb_shed 2:Reb_amb_bulb',
      // The camp's three channels are its music's: the mill comes with the sluice, so it isn't a loop.
      'camp-yard': '0:Reb_camp',
      pond: '0:Reb_camp 2:Reb_camp_2',
      'tower-top': '0:Reb_road 1:Reb_road_1',
      // The quarry's wind is its music's layer, in the pit only.
      'east-path': '0:Reb_quarry',
      quarry: '0:Reb_quarry 1:Reb_quarry_1',
      'mine-entrance': '0:Reb_mine',
      // The mine's water is its music's layer, which the pump stops; the loop is the air and the timber.
      tunnel: '0:Reb_mine 1:Reb_mine_1 2:Reb_amb_mine',
      gallery: '0:Reb_mine 2:Reb_amb_mine',
      'mine-lift': '0:Reb_mine 2:Reb_amb_mine',
      mast: '0:Reb_summit 1:Reb_summit_1',
      car: '0:Reb_skyway 1:Reb_amb_gale',
      'valley-path': '0:Reb_valley 2:Reb_amb_dusk',
      creek: '0:Reb_valley 1:Reb_valley_1 2:Reb_amb_dusk',
      'lower-station': '0:Reb_valley',
      den: '0:Reb_amb_forest',
      crash: '1:Reb_amb_dusk',
      'estate-wall': '0:Reb_estate 1:Reb_amb_night',
      'garden-shed': '0:Reb_estate',
      cellar: '0:Reb_amb_cellar',
      lodge: '0:Bgm_31',
    },
  );
});
