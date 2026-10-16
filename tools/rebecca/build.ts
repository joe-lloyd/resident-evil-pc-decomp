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
import { copyFileSync, existsSync, mkdirSync, readFileSync, readdirSync, writeFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { buildTrailRoom, trailRoom, trailRoomFile, trailStart } from './new_room.ts';

/**
 * Where a new game in REB mode starts (stage counts from 0, as in the debug
 * menu): the mountain trail, near its top, facing down it.
 */
export const start = { ...trailRoom, ...trailStart };

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
  mkdirSync(path.join(reb, 'DATA'), { recursive: true });
  writeFileSync(path.join(reb, 'DATA', 'BIO_CARD.DAT'), card);
  written.push('DATA/BIO_CARD.DAT');

  // New rooms: the mountain trail, built from the courtyard garden's file.
  written.push(...buildTrailRoom(baseDir, outDir, raeCli));

  // Room scripts: rooms/ROOMsrrv.c replaces that room's init and main scripts.
  // The new room's script is assembled into its own file above.
  const scripts = readdirSync(roomsDir).filter((f) => /^ROOM[1-7][0-9A-F]{2}[01]\.c$/i.test(f) && f.slice(0, 8).toUpperCase() !== trailRoomFile);
  for (const file of scripts) {
    const room = file.slice(0, 8).toUpperCase();
    const stageDir = findFile(baseDir, `Stage${room[4]}`);
    const original = findFile(stageDir, `${room}.RDT`);
    const outStage = path.join(reb, `Stage${room[4]}`);
    mkdirSync(outStage, { recursive: true });
    execFileSync(process.execPath, [raeCli, 'asm', path.join(roomsDir, file), original, path.join(outStage, `${room}.RDT`)], {
      stdio: ['ignore', 'ignore', 'inherit'],
    });
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
