// Rebecca's scenario played the way a player would, one function per chapter.
// Each starts where the one before ends, so the chapter tests boot into a
// chapter's first room and run its function, and full-playthrough.ts runs
// them all from a new game to the title after the ending.
//
// A chapter records what went wrong in `run.failures` and carries on where it
// can; it throws only when the run cannot go on (stuck, dead).
import path from 'node:path';
import { approach, check, fight, goTo, faceTowards, settle, useDoor, useFightBack, useRoomData } from './flows.ts';
import { Key, type GameLink } from './link.ts';
import { roomLabel, type GameState } from './state.ts';
import { snapshot } from './snapshot.ts';

type Zone = { x: number; z: number; w: number; d: number };
type Room = { stage: number; room: number };

export class Run {
  readonly failures: string[] = [];
  readonly link: GameLink;
  readonly out: string;
  readonly dataDirs: string[];
  private readonly started = Date.now();

  constructor(link: GameLink, overlay: string, out = process.env.OUT ?? '/tmp/rae-tests') {
    this.link = link;
    this.out = out;
    this.dataDirs = [path.join(overlay, 'REB'), process.env.RE1_DATA ?? '/tmp/re1-pc'];
    useRoomData(this.dataDirs);
  }

  log(s: GameState, what: string): void {
    console.log(`[${Math.round((Date.now() - this.started) / 1000)}s] ${roomLabel(s)} hp ${s.player.hp}/${s.player.maxHp} ${what}`);
  }

  fail(what: string): void {
    console.log(`  FAILED: ${what}`);
    this.failures.push(what);
  }

  async picture(name: string): Promise<void> {
    console.log(`picture: ${await snapshot(this.link, this.out, name)}`);
  }

  /** Start waiting for a message now; returns whether it showed by `timeoutMs`. */
  expectMessage(id: number, label: string, timeoutMs = 90_000): () => Promise<GameState | undefined> {
    const p = this.link.waitFor((s) => s.messageId === id, label, timeoutMs);
    p.catch(() => undefined);
    return () => p.catch(() => undefined);
  }

  /** Go through a door and check the room it leads to. */
  async door(zone: Zone, to?: Room, label?: string): Promise<GameState> {
    const s = await useDoor(this.link, zone);
    this.log(s, label ?? 'through the door');
    if (to && !inRoom(s, to)) this.fail(`expected ${roomLabel(to)}, got ${roomLabel(s)}`);
    return s;
  }

  /** Report and exit. */
  finish(): void {
    if (this.failures.length) {
      console.error(`FAIL\n  ${this.failures.join('\n  ')}`);
      process.exitCode = 1;
    } else {
      console.log('PASS');
    }
  }

  /** On an exception: where she was, and a picture. */
  async crashed(): Promise<void> {
    const s = await this.link.state();
    console.log(`failed at ${roomLabel(s)} (${s.player.x}, ${s.player.z}) angle ${s.player.angle}; picture: ${await snapshot(this.link, this.out, 'failed')}`);
  }
}

export const inRoom = (s: Pick<GameState, 'stage' | 'room'>, r: Room) => s.stage === r.stage && s.room === r.room;
const has = (s: GameState, id: number) => s.items.some((it) => it.id === id);
/** Flag `n` of FG_COMMON (bank 1): 32-bit LE words, counted from the top bit. */
export const commonFlag = (s: GameState, n: number) => {
  const b = s.banks[1];
  return ((new DataView(b.buffer, b.byteOffset, b.byteLength).getUint32((n >> 5) * 4, true) >>> (31 - (n & 31))) & 1) === 1;
};

export const ROOMS = {
  trail: { stage: 2, room: 0x12 },
  saveRoom: { stage: 0, room: 0x00 },
  leftStairs: { stage: 0, room: 0x01 },
  richard: { stage: 1, room: 0x01 },
  bar: { stage: 0, room: 0x0f },
  guardhouse: { stage: 3, room: 0x08 },
  storehouse: { stage: 3, room: 0x09 },
  plant42: { stage: 3, room: 0x0c },
  powerRoom: { stage: 4, room: 0x11 },
  wesker: { stage: 4, room: 0x14 },
  huntersStairs: { stage: 5, room: 0x01 },
  heliport: { stage: 2, room: 0x03 },
} as const;

