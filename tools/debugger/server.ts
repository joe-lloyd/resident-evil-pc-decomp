// The debug dashboard's server: one test-mode connection to the game
// (tools/harness/link.ts), fanned out to any open page as server-sent events.
// It runs under Node or Bun with no dependencies, from run.ts or inside the
// Electrobun shell in app/.
//
// PORT        the game's test port (default 7811)
// HTTP_PORT   the dashboard's port (default 7900)
// RE1_DATA    folders with Stage1..Stage7 room files, overlay first, split by
//             the platform's path separator (default /tmp/re1-pc)
// RE1_EXE     a local residentevil.exe to start, like --exe (the Electrobun app takes no arguments)
// RE1_ARGS    extra game arguments for --launch / --exe, e.g. "--boot rebecca"
// RELAY_PORT  pass the game's port through on this one, so a test script can
//             drive the game while the page watches (lab.ts RE1_LAB_RELAY)
import { spawn } from 'node:child_process';
import { readFileSync } from 'node:fs';
import http from 'node:http';
import net from 'node:net';
import path from 'node:path';
import { GameLink, Key } from '../harness/link.ts';
import { Bank, flag, messageOnScreen, roomLabel, screen, type GameState } from '../harness/state.ts';
import { loadRoomMap } from './rdt.ts';

export interface Options {
  gamePort: number;
  httpPort: number;
  dataDirs: string[];
  /** This folder: the page files and the repo's Types.h are found from it. */
  root: string;
  start?: { kind: 'lab' } | { kind: 'exe'; exe: string };
  gameArgs: string;
  relayPort?: number;
}

type Level = 'info' | 'warn' | 'error';
interface LogEntry {
  at: number;
  frame: number;
  level: Level;
  text: string;
}

