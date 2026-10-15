// Pick a free sound for each of RE1's instruments, so the RE1 tracks can also
// play on sounds we may use: VCSL (CC0) and Strudel's own synths.
//
// A first try matched each game sample to the free sound with the nearest
// spectrum. It picked bare sawtooth waves and white noise, which sound like a
// chiptune. So this sorts each game instrument into a family by what it does
// (bass, strings, piano, bell, cymbal and so on), from its measured sound and
// how the music uses it, and gives each family one sound chosen to sound good:
// a recorded VCSL instrument where there is one, a detuned synth with vibrato
// where there isn't. The notes stay the game's; the instrument is ours.
//
//   node tools/rebecca/music/re1-voices.ts <rae music dir> <cache dir> <voices.json>
//
// voices.json maps each instrument tone, "SEPxx/p<program>t<tone>", to its
// voice, for re1.ts. To change an instrument by ear, put its family in
// re1-voices.fix.json beside this file, by program ("SEP0F/p2": "harp") or by
// tone ("SEP0F/p7t3": "snare"); it wins over the sorting.
import { existsSync, mkdirSync, readFileSync, readdirSync, writeFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { spuEnvelope, type Music } from './re1.ts';

export const VCSL = 'https://raw.githubusercontent.com/felixroos/dough-samples/9eacfc86ec4393e68a463ff52b01c19cfaa77f38/vcsl.json';

// ---- Reading sound -----------------------------------------------------------

/** A WAV as mono floats: 8, 16, 24 or 32-bit PCM, or 32-bit float. */
export function readWav(b: Buffer): { x: Float32Array; rate: number } {
  if (b.toString('latin1', 0, 4) !== 'RIFF' || b.toString('latin1', 8, 12) !== 'WAVE') throw new Error('not a WAV');
  let at = 12;
  let fmt: { format: number; channels: number; rate: number; bits: number } | undefined;
  while (at + 8 <= b.length) {
    const id = b.toString('latin1', at, at + 4);
    const size = b.readUInt32LE(at + 4);
    const body = at + 8;
    if (id === 'fmt ') {
      let format = b.readUInt16LE(body);
      if (format === 0xfffe) format = b.readUInt16LE(body + 24);
      fmt = { format, channels: b.readUInt16LE(body + 2), rate: b.readUInt32LE(body + 4), bits: b.readUInt16LE(body + 14) };
    } else if (id === 'data' && fmt) {
      const bytes = fmt.bits / 8;
      const frames = Math.floor(Math.min(size, b.length - body) / (bytes * fmt.channels));
      const x = new Float32Array(frames);
      for (let i = 0; i < frames; i++) {
        let sum = 0;
        for (let c = 0; c < fmt.channels; c++) {
          const p = body + (i * fmt.channels + c) * bytes;
          sum += fmt.format === 3 ? b.readFloatLE(p)
            : bytes === 1 ? (b[p]! - 128) / 128
            : bytes === 2 ? b.readInt16LE(p) / 32768
            : bytes === 3 ? b.readIntLE(p, 3) / 8388608
            : b.readInt32LE(p) / 2147483648;
        }
        x[i] = sum / fmt.channels;
      }
      return { x, rate: fmt.rate };
    }
    at = body + size + (size & 1);
  }
  throw new Error('WAV has no data');
}

/** Magnitudes of a Hann-windowed FFT of `n` (a power of two) samples from `from`. */
function spectrum(x: Float32Array, from: number, n: number): Float64Array {
  const re = new Float64Array(n);
  const im = new Float64Array(n);
  for (let i = 0; i < n; i++) re[i] = (x[from + i] ?? 0) * (0.5 - 0.5 * Math.cos((2 * Math.PI * i) / (n - 1)));
  for (let i = 1, j = 0; i < n; i++) {
    let bit = n >> 1;
    for (; j & bit; bit >>= 1) j ^= bit;
    j ^= bit;
    if (i < j) {
      [re[i], re[j]] = [re[j]!, re[i]!];
      [im[i], im[j]] = [im[j]!, im[i]!];
    }
  }
  for (let len = 2; len <= n; len <<= 1) {
    const a = (-2 * Math.PI) / len;
    for (let i = 0; i < n; i += len) {
      for (let k = 0; k < len / 2; k++) {
        const wr = Math.cos(a * k);
        const wi = Math.sin(a * k);
        const p = i + k;
        const q = p + len / 2;
        const tr = re[q]! * wr - im[q]! * wi;
        const ti = re[q]! * wi + im[q]! * wr;
        re[q] = re[p]! - tr;
        im[q] = im[p]! - ti;
        re[p] = re[p]! + tr;
        im[p] = im[p]! + ti;
      }
    }
  }
  const mag = new Float64Array(n / 2);
  for (let i = 0; i < n / 2; i++) mag[i] = Math.hypot(re[i]!, im[i]!);
  return mag;
}

const HARMONICS = 12;
const BANDS = [60, 120, 250, 500, 1000, 2000, 4000, 8000, 16000];
const db = (v: number) => 20 * Math.log10(Math.max(v, 1e-9));

/** What a sound measures as. */
export interface Timbre {
  /** dB of harmonics 1..12 against the loudest, for a pitched sound. */
  readonly harmonics: readonly number[];
  /** dB of the octave bands from 60 Hz against the loudest. */
  readonly bands: readonly number[];
  /** 0 for a pure tone, near 1 for noise. */
  readonly flatness: number;
  /** How strongly it repeats at its best period: near 1 for a pitched sound. */
  readonly pitched: number;
  /** Seconds to its peak, and from the peak down 20 dB (Infinity if it never falls that far). */
  readonly attack: number;
  readonly fall: number;
  /** RMS of the steady part, as the sample stands. */
  readonly level: number;
  /** The amplitude-weighted mean harmonic: near 1 for a dull sound, 3 and up for a bright one. */
  readonly brightness: number;
  /** Share of the energy up to the 12th harmonic that sits on the harmonics: low for a bell's or a gong's partials. */
  readonly harmonicity: number;
  /** The fundamental it was measured at, in Hz. */
  readonly f0: number;
}

/**
 * Measure a sound around its steady part: from `steady` (a sample index) or
 * from 60 ms after its peak. `expected` is where its fundamental should be;
 * the sound's own repeat period wins when it has a clear one.
 */
export function measure(x: Float32Array, rate: number, expected: number, steady?: number): Timbre {
  let f0 = expected;
  const frame = Math.round(rate / 100);
  const env: number[] = [];
  for (let i = 0; i + frame <= x.length; i += frame) {
    let s = 0;
    for (let j = i; j < i + frame; j++) s += x[j]! * x[j]!;
    env.push(Math.sqrt(s / frame));
  }
  const peakAt = env.indexOf(Math.max(...env));
  const peak = env[peakAt] ?? 0;
  const attack = (env.findIndex((v) => v >= 0.9 * peak) * frame) / rate;
  const fallAt = env.findIndex((v, i) => i > peakAt && v < peak / 10);
  // A one-shot that stops before it has fallen 20 dB falls at its end; a looped one rings on.
  const fall = fallAt >= 0 ? ((fallAt - peakAt) * frame) / rate : steady === undefined ? ((env.length - peakAt) * frame) / rate : Infinity;
  // A short loop or one-shot is repeated to fill the window, as the SPU loops it.
  const n = 8192;
  let from = steady ?? Math.min(peakAt * frame + Math.round(rate * 0.06), Math.max(0, x.length - n));
  let src = x;
  if (from + n > x.length) {
    const seg = x.subarray(from);
    src = new Float32Array(n);
    for (let i = 0; i < n; i++) src[i] = seg.length ? seg[i % seg.length]! : 0;
    from = 0;
  }
  // The sample's own pitch: the shortest period that repeats nearly as well as
  // the best one, down to 50 Hz. A centre key can sit octaves away from
  // what the sample sounds (RE1 tunes some samples far from their recording).
  const corr = (lag: number) => {
    let ab = 0;
    let aa = 0;
    let bb = 0;
    for (let i = from; i < from + n - lag && i + lag < src.length; i++) {
      ab += src[i]! * src[i + lag]!;
      aa += src[i]! ** 2;
      bb += src[i + lag]! ** 2;
    }
    return ab / Math.sqrt(aa * bb + 1e-12);
  };
  // Short lags of a smooth sound always correlate, so look only past the
  // first dip below zero.
  const lags = Array.from({ length: Math.floor(rate / 50) }, (_, i) => i + 1);
  const scores = lags.map(corr);
  const dip = scores.findIndex((c) => c < 0);
  const past = dip < 0 ? [] : scores.slice(dip);
  const top = past.length ? Math.max(...past) : 0;
  const pitched = top;
  if (pitched > 0.5) {
    // The first peak near the best, climbed to its top: a smooth sound's peaks are broad.
    let j = past.findIndex((c) => c >= 0.92 * top);
    while (j + 1 < past.length && past[j + 1]! >= past[j]!) j++;
    const lag = dip + 1 + j;
    if (rate / lag >= 40 && rate / lag <= 4000) f0 = rate / lag;
  }
  const mag = spectrum(src, from, n);
  const bin = rate / n;
  const at = (hz: number) => {
    let m = 0;
    for (let k = Math.floor((hz * 0.97) / bin); k <= Math.ceil((hz * 1.03) / bin) && k < mag.length; k++) m = Math.max(m, mag[k]!);
    return m;
  };
  const h = Array.from({ length: HARMONICS }, (_, k) => (f0 * (k + 1) < rate / 2 ? db(at(f0 * (k + 1))) : -120));
  const amps = h.map((v) => 10 ** (v / 20));
  const brightness = amps.reduce((a, v, k) => a + (k + 1) * v, 0) / (amps.reduce((a, v) => a + v, 0) + 1e-12);
  let onHarmonics = 0;
  let all = 0;
  for (let k = Math.floor((f0 * 0.5) / bin); k < Math.min(mag.length, Math.ceil((f0 * 12.5) / bin)); k++) {
    const e = mag[k]! ** 2;
    all += e;
    const r = (k * bin) / f0;
    if (Math.abs(r - Math.round(r)) < 0.04 * Math.max(1, Math.round(r) / 4) && Math.round(r) >= 1) onHarmonics += e;
  }
  const loudest = Math.max(...h);
  const bandsRaw = BANDS.map((lo) => {
    let e = 0;
    for (let k = Math.floor(lo / bin); k < Math.min(mag.length, Math.floor((lo * 2) / bin)); k++) e += mag[k]! ** 2;
    return 10 * Math.log10(e + 1e-12);
  });
  const btop = Math.max(...bandsRaw);
  let logSum = 0;
  let sum = 0;
  let count = 0;
  for (let k = Math.floor(50 / bin); k < Math.min(mag.length, Math.floor(10000 / bin)); k++) {
    logSum += Math.log(mag[k]! + 1e-12);
    sum += mag[k]!;
    count++;
  }
  const flatness = Math.exp(logSum / count) / (sum / count + 1e-12);
  let rms = 0;
  for (let i = from; i < from + n; i++) rms += (src[i] ?? 0) ** 2;
  return {
    harmonics: h.map((v) => Math.max(-60, v - loudest)),
    bands: bandsRaw.map((v) => Math.max(-60, v - btop)),
    flatness,
    pitched,
    attack,
    fall,
    level: Math.sqrt(rms / n),
    brightness,
    harmonicity: onHarmonics / (all + 1e-12),
    f0,
  };
}

// ---- The families ------------------------------------------------------------

export interface Family {
  /** A VCSL sound or a Strudel synth. */
  readonly s: string;
  readonly kind: 'sample' | 'bank' | 'synth' | 'noise';
  /** More Strudel calls that make the sound: unison, vibrato, a filter envelope. */
  readonly chain?: string;
  /** Low-pass cutoff in harmonics of each note, for synths: it follows the pitch. */
  readonly harmonics?: number;
  /** A fixed low-pass cutoff in Hz. */
  readonly lpf?: number;
  /** The least attack and release in seconds, where the game's envelope is too abrupt for this sound. */
  readonly attack?: number;
  readonly release?: number;
  /** Times the game's own gain. */
  readonly level: number;
  readonly about: string;
}

export const FAMILIES = {
  strings: { s: 'supersaw', kind: 'synth', chain: '.unison(5).detune(0.12).spread(0.8).vib(5).vibmod(0.08)', harmonics: 3, attack: 0.12, release: 0.4, level: 1.3, about: 'A string section: detuned saws, filtered, with vibrato' },
  pad: { s: 'supersaw', kind: 'synth', chain: '.unison(4).detune(0.2).spread(0.9)', harmonics: 2, attack: 0.4, release: 1, level: 1.1, about: 'A slow synth pad' },
  choir: { s: 'supersaw', kind: 'synth', chain: ".unison(4).detune(0.1).spread(0.7).vowel('o').vib(4.5).vibmod(0.1)", harmonics: 6, attack: 0.2, release: 0.6, level: 1.6, about: 'A wordless choir: detuned saws through a vowel' },
  brass: { s: 'supersaw', kind: 'synth', chain: '.unison(3).detune(0.06).lpenv(2).lpattack(0.08).lpdecay(0.3).vib(5).vibmod(0.05)', harmonics: 4, attack: 0.03, level: 1.2, about: 'Brass: bright saws with a filter swell' },
  organ: { s: 'organ_8inch', kind: 'sample', level: 0.8, about: 'Organ (VCSL)' },
  flute: { s: 'recorder_alto_vib', kind: 'sample', attack: 0.03, level: 1, about: 'Recorder with vibrato (VCSL)' },
  lead: { s: 'ocarina_vib', kind: 'sample', attack: 0.04, release: 0.3, level: 1.1, about: 'Ocarina with vibrato (VCSL), for a sung lead line' },
  shimmer: { s: 'triangle', kind: 'synth', chain: '.vib(5).vibmod(0.12)', harmonics: 4, attack: 0.3, release: 1.2, level: 1.4, about: 'A soft, high, glassy pad' },
  piano: { s: 'steinway', kind: 'sample', level: 1, about: 'Grand piano (VCSL)' },
  harp: { s: 'harp', kind: 'sample', level: 1.2, about: 'Concert harp (VCSL), for plucks and pizzicato' },
  bell: { s: 'tubularbells', kind: 'sample', level: 0.8, about: 'Tubular bells (VCSL)' },
  vibes: { s: 'vibraphone', kind: 'sample', level: 1, about: 'Vibraphone (VCSL)' },
  glock: { s: 'glockenspiel', kind: 'sample', level: 0.7, about: 'Glockenspiel (VCSL)' },
  marimba: { s: 'marimba', kind: 'sample', level: 1, about: 'Marimba (VCSL)' },
  bass: { s: 'supersaw', kind: 'synth', chain: '.unison(2).detune(0.05)', harmonics: 2.5, attack: 0.01, release: 0.15, level: 1.5, about: 'A round synth bass' },
  'bass-pluck': { s: 'steinway', kind: 'sample', level: 1.2, about: 'Low piano, for plucked bass' },
  kick: { s: 'bassdrum1', kind: 'bank', level: 1, about: 'Bass drum (VCSL)' },
  snare: { s: 'snare_modern', kind: 'bank', level: 0.8, about: 'Snare (VCSL)' },
  hat: { s: 'hihat', kind: 'bank', level: 0.6, about: 'Hi-hat (VCSL)' },
  shaker: { s: 'shaker_small', kind: 'bank', level: 0.7, about: 'Shaker (VCSL)' },
  crash: { s: 'clash', kind: 'bank', level: 0.6, about: 'Clash cymbals (VCSL)' },
  cymbal: { s: 'sus_cymbal', kind: 'bank', level: 0.8, about: 'Suspended cymbal (VCSL)' },
  tom: { s: 'tom_mallet', kind: 'bank', level: 1, about: 'Tom (VCSL)' },
  timpani: { s: 'timpani', kind: 'bank', level: 1, about: 'Timpani (VCSL)' },
  gong: { s: 'gong', kind: 'bank', level: 0.8, about: 'Gong (VCSL)' },
  metal: { s: 'anvil', kind: 'bank', level: 0.6, about: 'Anvil (VCSL), for metal hits' },
  wind: { s: 'pink', kind: 'noise', lpf: 900, attack: 0.3, release: 0.8, level: 0.5, about: 'Filtered noise, for wind and air' },
} as const satisfies Record<string, Family>;
export type FamilyName = keyof typeof FAMILIES;

export interface Voice extends Family {
  readonly family: FamilyName;
  /** Why it was put in its family, for the page and the code's comments. */
  readonly heard: string;
}

/** How a program is used by the music: the keys it plays and how long its notes are, in seconds. */
export interface Use { readonly keys: readonly number[]; readonly seconds: readonly number[]; readonly bends: number }

const median = (xs: readonly number[]) => (xs.length ? [...xs].sort((a, b) => a - b)[Math.floor(xs.length / 2)]! : NaN);

/** The family of one game sample, from what it measures as and how its program is played. */
export function sort(t: Timbre, sustains: boolean, kit: boolean, use: Use): { family: FamilyName; heard: string } {
  const key = median(use.keys);
  const long = median(use.seconds);
  const unpitched = t.flatness > 0.3 || (t.pitched < 0.4 && t.flatness > 0.2) || t.harmonicity < 0.15;
  const say = (family: FamilyName, why: string) => ({ family, heard: why });
  if (unpitched || (kit && t.pitched < 0.7)) {
    const [low, , , mid1, mid2, mid3, high1, high2] = [t.bands[0]!, t.bands[1]!, t.bands[2]!, t.bands[3]!, t.bands[4]!, t.bands[5]!, t.bands[6]!, t.bands[7]!];
    const lowE = Math.max(low, t.bands[1]!, t.bands[2]!);
    const midE = Math.max(mid1, mid2, mid3);
    const highE = Math.max(high1, high2, t.bands[8]!);
    if (t.fall === Infinity && sustains) return say('wind', 'unpitched and held: a drone or air');
    if (t.fall > 2.5) return say(lowE > highE ? 'gong' : 'cymbal', `unpitched, rings for ${t.fall.toFixed(1)} s`);
    if (lowE >= midE && lowE >= highE) return say(t.fall < 0.6 ? 'kick' : 'timpani', `unpitched, low, falls in ${t.fall.toFixed(2)} s`);
    if (highE > midE + 3) return say(t.fall < 0.3 ? (t.fall < 0.12 ? 'hat' : 'shaker') : t.fall < 1.5 ? 'crash' : 'cymbal', `unpitched, high, falls in ${t.fall === Infinity ? 'never' : `${t.fall.toFixed(2)} s`}`);
    if (t.pitched > 0.3) return say(t.fall < 0.5 ? 'tom' : 'metal', 'unpitched but ringing, in the middle');
    return say('snare', 'unpitched noise in the middle');
  }
  if (t.harmonicity < 0.55 && !sustains) {
    if (key < 50) return say('timpani', `low, partials off the harmonics (${t.harmonicity.toFixed(2)}): a drum with a pitch`);
    return say(key >= 76 ? 'glock' : key >= 60 ? 'vibes' : 'bell', `partials off the harmonics (${t.harmonicity.toFixed(2)}): struck metal`);
  }
  if (key < 48) return say(sustains ? 'bass' : 'bass-pluck', `plays low (around ${noteOf(key)})`);
  // A slow swell is a pad, whatever its envelope does after; so are very long notes.
  if (t.attack > 0.6 || long > 4) return say(key >= 80 ? 'shimmer' : 'pad', t.attack > 0.6 ? `swells in over ${t.attack.toFixed(1)} s` : `notes of ${long.toFixed(1)} s: a held chord`);
  // A held sound playing quick notes, an arpeggio, is heard as plucked.
  if (sustains && long < 0.35) return say('harp', `held, but plays quick notes (${long.toFixed(2)} s): an arpeggio`);
  // A held line that bends its pitch is a sung lead.
  if (sustains && use.bends >= 4) return say('lead', `held, bends its pitch ${use.bends} times: a lead line`);
  if (!sustains) {
    if (t.fall < 0.35 || long < 0.15) return say(key >= 72 && t.harmonicity < 0.75 ? 'marimba' : 'harp', `short notes that die fast (${t.fall.toFixed(2)} s)`);
    return say('piano', `struck, falls in ${t.fall === Infinity ? 'its own time' : `${t.fall.toFixed(2)} s`}`);
  }
  if (t.attack > 0.08) return say(t.brightness > 2.2 && key >= 60 && key < 76 ? 'choir' : 'strings', `held, swells in over ${t.attack.toFixed(2)} s`);
  if (t.brightness > 2.6 && key < 72) return say('brass', `held, bright (${t.brightness.toFixed(1)})`);
  if (t.brightness > 2.6) return say('strings', `held, bright and high (${t.brightness.toFixed(1)})`);
  if (key < 67 && long < 1.5) return say('piano', `held, starts at once, dull, notes of ${long.toFixed(2)} s`);
  return say(key >= 67 ? 'flute' : 'organ', `held, starts at once, ${t.brightness.toFixed(1)} bright`);
}

const NAMES = ['c', 'db', 'd', 'eb', 'e', 'f', 'gb', 'g', 'ab', 'a', 'bb', 'b'];
const noteOf = (m: number) => (Number.isNaN(m) ? '?' : `${NAMES[Math.round(m) % 12]}${Math.floor(Math.round(m) / 12) - 1}`);

/** Each program's keys and note lengths across a file's sequences. */
function uses(music: Music): Map<number, { keys: number[]; seconds: number[]; bends: number }> {
  const out = new Map<number, { keys: number[]; seconds: number[]; bends: number }>();
  for (const seq of music.sequences) {
    const program = new Map<number, number>();
    for (const e of seq.events) {
      if (e.kind === 'program') program.set(e.channel, e.program);
      if (e.kind === 'bend' && e.value !== 0) {
        const p = program.get(e.channel) ?? 0;
        (out.get(p) ?? out.set(p, { keys: [], seconds: [], bends: 0 }).get(p)!).bends++;
      }
      if (e.kind !== 'note') continue;
      const p = program.get(e.channel) ?? 0;
      const u = out.get(p) ?? out.set(p, { keys: [], seconds: [], bends: 0 }).get(p)!;
      u.keys.push(e.key);
      u.seconds.push((e.length / seq.ppq) * (seq.usPerQuarter / 1e6));
    }
  }
  return out;
}

if (process.argv[1] === fileURLToPath(import.meta.url)) {
  const [input, cache, out] = process.argv.slice(2);
  if (!input || !cache || !out) {
    console.error('usage: node tools/rebecca/music/re1-voices.ts <rae music dir> <cache dir> <voices.json>');
    process.exit(2);
  }
  mkdirSync(cache, { recursive: true });
  const fixFile = path.join(path.dirname(fileURLToPath(import.meta.url)), 're1-voices.fix.json');
  const fixes = (existsSync(fixFile) ? JSON.parse(readFileSync(fixFile, 'utf8')) : {}) as Record<string, FamilyName>;
  for (const [k, f] of Object.entries(fixes)) if (!(f in FAMILIES)) throw new Error(`${fixFile}: ${k} names ${f}, which is not a family`);
  const voices: Record<string, Voice> = {};
  for (const file of readdirSync(input).filter((f) => /^SEP[0-9A-F]{2}\.json$/.test(f)).sort()) {
    const music = JSON.parse(readFileSync(path.join(input, file), 'utf8')) as Music;
    const used = uses(music);
    for (const program of music.bank.programs) {
      const kit = program.tones.some((t) => t.minKey === t.maxKey);
      const use = used.get(program.index) ?? { keys: [], seconds: [], bends: 0 };
      // One family for an instrument recorded at several keys, from its middle tone; a kit sorts each drum.
      const sorted = new Map<number, { family: FamilyName; heard: string }>();
      for (const tone of program.tones) {
        const sample = music.samples[tone.sample];
        if (!sample) continue;
        const { x, rate } = readWav(readFileSync(path.join(input, sample.file)));
        if (x.length < 64) continue;
        // The sample sounds fine/128 of a semitone below its centre key; the SPU tunes it up by that.
        const f0 = 440 * 2 ** ((tone.center - tone.fine / 128 - 69) / 12);
        const sustains = sample.loop !== undefined && spuEnvelope(tone.adsr1, tone.adsr2).sustain > 0;
        const mine = kit ? { keys: [tone.minKey], seconds: use.seconds, bends: 0 } : use;
        sorted.set(tone.sample, sort(measure(x, rate, f0, sample.loop?.start), sustains, kit, mine));
      }
      const middle = program.tones[Math.floor(program.tones.length / 2)];
      program.tones.forEach((tone, i) => {
        const mine = sorted.get(tone.sample);
        if (!mine) return;
        const pid = `${file.slice(0, 5)}/p${program.index}`;
        const id = `${pid}t${i}`;
        const pick = kit ? mine : (sorted.get(middle!.sample) ?? mine);
        const fixed = fixes[id] ?? fixes[pid];
        voices[id] = { ...FAMILIES[fixed ?? pick.family], family: fixed ?? pick.family, heard: fixed ? 'set by ear' : pick.heard };
      });
    }
  }
  writeFileSync(out, JSON.stringify(voices, null, 1));
  const counts = new Map<string, number>();
  for (const v of Object.values(voices)) counts.set(v.family, (counts.get(v.family) ?? 0) + 1);
  console.log(`${Object.keys(voices).length} instrument tones sorted:`, [...counts].sort((a, b) => b[1] - a[1]).map(([s, n]) => `${s} ${n}`).join(', '));
}