// ---------------------------------------------------------------------------
// Prologue and Chapter 1: down the trail, in the back way, the meeting.
// ---------------------------------------------------------------------------

const MEETING = 0x80 + 46;
const chapter1Route: { name: string; at: Room; fight: boolean; door: Zone }[] = [
  { name: 'mountain trail', at: ROOMS.trail, fight: false, door: { x: 1500, z: 15200, w: 4000, d: 2000 } },
  { name: 'courtyard garden', at: { stage: 2, room: 0x00 }, fight: false, door: { x: 22300, z: 3200, w: 4700, d: 4100 } },
  { name: 'storeroom', at: { stage: 0, room: 0x1b }, fight: false, door: { x: 0, z: 5200, w: 2600, d: 2400 } },
  { name: 'roofed passage', at: { stage: 0, room: 0x1a }, fight: true, door: { x: 4700, z: 2700, w: 1800, d: 2300 } },
  { name: 'back passage', at: { stage: 0, room: 0x0a }, fight: true, door: { x: 10600, z: 5200, w: 2000, d: 1700 } },
  { name: '1F left stairs', at: ROOMS.leftStairs, fight: false, door: { x: 7600, z: 7700, w: 2400, d: 1500 } },
];

/** From the top of the mountain trail to the meeting with Chris in the save room. */
export async function chapter1(run: Run): Promise<void> {
  const { link } = run;
  for (const [i, step] of chapter1Route.entries()) {
    const here = await settle(link, (s) => inRoom(s, step.at));
    run.log(here, `in the ${step.name}`);
    await run.picture(`ch1-${String(i).padStart(2, '0')}-${step.name.replace(/\W+/g, '-')}`);
    if (step.fight) {
      const shots = await fight(link);
      run.log(await link.state(), `cleared the ${step.name} with ${shots} shots`);
    }
    const last = i === chapter1Route.length - 1;
    const meeting = last ? run.expectMessage(MEETING, 'the meeting', 120_000) : undefined;
    await run.door(step.door);
    if (meeting) {
      if (await meeting()) await run.picture('ch1-99-meeting');
      else run.fail('the meeting with Chris never played');
    }
  }
  run.log(await settle(link, (s) => inRoom(s, ROOMS.saveRoom)), 'chapter 1 complete');
}

// ---------------------------------------------------------------------------
// Chapter 2: Richard, poisoned at the top of the 1F left stairs, and the serum.
// ---------------------------------------------------------------------------

const SERUM = 66;
const RICHARD_FOUND = 0x80 + 4;
const RICHARD_TREATED = 0x80 + 5;
const RICHARD_DEAD = 0x80 + 6;
const SHELF_SPOT = { x: 6300, z: 7600 };
const toRichard: { at: Room; door: Zone }[] = [
  { at: ROOMS.saveRoom, door: { x: 2700, z: 500, w: 1700, d: 1800 } },
  { at: ROOMS.leftStairs, door: { x: 4700, z: 2500, w: 2605, d: 1300 } },
];
const toSaveRoom: { at: Room; door: Zone }[] = [
  { at: ROOMS.richard, door: { x: 11345, z: 10300, w: 2605, d: 2500 } },
  { at: ROOMS.leftStairs, door: { x: 7600, z: 7700, w: 2400, d: 1500 } },
];
const RICHARD_EXIT = { x: 14700, z: 25700, w: 1500, d: 1900 };

async function walk(run: Run, legs: { at: Room; door: Zone }[]): Promise<GameState> {
  let s = await run.link.state();
  for (const leg of legs) {
    await settle(run.link, (st) => inRoom(st, leg.at));
    await fight(run.link);
    s = await run.door(leg.door);
  }
  // No settle here: a scene that opens on arrival stays on screen for its picture.
  return s;
}

