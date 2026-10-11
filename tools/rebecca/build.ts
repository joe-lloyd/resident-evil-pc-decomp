// Build Rebecca's scenario overlay (REB/) from the player's own copy of the
// game. Nothing from the game ships with this repository: the scenario is the
// script text in rooms/ plus the edits below, applied to the original files.
//
//   node tools/rebecca/build.ts <USA dir> <out dir>
//
// <USA dir> holds the original Stage1..Stage7 room files and DATA/BIO_CARD.DAT.
// RAE_CLI points at retro-archive-explorer's scripts/cli.mjs, which assembles
// the room scripts (`rae asm`).
import { execFileSync } from 'node:child_process';
import { existsSync, mkdirSync, readFileSync, readdirSync, rmSync, writeFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { buildTrailRoom, trailRoomFile } from './new_room.ts';
import { buildDayRoom } from './day/room.ts';
import { dayRooms, dayStart } from './day/rooms.ts';

/**
 * Where a new game in REB mode starts (stage counts from 0, as in the debug
 * menu): the mountain trail, near its top, facing down it.
 */
export const start = dayStart;

/**
 * Enemies that are already dead when her game starts: enemy() skips a spawn
 * whose kill flag (its third argument) is set. Chris's route is thinned for a
 * medic with a Beretta and one spare clip. In Chapter 1 the Cerberus in 11A
 * and one zombie in 10A stay as her fights.
 */
export const killedAtStart = [
  48, 49, 50, // ROOM3000 courtyard garden: all three Cerberus
  113, // ROOM10A0 back passage: one of its two zombies
  9, 10, 11, // ROOM1010 1F left stairs: all three zombies
];

/** BioCardLayout offsets (src/game/BioCard.h). */
const CARD_ENEMY_FLAGS = 0x25c;

/** Set flag `index` of a bank: word index / 32, top bit first, as cmd_bit_op does. */
function setFlag(card: Uint8Array, bankOffset: number, index: number): void {
  const at = bankOffset + (index >> 5) * 4;
  const view = new DataView(card.buffer, card.byteOffset, card.byteLength);
  view.setUint32(at, (view.getUint32(at, true) | (0x80000000 >>> (index & 31))) >>> 0, true);
}

const here = path.dirname(fileURLToPath(import.meta.url));
const roomsDir = path.join(here, 'rooms');

function findFile(dir: string, name: string): string {
  const hit = readdirSync(dir).find((f) => f.toLowerCase() === name.toLowerCase());
  if (!hit) throw new Error(`${name} not found in ${dir}`);
  return path.join(dir, hit);
}

export function build(baseDir: string, outDir: string, raeCli: string): string[] {
  const reb = path.join(outDir, 'REB');
  const written: string[] = [];

  // New game start: BIO_CARD.DAT's stage, room and camera bytes (BioCard.h,
  // 0x200), and the saved-position fields (0x22C x, 0x22E z, 0x230 angle), which
  // the port reads as the spot Rebecca stands on in the start room.
  const cardIn = findFile(findFile(baseDir, 'DATA'), 'BIO_CARD.DAT');
  const card = readFileSync(cardIn);
  card[0x200] = start.stage;
  card[0x201] = start.room;
  card[0x202] = 0;
  card.writeInt16LE(start.x, 0x22c);
  card.writeInt16LE(start.z, 0x22e);
  card.writeInt16LE(start.angle, 0x230);
  for (const index of killedAtStart) setFlag(card, CARD_ENEMY_FLAGS, index);
  mkdirSync(path.join(reb, 'DATA'), { recursive: true });
  writeFileSync(path.join(reb, 'DATA', 'BIO_CARD.DAT'), card);
  written.push('DATA/BIO_CARD.DAT');

  // New rooms: the mountain trail, built from the courtyard garden's file,
  // and the rooms of her day (day/rooms.ts).
  written.push(...buildTrailRoom(baseDir, outDir, raeCli));
  for (const room of dayRooms) written.push(...buildDayRoom(room, baseDir, outDir, raeCli));

  // Room scripts: rooms/ROOMsrrv.c replaces that room's init and main scripts.
  // The new room's script is assembled into its own file above.
  const scripts = readdirSync(roomsDir).filter((f) => /^ROOM[1-7][0-9A-F]{2}[01]\.c$/i.test(f) && f.slice(0, 8).toUpperCase() !== trailRoomFile);
  for (const file of scripts) {
    const room = file.slice(0, 8).toUpperCase();
    const stageDir = findFile(baseDir, `Stage${room[4]}`);
    const original = findFile(stageDir, `${room}.RDT`);
    const outStage = path.join(reb, `Stage${room[4]}`);
    mkdirSync(outStage, { recursive: true });
    const out = path.join(outStage, `${room}.RDT`);
    const run = (args: string[]) => execFileSync(process.execPath, [raeCli, ...args], { stdio: ['ignore', 'ignore', 'inherit'] });
    // rooms/ROOMsrrv.msg.txt, if present, replaces the room's messages
    // (`rae msg` format); it is applied after the scripts.
    const messages = path.join(roomsDir, `${room}.msg.txt`);
    if (existsSync(messages)) {
      const scripted = `${out}.scripts`;
      run(['asm', path.join(roomsDir, file), original, scripted]);
      run(['msg-set', messages, scripted, out]);
      rmSync(scripted);
    } else {
      run(['asm', path.join(roomsDir, file), original, out]);
    }
    written.push(`Stage${room[4]}/${room}.RDT`);
  }
  return written;
}

if (process.argv[1] === fileURLToPath(import.meta.url)) {
  const [baseDir, outDir] = process.argv.slice(2);
  const raeCli = process.env.RAE_CLI;
  if (!baseDir || !outDir || !raeCli || !existsSync(raeCli)) {
    console.error('usage: RAE_CLI=<retro-archive-explorer>/scripts/cli.mjs node tools/rebecca/build.ts <USA dir> <out dir>');
    process.exit(1);
  }
  for (const f of build(baseDir, outDir, raeCli)) console.log(`REB/${f}`);
}
