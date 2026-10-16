// node --test tools/rebecca/music/ps1.test.ts
import assert from 'node:assert/strict';
import { test } from 'node:test';
import { adpcmRoundTrip, levelGain, loopedWav, rmsDb, toInt16, toMono22k } from './ps1.ts';

const tone = (hz: number, rate: number, n: number, amp = 0.5) => Float32Array.from({ length: n }, (_, i) => amp * Math.sin((2 * Math.PI * hz * i) / rate));

test('halving the rate keeps a 1 kHz tone and drops a 15 kHz one, which 22050 Hz cannot hold', () => {
  const low = tone(1000, 44100, 44100);
  const high = tone(15000, 44100, 44100);
  const keep = toMono22k(low, low).subarray(100, -100);
  const drop = toMono22k(high, high).subarray(100, -100);
  assert.equal(keep.length, 22050 - 200);
  assert.ok(Math.abs(rmsDb(keep) - rmsDb(low)) < 0.1, `1 kHz: ${rmsDb(keep)} against ${rmsDb(low)}`);
  assert.ok(rmsDb(drop) < rmsDb(high) - 60, `15 kHz is only down to ${rmsDb(drop)}`);
});

test('the level: RE1-loud by RMS, unless a peak would pass -1 dB', () => {
  const quiet = tone(440, 22050, 22050, 0.01);
  const gain = levelGain(quiet);
  assert.ok(Math.abs(rmsDb(Array.from(quiet, (v) => v * gain)) - -24) < 0.01);
  const spiky = new Float32Array(22050);
  spiky[100] = 0.5;
  assert.ok(Math.abs(20 * Math.log10(0.5 * levelGain(spiky)) - -1) < 0.01);
});

test('ADPCM: close to the input, silence stays silent, the same every time', () => {
  const pcm = toInt16(tone(440, 22050, 22050), 1);
  const out = adpcmRoundTrip(pcm);
  let err = 0;
  let sig = 0;
  for (let i = 0; i < pcm.length; i++) {
    err += (pcm[i]! - out[i]!) ** 2;
    sig += pcm[i]! ** 2;
  }
  const snr = 10 * Math.log10(sig / err);
  assert.ok(snr > 30 && snr < 90, `SNR ${snr} dB: 4-bit ADPCM is lossy, but not that lossy`);
  assert.deepEqual(adpcmRoundTrip(new Int16Array(100)), new Int16Array(100));
  assert.deepEqual(adpcmRoundTrip(pcm), out);
});

test('the WAV carries its loop where src/system/AudioFile.cpp reads it', () => {
  const pcm = Int16Array.from({ length: 1000 }, (_, i) => i - 500);
  const wav = loopedWav(pcm, 400);
  const dv = new DataView(wav.buffer);
  const tag = (at: number) => new TextDecoder().decode(wav.subarray(at, at + 4));
  assert.equal(tag(0), 'RIFF');
  assert.equal(dv.getUint32(4, true), wav.length - 8);
  const chunks = new Map<string, number>();
  for (let at = 12; at < wav.length; at += 8 + dv.getUint32(at + 4, true)) chunks.set(tag(at), at + 8);
  assert.deepEqual([...chunks.keys()], ['fmt ', 'smpl', 're1p', 'data']);
  const fmt = chunks.get('fmt ')!;
  assert.deepEqual([dv.getUint16(fmt, true), dv.getUint16(fmt + 2, true), dv.getUint32(fmt + 4, true), dv.getUint16(fmt + 14, true)], [1, 1, 22050, 16]);
  const smpl = chunks.get('smpl')!;
  // AudioFile.cpp: loop count at +28, the first loop's start at +44 and its inclusive end at +48.
  assert.deepEqual([dv.getUint32(smpl + 28, true), dv.getUint32(smpl + 44, true), dv.getUint32(smpl + 48, true)], [1, 400, 999]);
  assert.equal(dv.getUint32(chunks.get('re1p')!, true), 1);
  const data = chunks.get('data')!;
  assert.equal(dv.getUint32(data - 4, true), 2000);
  assert.deepEqual([dv.getInt16(data, true), dv.getInt16(data + 1998, true)], [-500, 499]);
});
