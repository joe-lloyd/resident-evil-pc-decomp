// Build Rebecca's scenario overlay (REB/) from the player's own copy of the
// game. Nothing from the game ships with this repository: the scenario is the
// script text in rooms/ plus the edits below, applied to the original files.
//
//   node tools/rebecca/build.ts <USA dir> <out dir>
//
// <USA dir> holds the original Stage1..Stage7 room files, DATA/BIO_CARD.DAT,
// the character models in enemy/ and players/W31 to W34.EMW.
// RAE_CLI points at retro-archive-explorer's scripts/cli.mjs, which assembles
// the room scripts (`rae asm`).
import { execFileSync } from 'node:child_process';
import { existsSync, mkdirSync, readFileSync, readdirSync, rmSync, writeFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { buildDayRoom } from './day/room.ts';
import { buildCardSheet } from './card.ts';
import { footstepFiles } from './footsteps.ts';
import { ambienceFiles } from './sound/ambience.ts';
import { floorSounds, groundStepFiles, roomsFile, type RoomSounds } from './sound/ground.ts';
import { buildArms } from './arms.ts';
import { filePages } from './files/pages.ts';
import { buildWalk, walkFileName } from './walks.ts';
import { readPng } from '../harness/image.ts';
import { dayRooms, dayStart, walks } from './day/rooms.ts';
import { people, personModel } from './npc/people.ts';
import { saveRoomFiles } from './saveroom/patch.ts';
import { buildIconSheet, globalsCpp, iconRows } from './items/sheet.ts';
import { itemView, itemViewFiles, menuDataCpp, readItemModel } from './items/tmd.ts';
import { KEY_ITEMS } from './items/items.ts';
import { CUES } from './plan/music.ts';
import { day } from './plan/day.ts';
import { musicFile, musicTable, setRoomStates } from './music/table.ts';
import { mapFiles } from './maps/files.ts';

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
  // Her rooms' music (music/table.ts): each room's state starts its cue's channels, or is silent.
  const renders = path.join(here, 'music', 'renders');
  const music = musicTable(CUES, day.places, dayRooms, (sketch) => existsSync(path.join(renders, `${sketch}.wav`)));
  setRoomStates(card, music);
  mkdirSync(path.join(reb, 'DATA'), { recursive: true });
  writeFileSync(path.join(reb, 'DATA', 'BIO_CARD.DAT'), card);
  written.push('DATA/BIO_CARD.DAT');

  // Her card on the character select screen, built from the player's own sheet and faces.
  const dataDir = findFile(baseDir, 'DATA');
  const sheet = buildCardSheet(
    readFileSync(findFile(dataDir, 'Select_b.tim')),
    readFileSync(findFile(dataDir, 'Statface.tim')),
    readPng(path.join(here, 'card', 'rebecca-id-lettering.png')),
  );
  writeFileSync(path.join(reb, 'DATA', 'Select_b.tim'), sheet);
  written.push('DATA/Select_b.tim');

  // Her knife, shotgun and Magnum: her own unused files, textured from the
  // player's Jill (arms.ts), saved under the names her weapon table loads
  // (g_weaponPathTable, 0x004c1ca8: knife w11, shotgun w13, Magnum w14).
  const players = findFile(baseDir, 'players');
  const enemy = findFile(baseDir, 'enemy');
  const arms = buildArms(
    readFileSync(findFile(enemy, 'CHAR11.EMD')),
    readFileSync(findFile(enemy, 'CHAR13.EMD')),
    ['W31.EMW', 'W33.EMW', 'W34.EMW'].map((name) => ({ file: readFileSync(findFile(players, name)) })),
    [readFileSync(findFile(players, 'W32.EMW'))],
  );
  mkdirSync(path.join(reb, 'enemy'), { recursive: true });
  mkdirSync(path.join(reb, 'players'), { recursive: true });
  writeFileSync(path.join(reb, 'enemy', 'CHAR13.EMD'), arms.rebecca);
  written.push('enemy/CHAR13.EMD');
  ['W11.EMW', 'W13.EMW', 'W14.EMW'].forEach((name, i) => {
    writeFileSync(path.join(reb, 'players', name), arms.weapons[i]!);
    written.push(`players/${name}`);
  });
  // Her key items' icons over their donors', in the player's own item sheet.
  const icons = buildIconSheet(readFileSync(findFile(dataDir, 'ITEM_ALL.PIX')), readFileSync(findFile(dataDir, 'STATUS.TIM')), globalsCpp());
  writeFileSync(path.join(reb, 'DATA', 'ITEM_ALL.PIX'), icons);
  written.push('DATA/ITEM_ALL.PIX');

  // Her items' own models to examine, over their donors' in ITEM_M2.
  const viewFile = itemViewFiles(menuDataCpp(), iconRows(globalsCpp()));
  mkdirSync(path.join(reb, 'ITEM_M2'), { recursive: true });
  for (const k of KEY_ITEMS) {
    if (!('own' in k.model)) continue;
    const m = readItemModel(k.model.own);
    if (!m) throw new Error(`items/models/${k.model.own}.json is missing: run items/render-items.ts`);
    const name = viewFile(k.id);
    if (written.includes(`ITEM_M2/${name}`)) throw new Error(`${k.step}: another item's model is ${name} already`);
    writeFileSync(path.join(reb, 'ITEM_M2', name), itemView(m.mesh, m.texture));
    written.push(`ITEM_M2/${name}`);
  }

  // The walks between her outdoor rooms, and her footsteps on the path.
  mkdirSync(path.join(reb, 'objspr'), { recursive: true });
  walks.forEach((slug, n) => {
    writeFileSync(path.join(reb, 'objspr', walkFileName(n)), buildWalk(path.join(here, 'day', slug, 'renders')));
    written.push(`objspr/${walkFileName(n)}`);
  });
  mkdirSync(path.join(reb, 'sound'), { recursive: true });
  for (const { name, bytes } of footstepFiles()) {
    writeFileSync(path.join(reb, 'sound', name), bytes);
    written.push(`sound/${name}`);
  }
  // Her music table, our renders it plays, and the loops made by code
  // (sound/ambience.ts). RE1's own files, such as the save room's Bgm_31,
  // stay the player's: the table only names them.
  writeFileSync(path.join(reb, 'sound', 'music.dat'), musicFile(music));
  written.push('sound/music.dat');
  for (const ch of music.groups.flatMap((g) => g.channels)) {
    if (!ch?.render) continue;
    writeFileSync(path.join(reb, 'sound', `${ch.file}.wav`), readFileSync(path.join(renders, `${ch.render}.wav`)));
    written.push(`sound/${ch.file}.wav`);
  }
  const loops = [...new Set(music.groups.flatMap((g) => g.channels.flatMap((ch) => (ch?.loop ? [ch.loop] : []))))];
  for (const { name, bytes } of ambienceFiles(loops)) {
    writeFileSync(path.join(reb, 'sound', name), bytes);
    written.push(`sound/${name}`);
  }
  const unrendered = CUES.filter((c) => c.kind === 'new' && c.places.length).flatMap((c) =>
    c.channels.filter((ch) => !ch.loop && (!ch.sketch || !existsSync(path.join(renders, `${ch.sketch}.wav`)))).map((ch) => `${c.id} (${ch.what})`));
  if (unrendered.length) console.warn(`music: no render yet, so silent: ${unrendered.join(', ')}`);

  // The people of her day: the player's own character models with our skins (npc/people.ts).
  const enemyDir = findFile(baseDir, 'enemy');
  mkdirSync(path.join(reb, 'enemy'), { recursive: true });
  for (const person of people) {
    writeFileSync(path.join(reb, 'enemy', person.model), personModel(readFileSync(findFile(enemyDir, person.model)), person));
    written.push(`enemy/${person.model}`);
  }

  // Her files' pages (files/documents.ts), in place of RE1's in her mode
  // only. The same folder as her items' models above: one name for it, since
  // Windows doesn't tell ITEM_M2 from item_m2, and no file written twice.
  mkdirSync(path.join(reb, 'ITEM_M2'), { recursive: true });
  for (const { name, bytes } of filePages()) {
    if (written.includes(`ITEM_M2/${name}`)) throw new Error(`a file's page and an item's model are both ${name}`);
    writeFileSync(path.join(reb, 'ITEM_M2', name), bytes);
    written.push(`ITEM_M2/${name}`);
  }

  // Her map screen's pictures (maps/files.ts): her areas, the overview at
  // each stage and the grid under them, in place of RE1's in her mode only.
  for (const { name, bytes } of mapFiles()) {
    if (written.includes(`ITEM_M2/${name}`)) throw new Error(`a map and another file are both ${name}`);
    writeFileSync(path.join(reb, 'ITEM_M2', name), bytes);
    written.push(`ITEM_M2/${name}`);
  }

  // The save room's trapdoor, where she comes up from the crawl space: the
  // player's own backgrounds with it laid over them (saveroom/patch.ts).
  const stage1 = findFile(baseDir, 'Stage1');
  mkdirSync(path.join(reb, 'Stage1'), { recursive: true });
  for (const { name, bytes } of saveRoomFiles((n) => readFileSync(findFile(stage1, n)))) {
    writeFileSync(path.join(reb, 'Stage1', name), bytes);
    written.push(`Stage1/${name}`);
  }

  // New rooms: the rooms of her day (day/rooms.ts), those rendered so far.
  const roomSounds: RoomSounds[] = [];
  for (const room of dayRooms) {
    if (!existsSync(path.join(here, 'day', room.slug, 'renders', 'room.json'))) {
      console.warn(`${room.slug}: not rendered yet, left out`);
      continue;
    }
    const built = buildDayRoom(room, baseDir, outDir, raeCli);
    written.push(...built.written);
    roomSounds.push(floorSounds(room.stage, room.room, built.floors));
  }
  // Her rooms' own sounds over their slots' rows (sound/ground.ts): her steps
  // on each floor, RE1's own from the player's files or ours, shipped here.
  writeFileSync(path.join(reb, 'sound', 'rooms.dat'), roomsFile(roomSounds));
  written.push('sound/rooms.dat');
  for (const { name, bytes } of groundStepFiles()) {
    writeFileSync(path.join(reb, 'sound', name), bytes);
    written.push(`sound/${name}`);
  }

  // Room scripts: rooms/ROOMsrrv.c replaces that room's init and main scripts.
  const scripts = readdirSync(roomsDir).filter((f) => /^ROOM[1-7][0-9A-F]{2}[01]\.c$/i.test(f));
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
