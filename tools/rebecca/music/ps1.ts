// The PS1 treatment for a rendered piece, and the WAV the game loads, as pure
// functions: render.ts runs them on what Strudel plays.
//
// - Halve the rate to 22050 Hz, the rate of RE1's own music on PC.
// - Mix to mono, as RE1's tracks are.
// - Set the level to RE1's: its music sits at about -21 to -26 dB RMS.
// - Run it through the PS1's sound chip's 4-bit ADPCM and back, which is
//   where RE1's grit comes from (psx-spx, "SPU ADPCM Samples").
// - Write the loop into the file: a `smpl` loop and the `re1p` mark, which
//   src/system/AudioFile.cpp reads, so the intro plays once and the rest loops.

export const RATE = 22050;

/** A filter for halving the rate: a windowed sinc cutting at 10 kHz, 63 taps. */
function halfBand(): Float64Array {
  const taps = 63;
  const mid = (taps - 1) / 2;
  const cut = 10000 / 44100; // cycles per input sample
  const h = new Float64Array(taps);
  let sum = 0;
  for (let i = 0; i < taps; i++) {
    const x = i - mid;
    const sinc = x === 0 ? 2 * cut : Math.sin(2 * Math.PI * cut * x) / (Math.PI * x);
    const blackman = 0.42 - 0.5 * Math.cos((2 * Math.PI * i) / (taps - 1)) + 0.08 * Math.cos((4 * Math.PI * i) / (taps - 1));
    h[i] = sinc * blackman;
    sum += h[i]!;
  }
  for (let i = 0; i < taps; i++) h[i]! /= sum;
  return h;
}

/** Stereo at 44100 Hz to mono at 22050 Hz. */
export function toMono22k(left: Float32Array, right: Float32Array): Float64Array {
  const h = halfBand();
  const mid = (h.length - 1) / 2;
  const out = new Float64Array(Math.floor(left.length / 2));
  for (let o = 0; o < out.length; o++) {
    const c = o * 2;
    let acc = 0;
    for (let k = 0; k < h.length; k++) {
      const i = c + k - mid;
      if (i >= 0 && i < left.length) acc += h[k]! * (left[i]! + right[i]!);
    }
    out[o] = acc / 2;
  }
  return out;
}

export function rmsDb(x: ArrayLike<number>): number {
  let s = 0;
  for (let i = 0; i < x.length; i++) s += x[i]! * x[i]!;
  return 10 * Math.log10(s / x.length);
}

export function peakDb(x: ArrayLike<number>): number {
  let p = 0;
  for (let i = 0; i < x.length; i++) p = Math.max(p, Math.abs(x[i]!));
  return 20 * Math.log10(p);
}

/** The gain that brings `x` to `rms` dB, held back so no sample goes past `peak` dB. */
export function levelGain(x: ArrayLike<number>, rms = -24, peak = -1): number {
  return 10 ** (Math.min(rms - rmsDb(x), peak - peakDb(x)) / 20);
}

/** The PS1 SPU's ADPCM prediction filters, in 64ths (psx-spx). */
const K0 = [0, 60, 115, 98, 122];
const K1 = [0, 0, -52, -55, -60];

const clamp16 = (v: number) => (v > 32767 ? 32767 : v < -32768 ? -32768 : v);

/**
 * Encode 16-bit samples as the PS1 does, 28 to a block with the filter and
 * shift that fit each block best, and decode them again: what the console
 * would play back. Same input, same output.
 */
export function adpcmRoundTrip(pcm: Int16Array): Int16Array {
  const out = new Int16Array(pcm.length);
  let p1 = 0;
  let p2 = 0;
  const block = new Int16Array(28);
  const best = new Int16Array(28);
  for (let at = 0; at < pcm.length; at += 28) {
    let bestErr = Infinity;
    let bestP1 = 0;
    let bestP2 = 0;
    for (let f = 0; f < 5; f++) {
      for (let shift = 0; shift <= 12; shift++) {
        let s1 = p1;
        let s2 = p2;
        let err = 0;
        const step = 2 ** (12 - shift);
        for (let i = 0; i < 28; i++) {
          const x = at + i < pcm.length ? pcm[at + i]! : 0;
          const predicted = (s1 * K0[f]! + s2 * K1[f]! + 32) >> 6;
          const nibble = Math.max(-8, Math.min(7, Math.round((x - predicted) / step)));
          const y = clamp16(((nibble << 12) >> shift) + predicted);
          block[i] = y;
          err += (x - y) * (x - y);
          if (err >= bestErr) break;
          s2 = s1;
          s1 = y;
        }
        if (err < bestErr) {
          bestErr = err;
          best.set(block);
          bestP1 = s1;
          bestP2 = s2;
        }
      }
    }
    for (let i = 0; i < 28 && at + i < pcm.length; i++) out[at + i] = best[i]!;
    p1 = bestP1;
    p2 = bestP2;
  }
  return out;
}

/** Float samples to 16-bit, scaled by `gain`, rounded and clipped. */
export function toInt16(x: ArrayLike<number>, gain: number): Int16Array {
  const out = new Int16Array(x.length);
  for (let i = 0; i < x.length; i++) out[i] = clamp16(Math.round(x[i]! * gain * 32767));
  return out;
}

/**
 * A 16-bit mono WAV at RATE whose frames from `loopStart` to the end loop:
 * fmt, smpl (one forward loop, its end inclusive), re1p (value 1), data.
 */
export function loopedWav(pcm: Int16Array, loopStart: number): Uint8Array {
  if (loopStart < 0 || loopStart >= pcm.length - 1) throw new Error(`loop start ${loopStart} is outside the ${pcm.length} frames`);
  const chunks: [string, Uint8Array][] = [];
  const fmt = new DataView(new ArrayBuffer(16));
  fmt.setUint16(0, 1, true); // PCM
  fmt.setUint16(2, 1, true); // mono
  fmt.setUint32(4, RATE, true);
  fmt.setUint32(8, RATE * 2, true);
  fmt.setUint16(12, 2, true);
  fmt.setUint16(14, 16, true);
  chunks.push(['fmt ', new Uint8Array(fmt.buffer)]);
  const smpl = new DataView(new ArrayBuffer(60));
  smpl.setUint32(8, Math.round(1e9 / RATE), true); // sample period, ns
  smpl.setUint32(12, 60, true); // unity note
  smpl.setUint32(28, 1, true); // one loop
  smpl.setUint32(36 + 8, loopStart, true);
  smpl.setUint32(36 + 12, pcm.length - 1, true);
  chunks.push(['smpl', new Uint8Array(smpl.buffer)]);
  chunks.push(['re1p', new Uint8Array([1, 0, 0, 0])]);
  const data = new Uint8Array(pcm.length * 2);
  const dv = new DataView(data.buffer);
  pcm.forEach((v, i) => dv.setInt16(i * 2, v, true));
  chunks.push(['data', data]);
  const size = 12 + chunks.reduce((n, [, b]) => n + 8 + b.length + (b.length & 1), 0);
  const out = new Uint8Array(size);
  const ov = new DataView(out.buffer);
  const tag = (s: string, at: number) => out.set(new TextEncoder().encode(s), at);
  tag('RIFF', 0);
  ov.setUint32(4, size - 8, true);
  tag('WAVE', 8);
  let at = 12;
  for (const [id, b] of chunks) {
    tag(id, at);
    ov.setUint32(at + 4, b.length, true);
    out.set(b, at + 8);
    at += 8 + b.length + (b.length & 1);
  }
  return out;
}