/** ITEM_* names from src/game/Types.h, so the page shows names, not ids. */
function itemNames(root: string): Record<number, string> {
  const names: Record<number, string> = {};
  const header = readFileSync(path.join(root, '../../src/game/Types.h'), 'utf8');
  for (const m of header.matchAll(/^#define ITEM_(\w+)\s+0x([0-9A-Fa-f]+)/gm)) {
    names[parseInt(m[2], 16)] ??= m[1].toLowerCase().replace(/_/g, ' ');
  }
  return names;
}

const KEY_NAMES = new Map<number, string>(Object.entries(Key).map(([name, vk]) => [vk, name]));
const BANK_NAMES = new Map<number, string>(Object.entries(Bank).map(([name, i]) => [i, name]));
/** The message and main-state banks change every few frames; a log of them would drown the rest. */
const QUIET_BANKS = new Set<number>([Bank.mainState, Bank.message]);

/** A script's command with its key codes named: `tap 67 3` reads `tap action 3`. */
function describeCommand(line: string): string {
  const [cmd, vk, ...rest] = line.split(/\s+/);
  const name = /^(tap|down|up)$/.test(cmd) ? KEY_NAMES.get(Number(vk)) : undefined;
  return name ? [cmd, name, ...rest].join(' ') : line;
}

/** The flags that differ between two states, as "bank:index on|off". */
function flagChanges(a: GameState, b: GameState): string[] {
  const out: string[] = [];
  b.banks.forEach((bytes, bank) => {
    if (QUIET_BANKS.has(bank) || !a.banks[bank]) return;
    for (let i = 0; i < bytes.length * 8; i++) {
      const on = flag(b, bank, i);
      if (on !== flag(a, bank, i)) out.push(`${BANK_NAMES.get(bank) ?? bank}:${i} ${on ? 'on' : 'off'}`);
    }
  });
  return out;
}

/** What a tester wants to see between two states: rooms, cuts, damage, messages, items, flags. */
export function changes(a: GameState, b: GameState, names: Record<number, string>): { level: Level; text: string }[] {
  const out: { level: Level; text: string }[] = [];
  const note = (level: Level, text: string) => out.push({ level, text });
  const sameRoom = a.stage === b.stage && a.room === b.room;
  if (!sameRoom) note('info', `room ${roomLabel(a)} -> ${roomLabel(b)}`);
  else if (a.camera !== b.camera) note('info', `camera ${a.camera} -> ${b.camera}`);
  if (screen(a) !== screen(b)) note('info', `screen ${screen(a)} -> ${screen(b)}`);
  if (messageOnScreen(b) && (!messageOnScreen(a) || a.messageId !== b.messageId)) note('info', `message ${b.messageId}`);
  // A boot or room load rewrites her health outside gameplay; only a drop in play is a hit.
  if (sameRoom && a.play && b.play && b.player.hp < a.player.hp) note('warn', `player hit: hp ${a.player.hp} -> ${b.player.hp}`);
  const had = new Set(a.items.map((it) => it.id));
  const has = new Set(b.items.map((it) => it.id));
  for (const id of has) if (id && !had.has(id)) note('info', `bag: got ${names[id] ?? id}`);
  for (const id of had) if (id && !has.has(id)) note('info', `bag: lost ${names[id] ?? id}`);
  // A new game or a load writes whole banks: one line, not hundreds.
  const flags = flagChanges(a, b);
  if (flags.length > 16) note('info', `flags: ${flags.length} changed at once`);
  else for (const change of flags) note('info', `flag ${change}`);
  if (!sameRoom) return out;
  b.enemies.forEach((e, i) => {
    const was = a.enemies[i];
    if (!was || was.type !== e.type || was.hp <= 0) return;
    if (e.hp < was.hp) note('info', `enemy ${i} (type ${e.type.toString(16)}) hp ${was.hp} -> ${e.hp}${e.hp <= 0 ? ', down' : ''}`);
  });
  return out;
}

/** The parsed state as plain JSON: the flag banks go out as hex. */
function wire(s: GameState): unknown {
  return { ...s, banks: s.banks.map((b) => Buffer.from(b).toString('hex')), screen: screen(s), label: roomLabel(s) };
}

const STATIC: Record<string, string> = {
  '/': 'index.html',
  '/app.js': 'app.js',
  '/style.css': 'style.css',
  '/icon.png': '../app/icon.png',
};
const TYPES: Record<string, string> = { '.html': 'text/html', '.js': 'text/javascript', '.css': 'text/css', '.png': 'image/png' };

export async function start(o: Options): Promise<{ url: string; close: () => void }> {
  const clients = new Set<http.ServerResponse>();
  const log: LogEntry[] = [];
  const names = itemNames(o.root);
  let link: GameLink | undefined;
  let latest: GameState | undefined;
  /** The script on the relay port, if one is connected. Like the game, the newest client wins. */
  let script: net.Socket | undefined;

  function send(event: string, data: unknown): void {
    const chunk = `event: ${event}\ndata: ${JSON.stringify(data)}\n\n`;
    for (const c of clients) c.write(chunk);
  }

  function note(level: Level, text: string): void {
    const entry = { at: Date.now(), frame: latest?.frame ?? 0, level, text };
    log.push(entry);
    if (log.length > 1000) log.splice(0, 500);
    send('log', entry);
  }

  function attach(l: GameLink): void {
    link = l;
    l.lines.add((line) => script?.write(`${line}\n`));
    let bad = 0;
    l.listeners.add((r) => {
      if (r.t === 'state') {
        if (latest) for (const c of changes(latest, r.state, names)) note(c.level, c.text);
        latest = r.state;
        send('state', wire(r.state));
      } else if (r.t === 'ack' && !r.ok) {
        note('error', `game rejected command: ${r.cmd}`);
      }
      // GameLink keeps lines it could not parse; surface the new ones.
      while (bad < l.badLines.length) note('error', `bad line from game: ${l.badLines[bad++]}`);
    });
  }

  async function connectLoop(): Promise<void> {
    for (;;) {
      send('link', { connected: false });
      const l = await GameLink.connect(o.gamePort, '127.0.0.1', Number.MAX_SAFE_INTEGER);
      attach(l);
      note('info', `connected to the game on port ${o.gamePort}`);
      send('link', { connected: true });
      // Test mode ignores the real keyboard; the dashboard is for playing along.
      // A relay is for a script, which plays alone.
      if (!o.relayPort) l.keyboard(true).catch((err) => note('warn', `keyboard 1 failed: ${String(err)}`));
      // The game sends a new client a state line straight away (TestMode_Tick), and the listener takes it.
      await l.closed;
      link = undefined;
      script?.destroy();
      note('error', `game connection closed at frame ${latest?.frame ?? '?'}`);
      // The next game is a new run: comparing its first state with this one's last logs a jump that never happened.
      latest = undefined;
    }
  }

  const server = http.createServer((req, res) => {
    const url = new URL(req.url ?? '/', 'http://localhost');
    res.setHeader('Access-Control-Allow-Origin', '*');
    if (url.pathname === '/events') {
      res.writeHead(200, { 'Content-Type': 'text/event-stream', 'Cache-Control': 'no-cache', Connection: 'keep-alive' });
      res.write(`event: hello\ndata: ${JSON.stringify({ items: names, log, connected: !!link, keyboard: !o.relayPort, state: latest && wire(latest) })}\n\n`);
      clients.add(res);
      req.on('close', () => clients.delete(res));
      return;
    }
    if (url.pathname === '/room') {
      const stage = Number(url.searchParams.get('stage'));
      const room = Number(url.searchParams.get('room'));
      const cf = url.searchParams.has('cf') ? Number(url.searchParams.get('cf')) : undefined;
      try {
        const map = loadRoomMap(o.dataDirs, stage, room, cf);
        res.writeHead(200, { 'Content-Type': 'application/json' }).end(JSON.stringify(map));
      } catch (err) {
        res.writeHead(404, { 'Content-Type': 'application/json' }).end(JSON.stringify({ error: String(err) }));
      }
      return;
    }
    if (url.pathname === '/cmd' && req.method === 'POST') {
      let body = '';
      req.setEncoding('utf8');
      req.on('data', (c: string) => (body += c));
      req.on('end', () => {
        const line = body.trim();
        if (!link || !line || line.includes('\n')) {
          res.writeHead(409).end(link ? 'one command per request' : 'no game connected');
          return;
        }
        link.raw(line);
        note('info', `> ${line}`);
        res.writeHead(204).end();
      });
      return;
    }
    const file = STATIC[url.pathname];
    if (!file) {
      res.writeHead(404).end();
      return;
    }
    res.writeHead(200, { 'Content-Type': TYPES[path.extname(file)] });
    res.end(readFileSync(path.join(o.root, 'public', file)));
  });

  await new Promise<void>((resolve) => server.listen(o.httpPort, '127.0.0.1', resolve));

  const relay = net.createServer((socket) => {
    // No game yet: close, and the script's GameLink.connect tries again.
    if (!link) return socket.destroy();
    script?.destroy();
    script = socket;
    note('info', `script connected on relay port ${o.relayPort}`);
    socket.setEncoding('utf8');
    let buffer = '';
    socket.on('data', (chunk: string) => {
      buffer += chunk;
      let nl: number;
      while ((nl = buffer.indexOf('\n')) >= 0) {
        const line = buffer.slice(0, nl).trim();
        buffer = buffer.slice(nl + 1);
        if (!line || !link) continue;
        link.raw(line);
        // Its polling would bury the log; the rest is what it did.
        if (!/^(ping|state)\b/.test(line)) note('info', `script> ${describeCommand(line)}`);
      }
    });
    socket.on('error', () => undefined);
    socket.on('close', () => {
      if (script !== socket) return;
      script = undefined;
      note('info', 'script disconnected');
    });
  });
  if (o.relayPort) relay.listen(o.relayPort, '127.0.0.1');

  let stopGame = () => {};
  if (o.start?.kind === 'lab') {
    const lab = await import('../harness/lab.ts');
    lab.stop(o.gamePort);
    lab.launch(o.gamePort, o.gameArgs);
    const ssh = lab.tunnel(o.gamePort);
    stopGame = () => {
      ssh.kill();
      lab.stop(o.gamePort);
    };
  } else if (o.start?.kind === 'exe') {
    const args = ['--test-port', String(o.gamePort), ...o.gameArgs.split(/\s+/).filter(Boolean)];
    const game = spawn(o.start.exe, args, { cwd: path.dirname(o.start.exe), stdio: 'ignore' });
    game.on('exit', (code) => note(code ? 'error' : 'info', `game exited with code ${code}`));
    stopGame = () => game.kill();
  }
  void connectLoop();

  return {
    url: `http://127.0.0.1:${o.httpPort}/`,
    close: () => {
      for (const c of clients) c.end();
      server.close();
      relay.close();
      script?.destroy();
      link?.close();
      stopGame();
    },
  };
}

export function optionsFromEnv(argv: string[], root: string): Options {
  const exeAt = argv.indexOf('--exe');
  const exe = exeAt >= 0 ? argv[exeAt + 1] : process.env.RE1_EXE;
  return {
    gamePort: Number(process.env.PORT ?? 7811),
    httpPort: Number(process.env.HTTP_PORT ?? 7900),
    dataDirs: (process.env.RE1_DATA ?? '/tmp/re1-pc').split(path.delimiter),
    root,
    start: argv.includes('--launch') ? { kind: 'lab' } : exe ? { kind: 'exe', exe } : undefined,
    gameArgs: process.env.RE1_ARGS ?? '',
    relayPort: process.env.RELAY_PORT ? Number(process.env.RELAY_PORT) : undefined,
  };
}
