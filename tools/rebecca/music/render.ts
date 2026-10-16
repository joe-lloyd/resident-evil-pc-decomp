// Render a Strudel sketch to the WAV the game plays, with no person at a
// browser, the same bytes every time.
//
//   node tools/rebecca/music/render.ts <@strudel/web 1.2.5 dist> [sketch...]
//
// Writes music/renders/<sketch>.wav for each sketch named, or for every
// sketch a cue in plan/music.ts names. build.ts ships them.
//
// How: Strudel's own browser build, the one the owner's page plays, runs in a
// headless Chrome, Playwright's chrome-headless-shell (already on the machine,
// or set CHROME), driven over the DevTools protocol with Node's own
// WebSocket. No new dependencies. In the page:
// - the audio context is an OfflineAudioContext, so the piece renders as fast
//   as it can and nothing depends on the clock;
// - Math.random is seeded, there and in the audio worklets, so the noise and
//   the reverb's impulse are the same each time;
// - every sample is fetched through this script, which pins VCSL to a commit
//   and keeps a copy (RE1_MUSIC_CACHE, default ~/.cache/rebecca-music);
// - the notes are queried and played one by one in order, as Strudel's
//   scheduler would, so the graph is built the same way each time;
// - Chrome's mixing is made exact, and nothing changes the graph while it
//   renders (the page's notes say why).
//
// The piece's loop is found from its notes: the fewest cycles after which
// they repeat. It renders three passes. The file is the first pass, which
// plays once as the intro, and the second, which loops: the second already
// holds the tails of the notes before it, so the join doesn't click. The
// third pass is only to measure that join.
import { spawn } from 'node:child_process';
import { createHash } from 'node:crypto';
import { existsSync, mkdirSync, mkdtempSync, readFileSync, readdirSync, rmSync, writeFileSync } from 'node:fs';
import { createServer, type IncomingMessage } from 'node:http';
import { homedir, tmpdir } from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { CUES } from '../plan/music.ts';
import { adpcmRoundTrip, levelGain, loopedWav, peakDb, rmsDb, RATE, toInt16, toMono22k } from './ps1.ts';

const here = path.dirname(fileURLToPath(import.meta.url));
/** VCSL's files at the commit that was its master when the sketches were written. */
const VCSL_MASTER = 'https://raw.githubusercontent.com/sgossner/VCSL/master/';
const VCSL_PINNED = 'https://raw.githubusercontent.com/sgossner/VCSL/c1ea7bcc3c7309650ab0da9d15c9cd1fbc4a4c7e/';
/** Strudel renders at this rate; ps1.ts halves it. */
const RENDER_RATE = 44100;
/** The longest loop looked for, in cycles. */
const MAX_CYCLES = 64;
const SEED = 0x5eb3cca;

export interface Rendered {
  readonly sketch: string;
  readonly cycles: number;
  readonly cps: number;
  readonly introFrames: number;
  readonly loopFrames: number;
  /** How far the loop strays from the pass after it, the largest difference in 16-bit steps: 0 is a join with no click. */
  readonly seam: number;
  readonly rms: number;
  readonly peak: number;
  readonly sha256: string;
}

function findChrome(): string {
  if (process.env.CHROME) return process.env.CHROME;
  const roots = [path.join(homedir(), 'Library/Caches/ms-playwright'), path.join(homedir(), '.cache/ms-playwright')];
  for (const root of roots) {
    if (!existsSync(root)) continue;
    const shells = readdirSync(root).filter((d) => d.startsWith('chromium_headless_shell-')).sort().reverse();
    for (const d of shells) {
      for (const sub of readdirSync(path.join(root, d))) {
        const exe = path.join(root, d, sub, 'chrome-headless-shell');
        if (existsSync(exe)) return exe;
      }
    }
  }
  throw new Error('no chrome-headless-shell found: set CHROME to a Chrome or Chromium binary');
}

