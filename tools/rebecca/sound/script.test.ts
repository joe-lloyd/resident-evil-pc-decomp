// The sound slots her rooms' scripts call for, read from the scripts the
// build compiles (day/<slug>/room.c).
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import path from 'node:path';
import { test } from 'node:test';
import { fileURLToPath } from 'node:url';
import { scriptSounds } from './script.ts';

const day = path.join(path.dirname(fileURLToPath(import.meta.url)), '..', 'day');
const sounds = (slug: string) => Object.fromEntries([...scriptSounds(slug, readFileSync(path.join(day, slug, 'room.c'), 'utf8'))].filter(([, name]) => name));

test("the junction's spinners cry with the web spinner's sounds, not the hunter's of its room id's row", () => {
  assert.deepEqual(sounds('junction'), {
    0: 'kuasi_A', 1: 'kuasi_B', 2: 'kuasi_C', 3: 'sp_rakk', 4: 'sp_atck', 5: 'sp_bomb', 6: 'sp_fumu', 7: 'sp_Doku', 8: 'sp_sanj2',
  });
});

test('a second kind of enemy cries from the second block of ten', () => {
  assert.deepEqual(sounds('washout'), {
    0: 'PY_mena', 1: 'PY_hit2', 2: 'PY_fall',
    10: 'cer_foot', 11: 'cer_taoA', 12: 'cer_unar', 13: 'cer_bite', 14: 'cer_cryA', 15: 'cer_taoB', 16: 'cer_jkMX', 17: 'cer_kamu', 18: 'cer_cryB', 19: 'cer_runMX',
  });
});

test('a hand-written room cries too, and its people do not', () => {
  assert.deepEqual(sounds('trail'), { 0: 'RVcar1', 1: 'RVpat', 2: 'RVcar2', 3: 'RVwing1', 4: 'RVwing2', 5: 'RVfryed' });
  assert.deepEqual(sounds('lookout'), { 29: 'cancel', 30: 'type01', 31: 'type02', 32: 'item02', 33: 'item01' });
});

test('a locked door rattles and its key turns, wood or metal', () => {
  const lock = (s: Record<string, string>) => [s[20], s[34]];
  assert.deepEqual(lock(sounds('creek')), ['D_gacha', 'key_door']);
  assert.deepEqual(lock(sounds('estate-wall')), ['DM_gacha', 'key_mtr']);
  // The kennels' hoist is a lift's cage.
  assert.deepEqual(lock(sounds('kennels')), ['DM_gacha', 'key_mtr']);
  // Two iron ways and a panel door: the commoner.
  assert.deepEqual(lock(sounds('camp-yard')), ['DM_gacha', 'key_mtr']);
});

test('a save room types and opens its box', () => {
  assert.deepEqual(sounds('booth'), { 29: 'cancel', 30: 'type01', 31: 'type02', 32: 'item02', 33: 'item01' });
});

test('two kinds wanting one slot is an error, not a silent pick', () => {
  const script = 'enemy(17, 0, 1, 1, 2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0);\nenemy(3, 2, 2, 1, 2, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0);';
  assert.throws(() => scriptSounds('test', script), /slot 0 wants z_taore and kuasi_A/);
});
