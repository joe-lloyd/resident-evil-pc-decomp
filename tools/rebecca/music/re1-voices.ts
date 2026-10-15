// Pick a free sound for each of RE1's instrument samples, so the RE1 tracks
// can also play on sounds we may use: VCSL (CC0) or Strudel's own synths.
// Nothing here is chosen by ear. Each game sample is measured: its harmonics,
// how noisy it is, how bright, how its level moves. One sample of every VCSL
// instrument is measured the same way, and the synths are worked out from
// their waveforms. The nearest wins, through the low-pass filter that brings
// it closest, so the filter becomes the voice's .lpf().
//
//   node tools/rebecca/music/re1-voices.ts <rae music dir> <cache dir> <voices.json>
//
// The cache gets one WAV per VCSL instrument from the pinned commit.
// voices.json maps "SEPxx/sNN" to the chosen sound, for re1.ts --free. A
// sound tried by ear and found wrong goes in re1-voices.fix.json beside this
// file, which wins over the measurement.
import { existsSync, mkdirSync, readFileSync, readdirSync, writeFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { spuEnvelope, type Music } from './re1.ts';

export const VCSL = 'https://raw.githubusercontent.com/felixroos/dough-samples/9eacfc86ec4393e68a463ff52b01c19cfaa77f38/vcsl.json';

export interface Voice {
  /** A VCSL sound or a Strudel synth. */
  readonly s: string;
  readonly kind: 'pitched' | 'bank' | 'synth' | 'noise';
  /** Low-pass cutoff in Hz at the game sample's centre key, or none. */
  readonly lpf?: number;
  /** For a pitched sound: the cutoff in harmonics of each note, so it follows the pitch as the game's samples do. */
  readonly harmonics?: number;
  /** Times the game's own gain, to match the game sample's level. */
  readonly gain: number;
  /** How far the measurements are apart: 0 is the same. */
  readonly distance: number;
  /** What the game sample measured as, for the page. */
  readonly heard: string;
}

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
  /** How strongly it repeats at its expected period: near 1 for a pitched sound. */
  readonly pitched: number;
  /** Seconds to its peak, and from the peak down 20 dB (Infinity if it never falls that far). */
  readonly attack: number;
  readonly fall: number;
  /** RMS of the steady part, as the sample stands. */
  readonly level: number;
}

/**
 * Measure a sound around its steady part: from `steady` (a sample index) or
 * from 60 ms after its peak. `f0` is where its fundamental should be.
 */
export function measure(x: Float32Array, rate: number, f0: number, steady?: number): Timbre {
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
  const fall = fallAt < 0 ? Infinity : ((fallAt - peakAt) * frame) / rate;
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
  const mag = spectrum(src, from, n);
  const bin = rate / n;
  const at = (hz: number) => {
    let m = 0;
    for (let k = Math.floor((hz * 0.97) / bin); k <= Math.ceil((hz * 1.03) / bin) && k < mag.length; k++) m = Math.max(m, mag[k]!);
    return m;
  };
  const h = Array.from({ length: HARMONICS }, (_, k) => (f0 * (k + 1) < rate / 2 ? db(at(f0 * (k + 1))) : -120));
  const top = Math.max(...h);
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
  // The best normalised autocorrelation within 6% of the expected period.
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
  const period = rate / f0;
  let pitched = -1;
  for (let lag = Math.max(2, Math.floor(period * 0.94)); lag <= Math.ceil(period * 1.06); lag++) pitched = Math.max(pitched, corr(lag));
  let rms = 0;
  for (let i = from; i < from + n; i++) rms += (src[i] ?? 0) ** 2;
  return {
    harmonics: h.map((v) => Math.max(-60, v - top)),
    bands: bandsRaw.map((v) => Math.max(-60, v - btop)),
    flatness,
    pitched,
    attack,
    fall,
    level: Math.sqrt(rms / n),
  };
}

// ---- The free sounds ---------------------------------------------------------