const page = `<!doctype html><meta charset="utf-8"><title>render</title>
<script>
// Seeded before Strudel loads: mulberry32.
function seeded(seed) { let a = seed >>> 0; return () => { a = (a + 0x6d2b79f5) >>> 0; let t = a; t = Math.imul(t ^ (t >>> 15), t | 1); t ^= t + Math.imul(t ^ (t >>> 7), t | 61); return ((t ^ (t >>> 14)) >>> 0) / 4294967296; }; }
Math.random = seeded(${SEED});
// Strudel makes its one audio context with new AudioContext(): make that an offline one, once the length is known.
window.__frames = 0;
class RenderContext extends OfflineAudioContext {
  constructor() {
    if (!window.__frames) throw new Error('the audio context was asked for before the length was known');
    super({ numberOfChannels: 2, length: window.__frames, sampleRate: ${RENDER_RATE} });
  }
  resume() { return Promise.resolve(); }
}
window.AudioContext = RenderContext;
// The other offline renders Strudel starts (the reverb's impulse) must finish before ours.
window.__pending = new Set();
const nativeStart = OfflineAudioContext.prototype.startRendering;
OfflineAudioContext.prototype.startRendering = function () {
  const p = nativeStart.call(this);
  if (!(this instanceof RenderContext)) { window.__pending.add(p); p.finally(() => window.__pending.delete(p)); }
  return p;
};
// Every fetch goes through the render script.
const nativeFetch = window.fetch.bind(window);
window.fetch = (url, opts) => {
  const href = new URL(typeof url === 'string' ? url : url.url, location.href).href;
  const p = href.startsWith(location.origin) ? nativeFetch(url, opts) : nativeFetch('/fetch?url=' + encodeURIComponent(href), opts);
  window.__pending.add(p); p.finally(() => window.__pending.delete(p));
  return p;
};
// Strudel tidies a voice up when its 'ended' event comes: it disconnects its
// nodes and stops its modulators. Offline, those events reach the page while
// the render runs, at points that differ from run to run, so each run cut
// the sound in a different place. Here nothing listens for 'ended', and once
// the render starts nothing in the page changes the graph: an ended voice is
// silent anyway.
Object.defineProperty(AudioScheduledSourceNode.prototype, 'onended', { set() {}, get() { return null; } });
const nativeListen = EventTarget.prototype.addEventListener;
EventTarget.prototype.addEventListener = function (type, ...rest) {
  if (type === 'ended' && this instanceof AudioScheduledSourceNode) return;
  return nativeListen.call(this, type, ...rest);
};
// Two things in Chrome change the low bits of a mix from run to run:
// - A node sums its inputs in the order of a hash of their addresses, and
//   float sums of three or more depend on the order.
// - A node's audio side goes when the collector takes its JavaScript object,
//   which locks the graph from the main thread at no set moment.
// So every node that is connected is kept, and every input to a node that
// mixes more than one goes through a worklet that rounds it to steps of
// 2^-20 (-120 dB): sums of such steps are exact in any order.
window.__keep = [];
const nativeConnect = AudioNode.prototype.connect;
function rounder(ctx) {
  const q = new AudioWorkletNode(ctx, 'reb-round', { numberOfInputs: 1, numberOfOutputs: 1, outputChannelCount: [2], channelCount: 2, channelCountMode: 'explicit' });
  window.__keep.push(q);
  return q;
}
AudioNode.prototype.connect = function (...args) {
  const dst = args[0];
  window.__keep.push(this, dst);
  const mixes = window.__rounding && args.length === 1 && dst instanceof AudioNode && !(dst instanceof ChannelMergerNode) && this.context instanceof RenderContext;
  if (!mixes) return nativeConnect.apply(this, args);
  const into = dst.__into ??= [];
  if (into.length === 1 && !into[0].rounded) {
    // The first input came straight in: send it through a rounder too.
    const first = into[0];
    first.src.disconnect(dst);
    first.rounded = rounder(this.context);
    nativeConnect.call(first.src, first.rounded);
    nativeConnect.call(first.rounded, dst);
  }
  if (into.length === 0) {
    into.push({ src: this });
    return nativeConnect.apply(this, args);
  }
  const q = rounder(this.context);
  into.push({ src: this, rounded: q });
  nativeConnect.call(this, q);
  nativeConnect.call(q, dst);
  return dst;
};
window.__rendering = false;
window.__rounding = false;
for (const [proto, name] of [[AudioNode.prototype, 'disconnect'], [AudioScheduledSourceNode.prototype, 'stop']]) {
  const native = proto[name];
  proto[name] = function (...args) {
    if (!window.__rendering) return native.apply(this, args);
  };
}
async function settle() {
  for (let quiet = 0; quiet < 3; ) {
    if (window.__pending.size) { quiet = 0; await Promise.allSettled([...window.__pending]); }
    else { quiet++; await new Promise((r) => setTimeout(r, 30)); }
  }
}
</script>
<script type="module">
import { initStrudel, getAudioContext, initAudio, webaudioOutput } from '/strudel/index.mjs';
const workletSeed = 'data:text/javascript,' + encodeURIComponent(seeded.toString() + ';Math.random = seeded(${SEED + 1});' + \`
registerProcessor('reb-round', class extends AudioWorkletProcessor {
  process(inputs, outputs) {
    const input = inputs[0], output = outputs[0];
    for (let c = 0; c < output.length; c++) {
      const i = input[c] ?? input[0], o = output[c];
      if (!i) { o.fill(0); continue; }
      for (let k = 0; k < o.length; k++) o[k] = Math.round(i[k] * 1048576) / 1048576;
    }
    return true;
  }
});\`);
window.renderSketch = async (code, maxCycles) => {
  const repl = await initStrudel();
  const pattern = await repl.evaluate(code, false);
  if (!pattern) throw new Error('the sketch did not evaluate: ' + (repl.state.evalError?.message ?? 'no pattern'));
  await settle(); // the sample map
  const cps = repl.scheduler.cps;
  const onsets = (a, b) => pattern.queryArc(a, b, { _cps: cps }).filter((h) => h.hasOnset());
  // A pass's notes, its times from its start; a signal's values (a filter on a sine) to 6 digits, as float time drifts.
  const round = (k, v) => (typeof v === 'number' ? +v.toPrecision(6) : v);
  const sig = (a, b) => onsets(a, b).map((h) => JSON.stringify([h.whole.begin.valueOf() - a, h.whole.end.valueOf() - a, h.value], round)).sort().join('|');
  let cycles = 0;
  for (let n = 1; n <= maxCycles && !cycles; n++) if (sig(0, n) === sig(n, 2 * n) && sig(n, 2 * n) === sig(2 * n, 3 * n)) cycles = n;
  if (!cycles) throw new Error('its notes do not repeat within ' + maxCycles + ' cycles');
  const seconds = (3 * cycles) / cps;
  window.__frames = Math.round(seconds * ${RENDER_RATE});
  const ctx = getAudioContext();
  await ctx.audioWorklet.addModule(workletSeed);
  // Strudel steals the oldest voice past 128 at once. It counts a voice off
  // when it ends, which never happens here, so lift the limit: no sketch
  // comes near 128 voices sounding together.
  await initAudio({ maxPolyphony: 1e9 });
  window.__rounding = true;
  let notes = 0;
  for (let c = 0; c < 3 * cycles; c++) {
    for (const h of onsets(c, c + 1)) {
      await webaudioOutput(h, 0, h.duration / cps, cps, h.whole.begin.valueOf() / cps);
      notes++;
    }
  }
  await settle();
  window.__rendering = true;
  const buf = await ctx.startRendering();
  const body = new Float32Array(buf.length * 2);
  body.set(buf.getChannelData(0), 0);
  body.set(buf.getChannelData(1), buf.length);
  await fetch('/result', { method: 'POST', body });
  return { cycles, cps, frames: buf.length, notes };
};
window.ready = true;
</script>`;