async function takeSerum(run: Run): Promise<void> {
  const { link } = run;
  await settle(link, (s) => inRoom(s, ROOMS.saveRoom));
  await goTo(link, run.dataDirs, SHELF_SPOT.x, SHELF_SPOT.z, { radius: 300 });
  await faceTowards(link, SHELF_SPOT.x, 9000);
  for (let i = 0; i < 4; i++) {
    await link.tap(Key.action, 3);
    await link.frames(20);
    const s = await settle(link);
    if (has(s, SERUM)) {
      run.log(s, 'took the serum');
      return;
    }
  }
  run.fail('could not take the serum from the shelf');
}

/**
 * From the save room after the meeting: find Richard, fetch the serum, treat
 * him, and leave by the corridor's far door for the bar. `serumFirst` takes
 * the serum before going up; `late` waits out his three minutes.
 */
export async function chapter2(run: Run, { serumFirst = false, late = false } = {}): Promise<void> {
  const { link } = run;
  run.log(await settle(link, (s) => inRoom(s, ROOMS.saveRoom)), 'in the save room after the meeting');
  if (serumFirst) await takeSerum(run);
  const found = run.expectMessage(RICHARD_FOUND, 'Richard found', 300_000);
  await walk(run, toRichard);
  if (await found()) await run.picture('ch2-00-richard');
  else run.fail('the scene with Richard never played');
  await settle(link);
  if (!serumFirst) {
    await walk(run, toSaveRoom);
    await takeSerum(run);
    if (late) {
      const until = Date.now() + 200_000;
      while (Date.now() < until) await link.frames(30);
      run.log(await link.state(), 'waited out the clock');
    }
    await walk(run, toRichard);
  }
  const end = await link.waitFor((s) => s.messageId === RICHARD_TREATED || s.messageId === RICHARD_DEAD, 'Richard treated', 30_000).catch(() => undefined);
  await run.picture('ch2-99-richard-after');
  const s = await settle(link);
  if (!end) run.fail('neither the treatment nor his death played');
  else if (late && end.messageId !== RICHARD_DEAD) run.fail('Richard was treated after the clock ran out');
  else if (!late && end.messageId === RICHARD_DEAD) run.fail('Richard died before the serum arrived');
  if (!commonFlag(s, 201)) run.fail('FG_COMMON 201 (his fate is settled) is not set');
  if (commonFlag(s, 202) === late) run.fail(`FG_COMMON 202 (Richard saved) is ${late ? 'set' : 'not set'}`);
  if (has(s, SERUM) !== late) run.fail(late ? 'the serum was used on a dead man' : 'the serum is still in her bag');
  run.log(s, `Richard ${commonFlag(s, 202) ? 'saved' : 'lost'}`);
  await run.door(RICHARD_EXIT, ROOMS.bar, 'on to the bar');
}

// ---------------------------------------------------------------------------
// Chapter 3: Moonlight, in the bar.
// ---------------------------------------------------------------------------

const GOLD_EMBLEM = 32;
const BAR_TITLE = 0x80 + 29;
const PIANO_PLAYED = 0x80 + 31;
const MUSIC_NOTES = 35;
const SHEET = { x: 16900, z: 10000, w: 1000, d: 2500 };
const PIANO = { x: 10200, z: 7300, w: 600, d: 1500 };
const BAR_EXIT = { x: 13700, z: 960, w: 1700, d: 1900 };

/** Take the Music Notes, play the piano, take the Gold Emblem, go on to the guardhouse. */
export async function chapter3(run: Run, title = run.expectMessage(BAR_TITLE, 'chapter 3 title')): Promise<void> {
  const { link } = run;
  let s = await settle(link, (st) => inRoom(st, ROOMS.bar));
  if (!(await title())) run.fail('the chapter 3 title never showed');
  run.log(s, 'in the bar');
  s = await check(link, SHEET);
  for (let i = 0; i < 2 && !has(s, MUSIC_NOTES); i++) s = await check(link, SHEET);
  if (has(s, MUSIC_NOTES)) run.log(s, 'took the Music Notes');
  else run.fail('could not take the Music Notes');
  const played = run.expectMessage(PIANO_PLAYED, 'the piano', 60_000);
  s = await check(link, PIANO);
  if (await played()) {
    run.log(s, 'played the piano');
    await run.picture('ch3-00-piano');
  } else run.fail('playing the piano never happened');
  for (let i = 0; i < 3 && !has(s, GOLD_EMBLEM); i++) s = await check(link, PIANO);
  if (has(s, GOLD_EMBLEM)) run.log(s, 'took the Gold Emblem');
  else run.fail('the Gold Emblem was not on the piano');
  if (has(s, MUSIC_NOTES)) run.fail('the Music Notes are still in her bag');
  await run.door(BAR_EXIT, ROOMS.guardhouse, 'on to the guardhouse');
}

