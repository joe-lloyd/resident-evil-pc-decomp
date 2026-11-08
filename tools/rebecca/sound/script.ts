// The room sound slots a room's script calls for, besides her footsteps
// (ground.ts). RE1 loads 48 per room by its id (src/game/SoundTables.cpp);
// her rooms sit in free ids whose rows hold some other room's sounds or
// none, so the build gives every slot of hers a sound or an empty name.
//
// What plays a slot in her rooms:
// - an enemy's cries: slot block * 10 + n (Snd_em), its block the last
//   operand of its enemy() line. Each kind's WAVs are RE1's own (day/foes.ts).
// - a locked door: the rattle when she has no key (slot 20) and the key
//   turning (34), door_try_enter. RE1's rooms use D_gacha and key_door for
//   wooden doors, DM_gacha and key_mtr for metal ones. A room has one of
//   each, so a room with both kinds takes the commoner, metal on a tie.
// - a typewriter: the save screen's cancel and keys (29, 30, 31).
// - an item box: its lid opening (32) and the screen closing (33).
import { FOE_KINDS } from '../day/foes.ts';

/** Door animations (door_aot_set's type) that are metal, by RE1's door files: iron and steel doors, a lift, and a gate on a walk. */
const METAL_DOORS = new Set([8, 10, 11, 12, 20, 48]);
const WOODEN_DOORS = new Set([0, 7, 33]);
/** Entity ids from 32 are people, not enemies: they never cry. */
const FIRST_NPC = 32;
const BLOCK = 10;

/** A script line's operands, comments dropped. */
const operands = (args: string) => args.replace(/\/\*.*?\*\//g, '').split(',').map((a) => a.trim());

export function scriptSounds(slug: string, script: string): Map<number, string> {
  const slots = new Map<number, string>();
  const put = (slot: number, name: string) => {
    const had = slots.get(slot);
    if (had !== undefined && had !== name) throw new Error(`${slug}: slot ${slot} wants ${had} and ${name}`);
    slots.set(slot, name);
  };

  for (const [, args] of script.matchAll(/\benemy\(([^;]*)\);/g)) {
    const ops = operands(args!);
    const id = Number(ops[0]);
    if (id >= FIRST_NPC) continue;
    const kind = Object.values(FOE_KINDS).find((k) => k.id === id);
    if (!kind) throw new Error(`${slug}: enemy ${id} has no cries in day/foes.ts`);
    const block = Number(ops.at(-1));
    const sounds: readonly string[] = kind.sounds;
    for (let n = 0; n < BLOCK; n++) put(block * BLOCK + n, sounds[n] ?? '');
  }

  const locks = [...script.matchAll(/\bdoor_aot_set\(([^;]*)\);/g)].map(([, args]) => operands(args!)).filter((ops) => ops[15] !== 'UNLOCKED');
  if (locks.length) {
    const types = locks.map((ops) => Number(ops[7]));
    const odd = types.filter((t) => !METAL_DOORS.has(t) && !WOODEN_DOORS.has(t));
    if (odd.length) throw new Error(`${slug}: a locked door of type ${odd[0]}, neither metal nor wooden`);
    const metal = types.filter((t) => METAL_DOORS.has(t)).length * 2 >= types.length;
    put(20, metal ? 'DM_gacha' : 'D_gacha');
    put(34, metal ? 'key_mtr' : 'key_door');
  }
  if (script.includes('SCE_TYPEWRITER')) {
    put(29, 'cancel');
    put(30, 'type01');
    put(31, 'type02');
  }
  if (script.includes('SCE_ITEMBOX')) {
    put(32, 'item02');
    put(33, 'item01');
  }
  return slots;
}