function body(req: IncomingMessage): Promise<Buffer> {
  return new Promise((resolve, reject) => {
    const parts: Buffer[] = [];
    req.on('data', (c: Buffer) => parts.push(c));
    req.on('end', () => resolve(Buffer.concat(parts)));
    req.on('error', reject);
  });
}

/** The page, Strudel's dist, a cached fetch for samples, and a place for the result. */
function serve(dist: string, cache: string, onResult: (b: Buffer) => void) {
  mkdirSync(cache, { recursive: true });
  const server = createServer(async (req, res) => {
    try {
      const url = new URL(req.url ?? '/', 'http://localhost');
      if (url.pathname === '/') {
        res.writeHead(200, { 'content-type': 'text/html' }).end(page);
      } else if (url.pathname.startsWith('/strudel/')) {
        const file = path.join(dist, path.normalize(url.pathname.slice('/strudel/'.length)));
        if (!file.startsWith(dist) || !existsSync(file)) return void res.writeHead(404).end();
        res.writeHead(200, { 'content-type': /\.m?js$/.test(file) ? 'text/javascript' : 'application/octet-stream' }).end(readFileSync(file));
      } else if (url.pathname === '/fetch') {
        const target = (url.searchParams.get('url') ?? '').replace(VCSL_MASTER, VCSL_PINNED);
        if (!/^https:\/\/raw\.githubusercontent\.com\//.test(target)) return void res.writeHead(403).end(`not fetching ${target}`);
        const file = path.join(cache, createHash('sha256').update(target).digest('hex'));
        if (!existsSync(file)) {
          const got = await fetch(target);
          if (!got.ok) return void res.writeHead(502).end(`${got.status} ${target}`);
          writeFileSync(file, Buffer.from(await got.arrayBuffer()));
        }
        res.writeHead(200, { 'access-control-allow-origin': '*', 'content-type': target.endsWith('.json') ? 'application/json' : 'application/octet-stream' }).end(readFileSync(file));
      } else if (url.pathname === '/result' && req.method === 'POST') {
        onResult(await body(req));
        res.writeHead(200).end();
      } else {
        res.writeHead(404).end();
      }
    } catch (e) {
      res.writeHead(500).end(String(e));
    }
  });
  return new Promise<{ port: number; close: () => void }>((resolve) => {
    server.listen(0, '127.0.0.1', () => {
      const address = server.address();
      resolve({ port: typeof address === 'object' && address ? address.port : 0, close: () => server.close() });
    });
  });
}

/** A minimal DevTools protocol client over Node's WebSocket. */
class Cdp {
  private next = 1;
  private waiting = new Map<number, { resolve: (v: unknown) => void; reject: (e: Error) => void }>();
  readonly logs: string[] = [];
  private ws: WebSocket;
  private constructor(ws: WebSocket) {
    this.ws = ws;
    ws.addEventListener('message', (ev) => {
      const msg = JSON.parse(String(ev.data)) as { id?: number; result?: unknown; error?: { message: string }; method?: string; params?: { type?: string; args?: { value?: unknown; description?: string }[]; exceptionDetails?: { text: string } } };
      if (msg.id !== undefined) {
        const w = this.waiting.get(msg.id);
        this.waiting.delete(msg.id);
        if (msg.error) w?.reject(new Error(msg.error.message));
        else w?.resolve(msg.result);
      } else if (msg.method === 'Runtime.consoleAPICalled') {
        this.logs.push((msg.params?.args ?? []).map((a) => String(a.value ?? a.description ?? '')).join(' '));
      } else if (msg.method === 'Runtime.exceptionThrown') {
        this.logs.push(`exception: ${JSON.stringify(msg.params?.exceptionDetails)}`);
      }
    });
  }
  static open(url: string): Promise<Cdp> {
    return new Promise((resolve, reject) => {
      const ws = new WebSocket(url);
      ws.addEventListener('open', () => resolve(new Cdp(ws)));
      ws.addEventListener('error', () => reject(new Error(`could not connect to ${url}`)));
    });
  }
  send(method: string, params: object = {}): Promise<any> {
    const id = this.next++;
    this.ws.send(JSON.stringify({ id, method, params }));
    return new Promise((resolve, reject) => this.waiting.set(id, { resolve, reject }));
  }
  close() {
    this.ws.close();
  }
}

async function launchChrome(): Promise<{ wsUrl: string; kill: () => Promise<void> }> {
  const profile = mkdtempSync(path.join(tmpdir(), 'reb-render-'));
  const chrome = spawn(findChrome(), ['--headless', '--remote-debugging-port=0', `--user-data-dir=${profile}`, '--no-first-run', '--autoplay-policy=no-user-gesture-required', 'about:blank'], { stdio: ['ignore', 'ignore', 'pipe'] });
  const exited = new Promise((resolve) => chrome.on('exit', resolve));
  // Chrome's scratch profile goes once Chrome has let go of it.
  const kill = async () => {
    chrome.kill();
    await exited;
    rmSync(profile, { recursive: true, force: true, maxRetries: 5 });
  };
  const browserWs = await new Promise<string>((resolve, reject) => {
    let err = '';
    chrome.stderr!.on('data', (d: Buffer) => {
      err += d.toString();
      const m = /DevTools listening on (ws:\/\/\S+)/.exec(err);
      if (m) resolve(m[1]!);
    });
    chrome.on('exit', (code) => reject(new Error(`chrome exited (${code}): ${err}`)));
    setTimeout(() => reject(new Error(`chrome did not start: ${err}`)), 30_000);
  });
  const { host } = new URL(browserWs);
  const targets = (await (await fetch(`http://${host}/json/list`)).json()) as { type: string; webSocketDebuggerUrl: string }[];
  const target = targets.find((t) => t.type === 'page');
  if (!target) throw new Error('chrome has no page');
  return { wsUrl: target.webSocketDebuggerUrl, kill };
}

/** Render one sketch: Strudel in the browser, then the PS1 treatment and the loop. */
export async function render(dist: string, sketchFile: string, cache: string): Promise<{ wav: Uint8Array; info: Rendered }> {
  let result: Buffer | undefined;
  const server = await serve(path.resolve(dist), cache, (b) => (result = b));
  const chrome = await launchChrome();
  const cdp = await Cdp.open(chrome.wsUrl);
  try {
    await cdp.send('Runtime.enable');
    await cdp.send('Page.navigate', { url: `http://127.0.0.1:${server.port}/` });
    for (let i = 0; i < 200; i++) {
      const r = await cdp.send('Runtime.evaluate', { expression: 'window.ready === true', returnByValue: true });
      if (r.result?.value === true) break;
      await new Promise((res) => setTimeout(res, 100));
    }
    const code = readFileSync(sketchFile, 'utf8');
    const r = await cdp.send('Runtime.evaluate', { expression: `renderSketch(${JSON.stringify(code)}, ${MAX_CYCLES})`, awaitPromise: true, returnByValue: true });
    if (r.exceptionDetails) throw new Error(`the page failed: ${r.exceptionDetails.exception?.description ?? r.exceptionDetails.text}\n${cdp.logs.join('\n')}`);
    const meta = r.result.value as { cycles: number; cps: number; frames: number; notes: number };
    // Strudel's own warnings, such as a sound it could not find.
    for (const line of cdp.logs) if (/warn|error|not found|cannot/i.test(line)) console.warn(`  strudel: ${line.replace(/%c|background-color[^%]*$/g, '').trim()}`);
    if (!result) throw new Error('the page sent no audio');
    const floats = new Float32Array(result.buffer, result.byteOffset, result.byteLength / 4);
    const mono = toMono22k(floats.subarray(0, meta.frames), floats.subarray(meta.frames));
    const pass = Math.round(meta.cycles / meta.cps * RATE);
    const kept = mono.subarray(0, 2 * pass);
    const gain = levelGain(kept);
    const pcm = adpcmRoundTrip(toInt16(kept, gain));
    // The join: after the loop's last sample the game plays its first, where
    // the endless piece would play the third pass. They should be the same.
    let seam = 0;
    for (let k = 0; k < pass; k++) seam = Math.max(seam, Math.abs(mono[pass + k]! - mono[2 * pass + k]!) * gain * 32767);
    const wav = loopedWav(pcm, pass);
    const info: Rendered = {
      sketch: path.basename(sketchFile, '.js'),
      cycles: meta.cycles,
      cps: meta.cps,
      introFrames: pass,
      loopFrames: pcm.length - pass,
      seam,
      rms: rmsDb(Array.from(pcm, (v) => v / 32768)),
      peak: peakDb(Array.from(pcm, (v) => v / 32768)),
      sha256: createHash('sha256').update(wav).digest('hex'),
    };
    return { wav, info };
  } finally {
    cdp.close();
    await chrome.kill();
    server.close();
  }
}

if (process.argv[1] === fileURLToPath(import.meta.url)) {
  const [dist, ...names] = process.argv.slice(2);
  if (!dist || !existsSync(path.join(dist, 'index.mjs'))) {
    console.error('usage: node tools/rebecca/music/render.ts <@strudel/web 1.2.5 dist folder> [sketch...]');
    process.exit(2);
  }
  const sketches = names.length ? names : [...new Set(CUES.flatMap((c) => (c.sketch ? [c.sketch] : [])))];
  const cache = process.env.RE1_MUSIC_CACHE ?? path.join(homedir(), '.cache', 'rebecca-music');
  const out = path.join(here, 'renders');
  mkdirSync(out, { recursive: true });
  for (const s of sketches) {
    const { wav, info } = await render(dist, path.join(here, 'sketches', `${s}.js`), cache);
    writeFileSync(path.join(out, `${s}.wav`), wav);
    const sec = (n: number) => (n / RATE).toFixed(1);
    console.log(`${s}: ${info.cycles} cycles at ${(info.cps * 60).toFixed(0)} cpm, intro ${sec(info.introFrames)} s then a ${sec(info.loopFrames)} s loop, loop against the next pass ${info.seam.toFixed(1)} steps at most, ${info.rms.toFixed(1)} dB RMS, peak ${info.peak.toFixed(1)} dB, sha256 ${info.sha256}`);
  }
}
