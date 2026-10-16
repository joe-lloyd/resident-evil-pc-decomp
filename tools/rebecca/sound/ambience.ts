// The loops that play under her music, one for each kind of place: the gale
// round the gondola, the forest, the mine, the valley at dusk, the estate at
// night, the cellar. Made by code from noise and a few synthesised calls, as
// footsteps.ts makes her steps, so they are ours to ship and come out the
// same every build.
//
// Each loop is LOOP seconds that join end to start without a seam: the
// continuous bed is rendered a little long and its tail crossfaded into its
// head, and the short events (a bird, a drip, a creak) are laid round the
// loop so one that runs past the end comes back in at the start. They sit
// near RE1's own ambience (its insects loop, Se_03, measures -37 dB RMS) and
// about 12 dB under the music (-24 dB, docs/REBECCA_MUSIC.md), so they stay
// under it. A cue's channel names its loop (plan/music.ts Channel.loop), and
// the game plays it as one of the cue's music channels (music/table.ts).
import { wav } from '../footsteps.ts';

const RATE = 22050;
/** Seconds in a loop. The mill's wheel turns ten times in it. */
export const LOOP = 24;
const N = RATE * LOOP;
/** The crossfade that joins the bed's end to its start. */
const FADE = RATE * 2;

/** A small seeded random number generator (mulberry32), so a build is repeatable. */
function random(seed: number): () => number {
  let a = seed >>> 0;
  return () => {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

const white = (rnd: () => number, n: number) => Float32Array.from({ length: n }, () => rnd() * 2 - 1);

/** A slow wandering control between 0 and 1: a few sines whose periods divide the loop, so it repeats with it. */
function drift(rnd: () => number, cycles: readonly number[]): (i: number) => number {
  const parts = cycles.map((c) => ({ c, phase: rnd() * Math.PI * 2, w: 0.5 + rnd() }));
  const total = parts.reduce((s, p) => s + p.w, 0);
  return (i) => 0.5 + 0.5 * parts.reduce((s, p) => s + p.w * Math.sin((2 * Math.PI * p.c * i) / N + p.phase), 0) / total;
}

/** One-pole low-pass, in place. */
function lowpass(x: Float32Array, hz: number): Float32Array {
  const k = 1 - Math.exp((-2 * Math.PI * hz) / RATE);
  let y = 0;
  for (let i = 0; i < x.length; i++) x[i] = y += k * (x[i]! - y);
  return x;
}

/** One-pole high-pass, in place. */
function highpass(x: Float32Array, hz: number): Float32Array {
  const k = 1 - Math.exp((-2 * Math.PI * hz) / RATE);
  let y = 0;
  for (let i = 0; i < x.length; i++) {
    y += k * (x[i]! - y);
    x[i] = x[i]! - y;
  }
  return x;
}

/** A band-pass (RBJ, constant peak gain) whose centre moves with `hz(i)`, in place. */
function bandpass(x: Float32Array, hz: (i: number) => number, q: number): Float32Array {
  let x1 = 0, x2 = 0, y1 = 0, y2 = 0;
  let b0 = 0, a1 = 0, a2 = 0;
  for (let i = 0; i < x.length; i++) {
    if (i % 32 === 0) {
      const w = (2 * Math.PI * hz(i)) / RATE;
      const alpha = Math.sin(w) / (2 * q);
      const a0 = 1 + alpha;
      b0 = alpha / a0;
      a1 = (-2 * Math.cos(w)) / a0;
      a2 = (1 - alpha) / a0;
    }
    const x0 = x[i]!;
    const y0 = b0 * x0 - b0 * x2 - a1 * y1 - a2 * y2;
    x2 = x1;
    x1 = x0;
    y2 = y1;
    y1 = y0;
    x[i] = y0;
  }
  return x;
}

/**
 * A continuous bed `make(n)` gives for n samples, joined into a seamless
 * loop: rendered FADE long, the extra tail crossfaded (equal power) into the head.
 */
function loopBed(make: (n: number) => Float32Array): Float32Array {
  const x = make(N + FADE);
  const out = x.slice(0, N);
  for (let i = 0; i < FADE; i++) {
    const t = i / FADE;
    out[i] = x[i]! * Math.sin((t * Math.PI) / 2) + x[N + i]! * Math.cos((t * Math.PI) / 2);
  }
  return out;
}

/** Add `ev` into the loop at sample `at`, wrapping past the end to the start. */
function place(out: Float32Array, ev: Float32Array, at: number, gain = 1): void {
  for (let j = 0; j < ev.length; j++) out[(at + j) % N]! += ev[j]! * gain;
}

/** A tone whose pitch `hz(t)` and level `amp(t)` follow t in seconds, for `len` seconds. */
function tone(len: number, hz: (t: number) => number, amp: (t: number) => number): Float32Array {
  const n = Math.round(len * RATE);
  const out = new Float32Array(n);
  let phase = 0;
  for (let i = 0; i < n; i++) {
    const t = i / RATE;
    phase += (2 * Math.PI * hz(t)) / RATE;
    out[i] = Math.sin(phase) * amp(t) * Math.min(1, t / 0.004, (len - t) / 0.004);
  }
  return out;
}

/** Echoes off rock or brick: copies of the sound later and quieter. */
function echoes(ev: Float32Array, taps: readonly (readonly [seconds: number, gain: number])[]): Float32Array {
  const end = Math.max(...taps.map(([s]) => s));
  const out = new Float32Array(ev.length + Math.round(end * RATE));
  out.set(ev);
  for (const [s, g] of taps) {
    const d = Math.round(s * RATE);
    for (let j = 0; j < ev.length; j++) out[d + j]! += ev[j]! * g;
  }
  return lowpass(out, 6000);
}

// --- The parts -------------------------------------------------------------

/** Wind: noise through a band that rises and opens as each gust builds, a low buffet under it, a thin whistle at the top. */
function wind(rnd: () => number, strength: number): Float32Array {
  const gust = drift(rnd, [1, 2, 3, 5, 7]);
  const level = (i: number) => 0.25 + 0.75 * Math.pow(gust(i % N), 1.6);
  return loopBed((n) => {
    const body = bandpass(white(rnd, n), (i) => 260 + 700 * strength * gust(i % N), 0.9);
    const buffet = lowpass(lowpass(white(rnd, n), 140), 140);
    const whistle = bandpass(white(rnd, n), (i) => 900 + 900 * gust(i % N), 18);
    const out = new Float32Array(n);
    for (let i = 0; i < n; i++) {
      const l = level(i);
      out[i] = body[i]! * l + buffet[i]! * 6 * l + whistle[i]! * 1.2 * strength * Math.pow(l, 3);
    }
    return out;
  });
}

/** Leaves stirring overhead: bright noise that swells with the wind and flutters fast. */
function leaves(rnd: () => number): Float32Array {
  const gust = drift(rnd, [2, 3, 4, 6]);
  return loopBed((n) => {
    const hiss = lowpass(highpass(white(rnd, n), 1800), 6500);
    const flutter = lowpass(white(rnd, n), 9);
    const out = new Float32Array(n);
    for (let i = 0; i < n; i++) out[i] = hiss[i]! * Math.pow(gust(i % N), 2) * (0.6 + 6 * Math.abs(flutter[i]!));
    return out;
  });
}

/** A small bird's call far off: a few quick rising chirps. */
function chirps(rnd: () => number): Float32Array {
  const notes = 2 + Math.floor(rnd() * 4);
  const base = 3000 + rnd() * 1500;
  const parts: Float32Array[] = [];
  for (let k = 0; k < notes; k++) {
    const len = 0.05 + rnd() * 0.06;
    const lift = 800 + rnd() * 900;
    parts.push(tone(len, (t) => base + lift * (t / len), (t) => Math.sin((Math.PI * t) / len)));
    parts.push(new Float32Array(Math.round((0.04 + rnd() * 0.06) * RATE)));
  }
  return concat(parts);
}

/** A thrush or a robin settling for the evening: two or three slow whistled notes with a wobble. */
function whistle(rnd: () => number): Float32Array {
  const parts: Float32Array[] = [];
  const notes = 2 + Math.floor(rnd() * 2);
  for (let k = 0; k < notes; k++) {
    const f = 1700 + rnd() * 900;
    const len = 0.18 + rnd() * 0.2;
    const bend = (rnd() - 0.5) * 500;
    parts.push(tone(len, (t) => f + bend * (t / len) + 40 * Math.sin(2 * Math.PI * 28 * t), (t) => Math.pow(Math.sin((Math.PI * t) / len), 0.7)));
    parts.push(new Float32Array(Math.round((0.12 + rnd() * 0.15) * RATE)));
  }
  return concat(parts);
}

/** An owl far off: hoo, a pause, hoo-hoo, falling a little. */
function owl(): Float32Array {
  const hoo = (len: number, f: number) => tone(len, (t) => f - 25 * (t / len), (t) => Math.pow(Math.sin((Math.PI * t) / len), 1.5));
  const gap = (s: number) => new Float32Array(Math.round(s * RATE));
  return lowpass(concat([hoo(0.45, 390), gap(0.35), hoo(0.22, 370), gap(0.12), hoo(0.5, 350)]), 1200);
}

/** One cricket's chirp: a few pulses of a high tone. */
function cricket(rnd: () => number, f: number): Float32Array {
  const pulses = 3 + Math.floor(rnd() * 2);
  const parts: Float32Array[] = [];
  for (let k = 0; k < pulses; k++) {
    parts.push(tone(0.016, () => f, (t) => Math.sin((Math.PI * t) / 0.016)));
    parts.push(new Float32Array(Math.round(0.014 * RATE)));
  }
  return concat(parts);
}

/** Crickets in the grass: `count` of them, each chirping at its own pace and pitch. */
function crickets(out: Float32Array, rnd: () => number, count: number, every: number, gain: number): void {
  for (let c = 0; c < count; c++) {
    const f = 3900 + rnd() * 900;
    const pace = every * (0.8 + rnd() * 0.5);
    const g = gain * (0.4 + rnd() * 0.6);
    let rest = 0;
    for (let t = rnd() * pace; t < LOOP; t += pace * (0.9 + rnd() * 0.2)) {
      // Now and then one falls quiet for a few chirps.
      if (rest > 0) {
        rest--;
        continue;
      }
      if (rnd() < 0.06) rest = 2 + Math.floor(rnd() * 5);
      place(out, cricket(rnd, f), Math.round(t * RATE), g);
    }
  }
}

/** A drop of water into a pool: a plink that rises as the bubble closes. */
function drip(rnd: () => number): Float32Array {
  const f = 1100 + rnd() * 1500;
  const d = 0.025 + rnd() * 0.03;
  return tone(0.12, (t) => f * (1 + 0.6 * (1 - Math.exp(-t / 0.012))), (t) => Math.exp(-t / d));
}

/** Timber taking a weight: a slow rough squeal, rising and falling. */
function creak(rnd: () => number, low: number): Float32Array {
  const len = 0.35 + rnd() * 0.5;
  const f = low * (1 + rnd() * 0.6);
  // The squeal's pitch jitters as the wood sticks and slips.
  const jitter = lowpass(white(random(Math.floor(rnd() * 1e9)), Math.round(len * RATE) + 1), 60);
  const pitch = (t: number) => f * (1 + 0.25 * Math.sin((Math.PI * t) / len) + 2 * jitter[Math.round(t * RATE)]!);
  const level = (t: number) => Math.pow(Math.sin((Math.PI * t) / len), 0.6) * (0.6 + 0.4 * Math.sin(2 * Math.PI * 23 * t));
  return lowpass(tone(len, pitch, level), 1800);
}

/** The low air of a place underground or shut in: a rumble you hear more than notice. */
function roomTone(rnd: () => number, hz: number): Float32Array {
  return loopBed((n) => lowpass(lowpass(white(rnd, n), hz), hz));
}

function concat(parts: readonly Float32Array[]): Float32Array {
  const out = new Float32Array(parts.reduce((s, p) => s + p.length, 0));
  let at = 0;
  for (const p of parts) {
    out.set(p, at);
    at += p.length;
  }
  return out;
}

/** `x` scaled so its RMS sits `db` from the bed's reference level (1.0). */
function bed(x: Float32Array, db: number): Float32Array {
  let sum = 0;
  for (const v of x) sum += v * v;
  const g = 10 ** (db / 20) / (Math.sqrt(sum / x.length) || 1);
  return x.map((v) => v * g);
}

/** `x` scaled so its peak sits `db` from the bed's reference level: an event over the bed. */
function peakAt(x: Float32Array, db: number): Float32Array {
  const peak = x.reduce((m, v) => Math.max(m, Math.abs(v)), 0) || 1;
  const g = 10 ** (db / 20) / peak;
  return x.map((v) => v * g);
}

function mix(...layers: readonly Float32Array[]): Float32Array {
  const out = new Float32Array(N);
  for (const x of layers) for (let i = 0; i < N; i++) out[i]! += x[i]!;
  return out;
}

/** Events at random times round the loop, about `every` seconds apart, each `make` gives at a peak `db` from the bed. */
function scatter(out: Float32Array, rnd: () => number, every: number, make: () => Float32Array, db: () => number): void {
  for (let t = rnd() * every; t < LOOP; t += every * (0.5 + rnd())) place(out, peakAt(make(), db()), Math.round(t * RATE));
}

// --- The places --------------------------------------------------------------
// Levels are in dB from the bed's reference: a bed at 0 is the loop's body,
// an event's peak at +10 stands well clear of it.

// A loop carries only what no music channel of its cue carries
// (docs/REBECCA_SOUND.md): the station's music has the wind, so the forest is
// leaves and birds; the mine's music has the drips and the water, so the mine
// is its air and timber.
export const AMBIENCES = ['gale', 'forest', 'mine', 'dusk', 'night', 'cellar'] as const;
export type Ambience = (typeof AMBIENCES)[number];

/** Each loop's seed, fixed, so the loops whose recipe stays the same sound the same. */
const SEED: Record<Ambience, number> = { gale: 1, forest: 2, mine: 4, dusk: 5, night: 6, cellar: 7 };

const MAKE: Record<Ambience, (rnd: () => number) => Float32Array> = {
  // High and exposed, round the gondola car and the pylon: hard wind, with a whistle.
  gale: (rnd) => wind(rnd, 1),
  // Under the trees: the leaves stirring, small birds far off.
  forest: (rnd) => {
    const out = mix(bed(leaves(rnd), 0));
    scatter(out, rnd, 4.5, () => lowpass(chirps(rnd), 5000), () => 4 + rnd() * 6);
    return out;
  },
  // Underground: the close air, timber taking the weight now and then.
  mine: (rnd) => {
    const out = mix(bed(roomTone(rnd, 90), 0));
    scatter(out, rnd, 7, () => creak(rnd, 150), () => 6);
    return out;
  },
  // The valley at dusk: crickets starting up, a breeze, a bird settling.
  dusk: (rnd) => {
    const out = mix(bed(wind(rnd, 0.25), -4));
    crickets(out, rnd, 5, 0.8, 10 ** (4 / 20));
    scatter(out, rnd, 9, () => lowpass(whistle(rnd), 4000), () => 7);
    return out;
  },
  // The estate at night: a few crickets, the wind in the hedges, an owl.
  night: (rnd) => {
    const out = mix(bed(wind(rnd, 0.3), -2));
    crickets(out, rnd, 3, 1.1, 10 ** (1 / 20));
    place(out, peakAt(owl(), 9), Math.round(5 * RATE));
    place(out, peakAt(owl(), 6), Math.round(17.5 * RATE));
    return out;
  },
  // Under the house: close air, slow drips in the dark, boards above.
  cellar: (rnd) => {
    const out = mix(bed(roomTone(rnd, 140), 0));
    scatter(out, rnd, 3.2, () => echoes(drip(rnd), [[0.05, 0.3], [0.11, 0.15]]), () => 8 + rnd() * 6);
    scatter(out, rnd, 8, () => creak(rnd, 220), () => 5);
    return out;
  },
};

/** Where the loops sit: dB RMS, and the highest peak allowed. */
const TARGET_RMS = -36;
const PEAK_MAX = -12;

/** One loop, levelled: its RMS at TARGET_RMS unless that would push a peak past PEAK_MAX. */
export function ambience(kind: Ambience): Float32Array {
  const x = MAKE[kind](random(0xa3b1 + SEED[kind]));
  let sum = 0;
  let peak = 0;
  for (const v of x) {
    sum += v * v;
    peak = Math.max(peak, Math.abs(v));
  }
  const rms = Math.sqrt(sum / x.length) || 1;
  const gain = Math.min(10 ** (TARGET_RMS / 20) / rms, 10 ** (PEAK_MAX / 20) / (peak || 1));
  for (let i = 0; i < x.length; i++) x[i] = x[i]! * gain;
  return x;
}

/** The WAV a loop ships as, without .wav. */
export const ambienceFile = (kind: Ambience) => `Reb_amb_${kind}`;

export function ambienceFiles(kinds: readonly Ambience[]): { name: string; bytes: Uint8Array }[] {
  return kinds.map((k) => ({ name: `${ambienceFile(k)}.wav`, bytes: wav(ambience(k)) }));
}