/** dB of Strudel's low-pass (a biquad, Q 1) at `f` for cutoff `fc`. */
const lowpass = (f: number, fc: number) => -10 * Math.log10((1 - (f / fc) ** 2) ** 2 + (f / fc) ** 2);

/** Strudel's synths as harmonic levels (dB of harmonic k) and RMS at gain 1 (0.3 times the waveform). */
const SYNTHS: Record<string, { harmonic: (k: number) => number; rms: number }> = {
  sawtooth: { harmonic: (k) => db(1 / k), rms: 0.3 * 0.577 },
  square: { harmonic: (k) => (k % 2 ? db(1 / k) : -120), rms: 0.3 },
  triangle: { harmonic: (k) => (k % 2 ? db(1 / k ** 2) : -120), rms: 0.3 * 0.577 },
  sine: { harmonic: (k) => (k === 1 ? 0 : -120), rms: 0.3 * 0.707 },
};
/** The noises' octave-band slopes in dB per octave. */
const NOISES: Record<string, number> = { white: 3, pink: 0, brown: -3 };
const CUTOFFS = [1, 1.5, 2, 3, 4, 6, 8, 12, 16, 24, Infinity];
/** For unpitched sounds the cutoff is in Hz, not harmonics. */
const DRUM_CUTOFFS = [250, 500, 1000, 2000, 4000, 8000, Infinity];
/** A cutoff above this is no cutoff. */
const OPEN = 16000;

const weights = Array.from({ length: HARMONICS }, (_, k) => 1 / Math.sqrt(k + 1));
const harmonicDistance = (a: readonly number[], b: readonly number[]) => {
  const top = Math.max(...b);
  let d = 0;
  let w = 0;
  for (let k = 0; k < HARMONICS; k++) {
    d += weights[k]! * Math.abs(a[k]! - Math.max(-60, b[k]! - top));
    w += weights[k]!;
  }
  return d / w;
};
const bandDistance = (a: readonly number[], b: readonly number[]) => {
  const top = Math.max(...b);
  return a.reduce((s, v, i) => s + Math.abs(v - Math.max(-60, b[i]! - top)), 0) / a.length;
};
/** Seconds as a log ratio, so 0.1 s against 0.2 s weighs as 1 s against 2 s. */
const timeDistance = (a: number, b: number) => Math.abs(Math.log2(Math.min(a, 8) + 0.05) - Math.log2(Math.min(b, 8) + 0.05));

interface Candidate { s: string; kind: Voice['kind']; t?: Timbre; f0?: number }

/** One file per VCSL instrument: the pitched ones nearest middle C, the banks' first. */
async function vcslCandidates(cache: string): Promise<Candidate[]> {
  mkdirSync(cache, { recursive: true });
  const mapFile = path.join(cache, 'vcsl.json');
  if (!existsSync(mapFile)) writeFileSync(mapFile, Buffer.from(await (await fetch(VCSL)).arrayBuffer()));
  const map = JSON.parse(readFileSync(mapFile, 'utf8')) as Record<string, string | string[] | Record<string, string | string[]>>;
  const first = (u: string | string[]) => (Array.isArray(u) ? u[0]! : u);
  const base = map._base as string;
  const out: Candidate[] = [];
  for (const [name, v] of Object.entries(map)) {
    if (name.startsWith('_')) continue;
    const pitched = !Array.isArray(v);
    const [key, url] = pitched
      ? Object.entries(v as Record<string, string | string[]>).map(([k, u]) => [k, first(u)] as const).sort((a, b) => Math.abs(midi(a[0]) - 60) - Math.abs(midi(b[0]) - 60))[0]!
      : ['c3', (v as string[])[0]!];
    if (!url.toLowerCase().endsWith('.wav')) continue;
    const file = path.join(cache, `${name}.wav`);
    if (!existsSync(file)) {
      const r = await fetch(base + url);
      if (!r.ok) continue;
      writeFileSync(file, Buffer.from(await r.arrayBuffer()));
    }
    try {
      const { x, rate } = readWav(readFileSync(file));
      const f0 = 440 * 2 ** ((midi(key) - 69) / 12);
      out.push({ s: name, kind: pitched ? 'pitched' : 'bank', t: measure(x, rate, f0), f0 });
    } catch {
      // A file that won't read is left out.
    }
  }
  return out;
}

