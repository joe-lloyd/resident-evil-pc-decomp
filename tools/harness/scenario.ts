// Rebecca's scenario played the way a player would, one function per chapter.
// Each starts where the one before ends, so the chapter tests boot into a
// chapter's first room and run its function, and full-playthrough.ts runs
// them all from a new game to the title after the ending.
//
// A chapter records what went wrong in `run.failures` and carries on where it
// can; it throws only when the run cannot go on (stuck, dead).
import path from 'node:path';
import { fight, settle, useDoor, useRoomData } from './flows.ts';
import type { GameLink } from './link.ts';
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
/** Flag `n` of FG_COMMON (bank 1): 32-bit LE words, counted from the top bit. */
export const commonFlag = (s: GameState, n: number) => {
  const b = s.banks[1];
  return ((new DataView(b.buffer, b.byteOffset, b.byteLength).getUint32((n >> 5) * 4, true) >>> (31 - (n & 31))) & 1) === 1;
};

export const ROOMS = {
  trail: { stage: 2, room: 0x12 },
  saveRoom: { stage: 0, room: 0x00 },
  leftStairs: { stage: 0, room: 0x01 },
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
