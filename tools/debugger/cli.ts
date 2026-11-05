// The dashboard from a terminal: what the page's log shows, the live state,
// and the command box, for a reader with no browser (or an agent).
//
//   node tools/debugger/cli.ts watch [--states]   follow the log; --states adds a line a second
//   node tools/debugger/cli.ts state [--json]     the latest state, once
//   node tools/debugger/cli.ts send <line>        a command, as the page's box sends it
//
// DASHBOARD sets the dashboard's address (default http://127.0.0.1:7900).
const base = process.env.DASHBOARD ?? 'http://127.0.0.1:7900';

type Entry = { at: number; frame: number; level: string; text: string };
type State = {
  frame: number;
  stage: number;
  room: number;
  camera: number;
  label: string;
  screen: string;
  player: { x: number; y: number; z: number; hp: number };
  enemies: { x: number; z: number; hp: number }[];
};

/** The dashboard's event stream, one {event, data} at a time. */
async function* events(): AsyncGenerator<{ event: string; data: unknown }> {
  const res = await fetch(`${base}/events`);
  if (!res.ok || !res.body) throw new Error(`${base}/events: HTTP ${res.status}`);
  const dec = new TextDecoder();
  let buf = '';
  for await (const chunk of res.body) {
    buf += dec.decode(chunk, { stream: true });
    let end: number;
    while ((end = buf.indexOf('\n\n')) >= 0) {
      const block = buf.slice(0, end);
      buf = buf.slice(end + 2);
      const event = /^event: (.*)$/m.exec(block)?.[1];
      const data = /^data: (.*)$/m.exec(block)?.[1];
      if (event && data) yield { event, data: JSON.parse(data) };
    }
  }
}

const clock = (ms: number) => new Date(ms).toTimeString().slice(0, 8);
const entry = (e: Entry) => `${clock(e.at)} f${e.frame} ${e.level === 'info' ? '' : `${e.level.toUpperCase()} `}${e.text}`;
const live = (e: State['enemies'][number]) => e.x !== -30000 && e.hp > 0;
const summary = (s: State) =>
  `f${s.frame} ${s.screen} stage ${s.stage + 1} room ${s.room.toString(16).padStart(2, '0')} ${s.label} cam ${s.camera} ` +
  `at (${s.player.x}, ${s.player.y}, ${s.player.z}) hp ${s.player.hp} enemies ${s.enemies.filter(live).length}`;

const [verb, ...rest] = process.argv.slice(2);
if (verb === 'watch') {
  const states = rest.includes('--states');
  let shown = 0;
  for await (const { event, data } of events()) {
    if (event === 'hello') for (const e of (data as { log: Entry[] }).log) console.log(entry(e));
    if (event === 'log') console.log(entry(data as Entry));
    if (event === 'state' && states && Date.now() - shown >= 1000) {
      shown = Date.now();
      console.log(`${clock(shown)} ${summary(data as State)}`);
    }
  }
} else if (verb === 'state') {
  for await (const { event, data } of events()) {
    if (event !== 'hello') continue;
    const s = (data as { state?: State }).state;
    if (!s) throw new Error('no game connected');
    console.log(rest.includes('--json') ? JSON.stringify(s, null, 2) : summary(s));
    process.exit(0);
  }
} else if (verb === 'send' && rest.length) {
  const res = await fetch(`${base}/cmd`, { method: 'POST', body: rest.join(' ') });
  if (!res.ok) throw new Error(`HTTP ${res.status}: ${await res.text()}`);
} else {
  console.error('usage: cli.ts watch [--states] | state [--json] | send <line>');
  process.exit(2);
}