// ---------------------------------------------------------------------------
// Chapter 4: the guardhouse.
// ---------------------------------------------------------------------------

const VJOLT = 27;
const HELMET_KEY = 54;
const GUARDHOUSE_TITLE = 0x80 + 16;
const ROOTS_POURED = 0x80 + 18;
const STOREHOUSE_DOOR = { x: 5500, z: 9400, w: 3000, d: 1800 };
const MIXING_TABLE = { x: 5100, z: 6000, w: 4400, d: 1100 };
const STOREHOUSE_EXIT = { x: 9600, z: 2300, w: 1800, d: 1700 };
const ROOTS = { x: 24200, z: 2400, w: 2600, d: 3400 };
const PLANT_DOOR = { x: 27800, z: 2100, w: 3000, d: 4000 };
const HELMET = { x: 9800, z: 17700, w: 2200, d: 1800 };
const PLANT_EXIT = { x: 1100, z: 8000, w: 1500, d: 3900 };

/** Mix V-JOLT, kill Plant 42 at its roots, take the Helmet Key, go on to the lab. */
export async function chapter4(run: Run, title = run.expectMessage(GUARDHOUSE_TITLE, 'chapter 4 title')): Promise<void> {
  const { link } = run;
  // Nothing in this chapter fights back, and the dead Plant 42 is still an
  // entity with 140 HP and the same status as a live one: walking must not
  // turn to shoot it.
  useFightBack(0);
  let s = await settle(link, (st) => inRoom(st, ROOMS.guardhouse));
  if (!(await title())) run.fail('the chapter 4 title never showed');
  run.log(s, 'in the guardhouse passage');
  await run.door(STOREHOUSE_DOOR, ROOMS.storehouse, 'in the drug storehouse');
  s = await check(link, MIXING_TABLE);
  for (let i = 0; i < 3 && !has(s, VJOLT); i++) s = await check(link, MIXING_TABLE);
  if (has(s, VJOLT)) run.log(s, 'mixed and took the V-JOLT');
  else run.fail('no V-JOLT from the mixing table');
  await run.picture('ch4-00-storehouse');
  await run.door(STOREHOUSE_EXIT, ROOMS.guardhouse);
  const poured = run.expectMessage(ROOTS_POURED, 'the roots', 60_000);
  s = await check(link, ROOTS);
  if (await poured()) run.log(s, 'poured the V-JOLT on the roots');
  else run.fail(`the roots never took the V-JOLT (last message ${s.messageId})`);
  s = await run.door(PLANT_DOOR, ROOMS.plant42, "in Plant 42's room");
  await run.picture('ch4-01-plant42');
  for (let i = 0; i < 3 && !has(s, HELMET_KEY); i++) s = await check(link, HELMET);
  if (has(s, HELMET_KEY)) run.log(s, 'took the Helmet Key');
  else run.fail('could not take the Helmet Key');
  await run.door(PLANT_EXIT, ROOMS.powerRoom, 'on to the lab');
}

// ---------------------------------------------------------------------------
// Chapter 5: underground.
// ---------------------------------------------------------------------------

const LAB_TITLE = 0x80 + 8;
const POWER_ON = 0x80 + 6;
const WESKER = 0x80 + 22;
const POWER_SWITCH = { x: 17700, z: 8300, w: 2100, d: 1600 };
const POWER_DOOR = { x: 11300, z: 15800, w: 3000, d: 2900 };
const WESKER_EXIT = { x: 13500, z: 8500, w: 1800, d: 2900 };