const NAMES: Record<string, number> = { c: 0, d: 2, e: 4, f: 5, g: 7, a: 9, b: 11 };
function midi(note: string): number {
  const m = note.toLowerCase().match(/^([a-g])(#|b|s)?(-?\d+)$/);
  if (!m) throw new Error(`not a note: ${note}`);
  return (Number(m[3]) + 1) * 12 + NAMES[m[1]!]! + (m[2] === '#' || m[2] === 's' ? 1 : m[2] === 'b' ? -1 : 0);
}

/** Every free sound for one game sample, each through its best filter, nearest first. */
export function options(target: Timbre, f0: number, sustains: boolean, pool: readonly Candidate[]): Voice[] {
  const unpitched = target.flatness > 0.3 || target.pitched < 0.4;
  const heard = `${unpitched ? 'unpitched' : 'pitched'}, ${sustains ? 'held' : target.fall === Infinity ? 'rings on' : `falls 20 dB in ${target.fall.toFixed(2)} s`}, noise ${target.flatness.toFixed(2)}`;
  const best = new Map<string, Voice>();
  const consider = (v: Omit<Voice, 'heard'>) => {
    const was = best.get(v.s);
    if (!was || v.distance < was.distance) best.set(v.s, { ...v, heard });
  };
  const cut = (hz: number) => (hz >= OPEN ? undefined : Math.round(hz));
  if (unpitched) {
    for (const c of pool) {
      if (!c.t || c.kind !== 'bank') continue;
      for (const fc of DRUM_CUTOFFS) {
        const bands = c.t.bands.map((v, i) => v + (fc === Infinity ? 0 : lowpass(BANDS[i]! * 1.41, fc)));
        const d = bandDistance(target.bands, bands) + 8 * Math.abs(target.flatness - c.t.flatness) + 4 * timeDistance(target.fall, c.t.fall);
        consider({ s: c.s, kind: 'bank', lpf: cut(fc), gain: target.level / Math.max(c.t.level, 1e-4), distance: d });
      }
    }
    for (const [s, slope] of Object.entries(NOISES)) {
      for (const fc of DRUM_CUTOFFS) {
        const bands = BANDS.map((lo, i) => i * slope + (fc === Infinity ? 0 : lowpass(lo * 1.41, fc)));
        // Noise holds as long as the note: its fall comes from the game's own envelope.
        const d = bandDistance(target.bands, bands) + 8 * Math.abs(target.flatness - 0.9);
        consider({ s, kind: 'noise', lpf: cut(fc), gain: target.level / 0.1, distance: d });
      }
    }
  } else {
    for (const c of pool) {
      if (!c.t || c.kind !== 'pitched' || c.t.pitched < 0.6) continue;
      // A sample that dies away can't hold a note the game holds.
      const dies = c.t.fall < 1.5;
      const penalty = (sustains && dies ? 6 : 0) + (!sustains ? 2 * timeDistance(target.fall, c.t.fall) : 0) + 2 * timeDistance(target.attack, c.t.attack);
      for (const mult of CUTOFFS) {
        const h = c.t.harmonics.map((v, k) => v + (mult === Infinity ? 0 : lowpass(k + 1, mult)));
        consider({ s: c.s, kind: 'pitched', lpf: cut(mult * f0), harmonics: mult === Infinity ? undefined : mult, gain: target.level / Math.max(c.t.level, 1e-4), distance: harmonicDistance(target.harmonics, h) + penalty });
      }
    }
    for (const [s, synth] of Object.entries(SYNTHS)) {
      for (const mult of CUTOFFS) {
        const h = Array.from({ length: HARMONICS }, (_, k) => synth.harmonic(k + 1) + (mult === Infinity ? 0 : lowpass(k + 1, mult)));
        // The filter takes level off: the harmonics' energy through it against without.
        const kept = Math.sqrt(h.reduce((a, v) => a + 10 ** (v / 10), 0) / Array.from({ length: HARMONICS }, (_, k) => synth.harmonic(k + 1)).reduce((a, v) => a + 10 ** (v / 10), 0));
        // A synth holds forever and takes the game's envelope, so it can play anything; a
        // recorded instrument that is nearly as close sounds more like one, so it wins a tie.
        consider({ s, kind: 'synth', lpf: cut(mult * f0), harmonics: mult === Infinity ? undefined : mult, gain: target.level / (synth.rms * kept), distance: harmonicDistance(target.harmonics, h) + (sustains ? 1 : 3) });
      }
    }
  }
  return [...best.values()]
    .map((v) => ({ ...v, gain: Math.round(Math.min(4, Math.max(0.05, v.gain)) * 100) / 100, distance: Math.round(v.distance * 10) / 10 }))
    .sort((a, b) => a.distance - b.distance);
}

if (process.argv[1] === fileURLToPath(import.meta.url)) {
  const [input, cache, out] = process.argv.slice(2);
  if (!input || !cache || !out) {
    console.error('usage: node tools/rebecca/music/re1-voices.ts <rae music dir> <cache dir> <voices.json>');
    process.exit(2);
  }
  const pool = await vcslCandidates(cache);
  console.log(`${pool.length} VCSL instruments measured`);
  const voices: Record<string, Voice> = {};
  for (const file of readdirSync(input).filter((f) => /^SEP[0-9A-F]{2}\.json$/.test(f)).sort()) {
    const music = JSON.parse(readFileSync(path.join(input, file), 'utf8')) as Music;
    const scored = new Map<number, Voice[]>();
    for (const sample of music.samples) {
      const tone = music.bank.programs.flatMap((p) => p.tones).find((t) => t.sample === sample.index);
      if (!tone) continue;
      const { x, rate } = readWav(readFileSync(path.join(input, sample.file)));
      if (x.length < 64) continue;
      const f0 = 440 * 2 ** ((tone.center + tone.fine / 128 - 69) / 12);
      // Held when the sample loops and the game's envelope keeps it sounding; a looped sample
      // whose envelope fades while the key is down plays like a struck or plucked note.
      const sustains = sample.loop !== undefined && spuEnvelope(tone.adsr1, tone.adsr2).sustain > 0;
      scored.set(sample.index, options(measure(x, rate, f0, sample.loop?.start), f0, sustains, pool));
    }
    // An instrument recorded at several keys gets one free sound across all of them, the one
    // nearest over the lot, so a tune doesn't change instrument at a key split. A drum kit
    // (a tone per key) keeps a sound per drum.
    for (const program of music.bank.programs) {
      const tones = program.tones.filter((t) => scored.has(t.sample));
      const kit = tones.some((t) => t.minKey === t.maxKey);
      for (const t of tones) {
        const key = music.samples[t.sample]!.file.replace(/\.wav$/, '');
        if (voices[key]) continue;
        const mine = scored.get(t.sample)!;
        if (kit || tones.length < 2) {
          voices[key] = mine[0]!;
          continue;
        }
        const total = (s: string) => tones.reduce((a, o) => a + (scored.get(o.sample)!.find((v) => v.s === s)?.distance ?? 99), 0);
        const pick = [...new Set(tones.flatMap((o) => scored.get(o.sample)!.slice(0, 8).map((v) => v.s)))].sort((a, b) => total(a) - total(b))[0]!;
        voices[key] = mine.find((v) => v.s === pick) ?? mine[0]!;
      }
    }
  }
  writeFileSync(out, JSON.stringify(voices, null, 1));
  const counts = new Map<string, number>();
  for (const v of Object.values(voices)) counts.set(v.s, (counts.get(v.s) ?? 0) + 1);
  console.log(`${Object.keys(voices).length} samples matched:`, [...counts].sort((a, b) => b[1] - a[1]).map(([s, n]) => `${s} ${n}`).join(', '));
}
