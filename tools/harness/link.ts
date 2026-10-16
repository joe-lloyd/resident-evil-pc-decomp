// A connection to one game running in test mode (--test-port).
import net from 'node:net';
import { parseReply, type GameState, type Reply } from './state.ts';

/** Virtual-key codes for the default PC bindings (src/Globals.cpp g_keyBindingData). */
export const Key = {
  up: 0x26,
  down: 0x28,
  left: 0x25,
  right: 0x27,
  action: 0x43, // C: confirm, examine, fire
  run: 0x56, // V: run, cancel
  aim: 0x58, // X
  menu: 0x5a, // Z: status screen
  enter: 0x0d,
  space: 0x20,
  escape: 0x1b,
  f1: 0x70,
} as const;

export class TimeoutError extends Error {}

type Waiter = { test: (r: Reply) => boolean; resolve: (r: Reply) => void };

export class GameLink {
  private socket: net.Socket;
  private buffer = '';
  private waiters: Waiter[] = [];
  latest: GameState | undefined;
  /** Every state line received, in order, for logs and judges. */
  readonly history: GameState[] = [];
  /** Lines from the game that did not parse; a test can fail on them. */
  readonly badLines: string[] = [];

  private constructor(socket: net.Socket) {
    this.socket = socket;
    socket.setEncoding('utf8');
    socket.on('data', (chunk: string) => this.onData(chunk));
  }

  /** Connect, retrying until the game has opened its port. */
  static async connect(port: number, host = '127.0.0.1', timeoutMs = 120_000): Promise<GameLink> {
    const deadline = Date.now() + timeoutMs;
    for (;;) {
      let socket: net.Socket | undefined;
      try {
        socket = await new Promise<net.Socket>((resolve, reject) => {
          const s = net.connect({ port, host }, () => resolve(s));
          s.once('error', reject);
        });
        const link = new GameLink(socket);
        await link.ping();
        return link;
      } catch (err) {
        socket?.destroy();
        if (Date.now() > deadline) throw new TimeoutError(`no game on ${host}:${port}: ${String(err)}`);
        await new Promise((r) => setTimeout(r, 1000));
      }
    }
  }

  close(): void {
    this.socket.destroy();
  }

  /** Send a protocol line as is (see docs/TEST_MODE.md); replies arrive as usual. */
  raw(line: string): void {
    this.socket.write(`${line}\n`);
  }

  private onData(chunk: string): void {
    this.buffer += chunk;
    let nl: number;
    while ((nl = this.buffer.indexOf('\n')) >= 0) {
      const line = this.buffer.slice(0, nl);
      this.buffer = this.buffer.slice(nl + 1);
      if (!line) continue;
      let reply: Reply;
      try {
        reply = parseReply(line);
      } catch (err) {
        this.badLines.push(`${String(err)}: ${line.slice(0, 200)}`);
        continue;
      }
      if (reply.t === 'state') {
        this.latest = reply.state;
        this.history.push(reply.state);
        if (this.history.length > 20_000) this.history.splice(0, 10_000);
      }
      this.waiters = this.waiters.filter((w) => {
        if (!w.test(reply)) return true;
        w.resolve(reply);
        return false;
      });
    }
  }

  /**
   * A promise for the first reply that passes `test`. It is created before the
   * command that causes the reply is sent, so it may reject before anyone
   * awaits it; the no-op catch keeps that from being an unhandled rejection
   * (awaiting it still throws).
   */
  private next(test: (r: Reply) => boolean, timeoutMs: number, label: string): Promise<Reply> {
    const p = this.waitReply(test, timeoutMs, label);
    p.catch(() => undefined);
    return p;
  }

  private waitReply(test: (r: Reply) => boolean, timeoutMs: number, label: string): Promise<Reply> {
    return new Promise((resolve, reject) => {
      const waiter: Waiter = {
        test,
        resolve: (r) => {
          clearTimeout(timer);
          resolve(r);
        },
      };
      const timer = setTimeout(() => {
        this.waiters = this.waiters.filter((w) => w !== waiter);
        reject(new TimeoutError(`timed out after ${timeoutMs} ms waiting for ${label}`));
      }, timeoutMs);
      this.waiters.push(waiter);
    });
  }

