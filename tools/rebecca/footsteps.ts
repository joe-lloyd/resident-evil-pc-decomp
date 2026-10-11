// Footsteps on a forest path, made from noise rather than taken from the
// game: a soft heel thump under a burst of crackle, as a boot settles on grit
// and dry needles. Two of them, one per foot, for the walk between Rebecca's
// outdoor rooms (src/game/PathWalk.cpp plays them from room sound slots 0
// and 1). WAV, 22050 Hz, 16-bit mono, as the game's own door sounds are.

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

/** One step: `seed` picks its grains, `pitch` lifts or lowers the crackle. */
export function footstep(seed: number, pitch = 1): Float32Array {
  const rnd = random(seed);
  const n = Math.round(RATE * 0.36);
  const out = new Float32Array(n);
  // The heel: a low thump that dies in a few hundredths of a second.
  for (let i = 0; i < n; i++) {
    const t = i / RATE;
    out[i]! += 0.45 * Math.sin(2 * Math.PI * 70 * t) * Math.exp(-t / 0.025) * Math.min(1, t / 0.003);
  }
  // The crunch: grains of grit, thickest just after the heel, then the toe.
  for (let g = 0; g < 220; g++) {
    const toe = rnd() < 0.35;
    const at = toe ? 0.11 + rnd() * 0.12 : Math.pow(rnd(), 1.8) * 0.16;
    const freq = (1200 + rnd() * 3800) * pitch;
    const decay = 0.0008 + rnd() * 0.003;
    const amp = (0.08 + rnd() * 0.25) * (toe ? 0.6 : 1) * Math.exp(-at / 0.12);
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
    y += 0.55 * (out[i]! - y);
    out[i] = y * Math.min(1, (n - i) / (RATE * 0.04));
  }
  const peak = out.reduce((m, v) => Math.max(m, Math.abs(v)), 0) || 1;
  for (let i = 0; i < n; i++) out[i] = (out[i]! / peak) * 0.7;
  return out;
}

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
