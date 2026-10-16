// The run a test plays: logging, pictures, failures, waiting for messages and
// going through doors. day.ts holds the stretches of Rebecca's day that use it.
//
// A chapter records what went wrong in `run.failures` and carries on where it
// can; it throws only when the run cannot go on (stuck, dead).
import path from 'node:path';
import { useDoor, useRoomData } from './flows.ts';
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
