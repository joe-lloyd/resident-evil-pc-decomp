// node --test tools/rebecca/music/table.test.ts
import assert from 'node:assert/strict';
import { test } from 'node:test';
import { CUES } from '../plan/music.ts';
import { day } from '../plan/day.ts';
import { dayRooms } from '../day/rooms.ts';
import { musicFile, musicTable, setRoomStates } from './table.ts';

const withYard = (sketch: string) => sketch === 'yard';

test("every save room plays RE1's Bgm_31, and the mansion's is left to RE1's own row", () => {
  const t = musicTable(CUES, day.places, dayRooms, withYard);
  const save = t.groups.findIndex((g) => g.file === 'Bgm_31');
  assert.deepEqual(t.groups[save], { cue: 'save', file: 'Bgm_31' });
  const saveRooms = t.rooms.filter((r) => r.group === save).map((r) => `${r.slug} ${r.stage}:${r.room.toString(16)}`);
  assert.deepEqual(saveRooms, ['lookout 2:14', 'office 3:12', 'booth 2:19', 'mine-office 4:1d', 'lodge 1:1d']);
  assert.equal(t.rooms.some((r) => r.place === 'save'), false);
});

test('a new cue plays its render once it exists, and its rooms are silent before', () => {
  const station = (rendered: (s: string) => boolean) => {
    const t = musicTable(CUES, day.places, dayRooms, rendered);
    return t.rooms.filter((r) => r.cue === 'station').map((r) => (r.group === null ? null : t.groups[r.group]!.file));
  };
  assert.deepEqual(station(withYard), ['Reb_station', 'Reb_station', 'Reb_station', 'Reb_station', 'Reb_station']);
  assert.deepEqual(station(() => false), [null, null, null, null, null]);
});

test('every one of her rooms has a row, so none keeps the row of the RE1 room whose slot it took', () => {
  const t = musicTable(CUES, day.places, dayRooms, withYard);
  assert.equal(t.rooms.length, dayRooms.length);
  // The mine lift is in a lab room's slot (stage 4 room 9), whose RE1 row has music.
  const lift = t.rooms.find((r) => r.slug === 'mine-lift')!;
  assert.deepEqual([lift.stage, lift.room, lift.cue, lift.group], [4, 9, 'mine', null]);
});

test('music.dat: the header, a group per cue with a file, and a row per room', () => {
  const t = musicTable(CUES, day.places, dayRooms, withYard);
  const bytes = musicFile(t);
  assert.equal(new TextDecoder().decode(bytes.subarray(0, 4)), 'RBM1');
  assert.deepEqual([bytes[4], bytes[5]], [2, dayRooms.length]);
  assert.equal(bytes.length, 8 + 2 * 52 + dayRooms.length * 6);
  const name = (g: number, ch: number) => new TextDecoder().decode(bytes.subarray(8 + g * 52 + ch * 16, 8 + g * 52 + ch * 16 + 16)).replace(/\0+$/, '');
  assert.deepEqual([name(0, 0), name(0, 1), name(1, 0)].sort(), ['', 'Bgm_31', 'Reb_station']);
  assert.deepEqual([...bytes.subarray(8 + 0 * 52 + 48, 8 + 0 * 52 + 51)], [1, 0, 0]);
  const rows = bytes.subarray(8 + 2 * 52);
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
  assert.equal(at(2, 0x1b), 0xff); // the den, only the room
  assert.equal(at(0, 0x00), 0x40); // the mansion's save room: RE1's own
});