/** Turn on the elevator power, face Wesker, run for the house. */
export async function chapter5(run: Run, title = run.expectMessage(LAB_TITLE, 'chapter 5 title')): Promise<void> {
  const { link } = run;
  let s = await settle(link, (st) => inRoom(st, ROOMS.powerRoom));
  if (!(await title())) run.fail('the chapter 5 title never showed');
  run.log(s, 'in the power room');
  const power = run.expectMessage(POWER_ON, 'the power switch', 60_000);
  s = await check(link, POWER_SWITCH);
  if (await power()) run.log(s, 'turned the power on');
  else run.fail(`the power switch never answered (last message ${s.messageId})`);
  const wesker = run.expectMessage(WESKER, 'Wesker', 60_000);
  await run.door(POWER_DOOR, ROOMS.wesker);
  if (await wesker()) await run.picture('ch5-00-wesker');
  else run.fail('the confrontation with Wesker never played');
  await settle(link);
  await run.door(WESKER_EXIT, ROOMS.huntersStairs, 'back in the house');
}

// ---------------------------------------------------------------------------
// Chapter 6 and the epilogue: the Hunter, the heliport, the ending.
// ---------------------------------------------------------------------------

const HUNTERS_TITLE = 0x80 + 12;
const EPILOGUE = 0x80 + 7;
const STAIRS_UP = { x: 4700, z: 2500, w: 2605, d: 1300 };
const DEATH_VARIANT = 0x80000000;

/**
 * Get past the Hunter to the stairs (`fightHunter` fights it first), meet
 * Chris on the heliport, and see the game end: MSF2_DEATH_VARIANT, no death
 * screen, the end screens, and back to the title.
 */
export async function chapter6(run: Run, { fightHunter = false } = {}, title = run.expectMessage(HUNTERS_TITLE, 'chapter 6 title')): Promise<void> {
  const { link } = run;
  // She runs from the Hunter; walking must not turn to fight it.
  useFightBack(0);
  let s = await settle(link, (st) => inRoom(st, ROOMS.huntersStairs));
  if (!(await title())) run.fail('the chapter 6 title never showed');
  run.log(s, `on the stairs, enemies ${JSON.stringify(s.enemies.map((e) => [e.type, e.hp]))}`);
  if (fightHunter) run.log(await link.state(), `cleared the stairs with ${await fight(link)} shots`);

  // The stairs by hand: the game ends a few pages into the heliport scene, so
  // nothing here may wait for control in that room.
  const epilogue = run.expectMessage(EPILOGUE, 'the epilogue', 120_000);
  await approach(link, STAIRS_UP);
  for (let i = 0; i < 40 && !inRoom(await link.state(), ROOMS.heliport); i++) {
    await link.tap(Key.action, 3);
    await link.frames(20);
  }
  s = await link.state();
  run.log(s, 'up the stairs');
  if (!inRoom(s, ROOMS.heliport)) run.fail(`expected the heliport, got ${roomLabel(s)}`);
  if (await epilogue()) {
    await link.frames(30);
    await run.picture('ch6-00-heliport');
  } else run.fail('the epilogue never played');

  // Page through the scene; when it closes the script ends the game.
  let ended: GameState | undefined;
  for (let i = 0; i < 60 && !ended; i++) {
    await link.tap(Key.action, 3);
    const st = await link.frames(20);
    if ((st.msf2 & DEATH_VARIANT) !== 0) ended = st;
  }
  if (!ended) {
    run.fail('the game never set the ending (MSF2_DEATH_VARIANT)');
    return;
  }
  run.log(ended, 'the ending begins');
  const endScreens = await link.waitFor((st) => !st.play && st.title === 0 && (st.msf2 & DEATH_VARIANT) === 0, 'the end screens', 600_000).catch(() => undefined);
  await link.frames(60);
  await run.picture('ch6-99-after-ending');
  if (!endScreens) run.fail('the ending never finished');
  // The game offers to save the clear: DO NOT SAVE, the last line, goes to the title.
  for (let i = 0; i < 12 && (await link.state()).title === 0; i++) {
    await link.tap(Key.up, 2);
    await link.frames(10);
    await link.tap(Key.action, 3);
    await link.frames(60);
  }
  const back = await link.state();
  if (back.title !== 0) run.log(back, 'back at the title after the ending');
  else run.fail('the ending never returned to the title');
}