  private async command(line: string, cmd: string): Promise<void> {
    const ack = this.next((r) => r.t === 'ack' && r.cmd === cmd, 10_000, `ack for ${line}`);
    this.socket.write(`${line}\n`);
    const reply = await ack;
    if (reply.t === 'ack' && !reply.ok) throw new Error(`game rejected: ${line}`);
  }

  async ping(): Promise<number> {
    const token = Math.random().toString(36).slice(2);
    const pong = this.next((r) => r.t === 'pong' && r.token === token, 30_000, 'pong');
    this.socket.write(`ping ${token}\n`);
    const reply = await pong;
    return reply.t === 'pong' ? reply.frame : -1;
  }

  /** Resolve with the current state if it passes, otherwise the first state that does. */
  async waitFor(test: (s: GameState) => boolean, label: string, timeoutMs = 30_000): Promise<GameState> {
    if (this.latest && test(this.latest)) return this.latest;
    const reply = await this.next((r) => r.t === 'state' && test(r.state), timeoutMs, label);
    if (reply.t !== 'state') throw new Error('unreachable');
    return reply.state;
  }

  /**
   * Wait a number of game frames (30 per second). Movies run no game frames,
   * so the wait also ends after the same span of wall-clock time.
   */
  async frames(n: number): Promise<GameState> {
    const start = await this.ping();
    const until = Date.now() + Math.ceil((n * 1000) / 30);
    for (;;) {
      const now = await this.ping();
      if (now - start >= n || Date.now() >= until) return this.state();
      await new Promise((r) => setTimeout(r, 30));
    }
  }

  /** Ask for a fresh state line, even if nothing changed. */
  async state(): Promise<GameState> {
    const fresh = this.next((r) => r.t === 'state', 5000, 'state');
    await this.command('state', 'state');
    const reply = await fresh;
    if (reply.t !== 'state') throw new Error('unreachable');
    return reply.state;
  }

  tap(vk: number, frames = 2): Promise<void> {
    return this.command(`tap ${vk} ${frames}`, 'tap');
  }

  down(vk: number): Promise<void> {
    return this.command(`down ${vk}`, 'down');
  }

  up(vk: number): Promise<void> {
    return this.command(`up ${vk}`, 'up');
  }

  release(): Promise<void> {
    return this.command('release', 'release');
  }

  /** Jump to a room like the debug menu's ROOM CHANGE. Needs gameplay to be running. */
  async room(stage: number, room: number): Promise<GameState> {
    const started = this.next((r) => r.t === 'ack' && r.cmd === 'room-start', 10_000, 'room-start');
    await this.command(`room ${stage} ${room}`, 'room');
    const reply = await started;
    if (reply.t === 'ack' && !reply.ok) throw new Error(`room ${stage} ${room} is not selectable`);
    return this.waitFor((s) => s.stage === stage && s.room === room && !(s.msf & 0x04000080), `room ${stage}:${room}`, 30_000);
  }

  /** Stand the player at (x, z) on the floor of the current room, facing `angle` when given. */
  place(x: number, z: number, angle?: number): Promise<void> {
    return this.command(`pos ${x} ${z}${angle === undefined ? '' : ` ${angle}`}`, 'pos');
  }

  /** Put an item in her first empty slot. */
  give(id: number, qty: number): Promise<void> {
    return this.command(`give ${id} ${qty}`, 'give');
  }

  setFlag(bank: number, index: number, on: boolean): Promise<void> {
    return this.command(`flag ${bank} ${index} ${on ? 1 : 0}`, 'flag');
  }

  /** Save the frame as a BMP on the game machine. */
  shot(path: string): Promise<void> {
    return this.command(`shot ${path}`, 'shot');
  }
}
