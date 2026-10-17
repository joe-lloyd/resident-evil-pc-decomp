// Footsteps made from noise rather than taken from the game: a soft heel
// thump under a burst of crackle, as a boot settles on grit and dry needles.
// - Two on a forest path, one per foot, for the walk between Rebecca's
//   outdoor rooms (src/game/PathWalk.cpp plays them from room sound slots 0
//   and 1).
// - Her steps on earth and on gravel in her rooms, walking and running
//   (sound/ground.ts): RE1 has no footsteps for either.
// WAV, 22050 Hz, 16-bit mono, as the game's own sounds are.

const RATE = 22050;

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

/** How a step sounds: the ground under it and the pace. */
export interface StepRecipe {
  /** Length in seconds. */
  readonly length: number;
  /** The heel thump's level. */
  readonly thump: number;
  /** Grains of grit in the crunch, and the share of them under the toe. */
  readonly grains: number;
  readonly toe: number;
  /** When the toe comes down after the heel, in seconds. */
  readonly toeAt: number;
  /** The grains' lowest pitch in Hz, and how much higher they go. */
  readonly low: number;
  readonly spread: number;
  /** Each grain's level, at the least, and how much louder it may be. */
  readonly grain: number;
  readonly grainSpread: number;
  /** The one-pole low-pass's coefficient: lower is duller. */
  readonly smooth: number;
  /** The peak the step is normalised to. */
  readonly peak: number;
}

/** Grit and dry needles on a forest path: the walk's steps. */
export const PATH: StepRecipe = { length: 0.36, thump: 0.45, grains: 220, toe: 0.35, toeAt: 0.11, low: 1200, spread: 3800, grain: 0.08, grainSpread: 0.25, smooth: 0.55, peak: 0.7 };

/** One step: `seed` picks its grains, `pitch` lifts or lowers the crackle. */
export function footstep(seed: number, pitch = 1, r: StepRecipe = PATH): Float32Array {
  const rnd = random(seed);
  const n = Math.round(RATE * r.length);
  const out = new Float32Array(n);
  // The heel: a low thump that dies in a few hundredths of a second.
  for (let i = 0; i < n; i++) {
    const t = i / RATE;
    out[i]! += r.thump * Math.sin(2 * Math.PI * 70 * t) * Math.exp(-t / 0.025) * Math.min(1, t / 0.003);
  }
  // The crunch: grains of grit, thickest just after the heel, then the toe.
  for (let g = 0; g < r.grains; g++) {
    const toe = rnd() < r.toe;
    const at = toe ? r.toeAt + rnd() * 0.12 : Math.pow(rnd(), 1.8) * 0.16;
    const freq = (r.low + rnd() * r.spread) * pitch;
    const decay = 0.0008 + rnd() * 0.003;
    const amp = (r.grain + rnd() * r.grainSpread) * (toe ? 0.6 : 1) * Math.exp(-at / 0.12);
    const start = Math.round(at * RATE);
    const phase = rnd() * Math.PI * 2;
    for (let i = start; i < Math.min(n, start + Math.round(decay * 6 * RATE)); i++) {
      const t = (i - start) / RATE;
      out[i]! += amp * Math.sin(2 * Math.PI * freq * t + phase) * Math.exp(-t / decay);
    }
  }
  // Soften the top a little (one-pole low-pass) and fade the tail out.
  let y = 0;
  for (let i = 0; i < n; i++) {
    y += r.smooth * (out[i]! - y);
    out[i] = y * Math.min(1, (n - i) / (RATE * 0.04));
  }
  const peak = out.reduce((m, v) => Math.max(m, Math.abs(v)), 0) || 1;
  for (let i = 0; i < n; i++) out[i] = (out[i]! / peak) * r.peak;
  return out;
}

/**
 * Her steps in her rooms, set to RE1's own steps' level (theirs peak at -3
 * to -14 dB): walking, a heel and a roll to the toe; running, a shorter,
 * harder strike.
 * - Earth: packed dirt, needles and grass, duller and softer than the path.
 * - Gravel: loose stones, more grains, brighter, a longer toe.
 */
export const GROUND_STEPS = {
  earth: {
    walk: { ...PATH, thump: 0.6, grains: 90, grain: 0.05, grainSpread: 0.14, low: 700, spread: 2200, smooth: 0.35, peak: 0.45 },
    run: { ...PATH, length: 0.26, thump: 0.75, grains: 110, toe: 0.2, toeAt: 0.07, grain: 0.06, grainSpread: 0.16, low: 700, spread: 2400, smooth: 0.38, peak: 0.55 },
  },
  gravel: {
    walk: { ...PATH, length: 0.42, thump: 0.35, grains: 420, toe: 0.45, grain: 0.07, grainSpread: 0.22, low: 1500, spread: 4200, smooth: 0.6, peak: 0.45 },
    run: { ...PATH, length: 0.32, thump: 0.45, grains: 480, toe: 0.3, toeAt: 0.08, grain: 0.08, grainSpread: 0.26, low: 1500, spread: 4400, smooth: 0.62, peak: 0.55 },
  },
} as const satisfies Record<string, { walk: StepRecipe; run: StepRecipe }>;

/** 16-bit mono PCM WAV bytes. */
export function wav(samples: Float32Array): Uint8Array {
  const data = samples.length * 2;
  const b = new Uint8Array(44 + data);
  const v = new DataView(b.buffer);
  const text = (at: number, s: string) => [...s].forEach((c, i) => v.setUint8(at + i, c.charCodeAt(0)));
  text(0, 'RIFF');
  v.setUint32(4, 36 + data, true);
  text(8, 'WAVE');
  text(12, 'fmt ');
  v.setUint32(16, 16, true);
  v.setUint16(20, 1, true); // PCM
  v.setUint16(22, 1, true); // mono
  v.setUint32(24, RATE, true);
  v.setUint32(28, RATE * 2, true);
  v.setUint16(32, 2, true);
  v.setUint16(34, 16, true);
  text(36, 'data');
  v.setUint32(40, data, true);
  samples.forEach((s, i) => v.setInt16(44 + i * 2, Math.max(-32768, Math.min(32767, Math.round(s * 32767))), true));
  return b;
}

/** The two steps PathWalk plays, by the names the engine's room sound table gives them. */
export const footstepFiles = (): { name: string; bytes: Uint8Array }[] => [
  { name: 'St_path01.wav', bytes: wav(footstep(1, 1.0)) },
  { name: 'St_path02.wav', bytes: wav(footstep(2, 0.9)) },
];
