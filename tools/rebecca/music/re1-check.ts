// Prove the RE1 transcriptions play the disc's notes: evaluate each track's
// generated Strudel code with Strudel's own engine, query one pass of it, and
// compare every note's start, length and pitch with the sequence, as exact
// fractions of a bar. Notes cut at the loop end are compared cut, and notes
// the bank has no tone for are left out: the PS1 plays nothing for them.
// Strudel isn't a dependency here; see check.ts for
// the scratch install.
//
//   node tools/rebecca/music/re1-check.ts /tmp/strudel /tmp/re1-music
import { readFileSync, readdirSync } from 'node:fs';
import { createRequire } from 'node:module';
import path from 'node:path';
import { pathToFileURL } from 'node:url';
import { noteName, transcribe, type Music } from './re1.ts';

const [dir, input] = process.argv.slice(2);
if (!dir || !input) {
  console.error('usage: node re1-check.ts <folder with @strudel installed> <rae music dir>');
  process.exit(2);
}
const from = createRequire(path.join(path.resolve(dir), 'package.json'));
const load = (name: string) => import(pathToFileURL(from.resolve(name)).href);
const [core, mini, tonal, { transpiler }] = await Promise.all(['@strudel/core', '@strudel/mini', '@strudel/tonal', '@strudel/transpiler'].map(load));
await core.evalScope(core, mini, tonal);
Object.assign(globalThis, { samples: () => {}, setcpm: () => {} });

interface Hap { whole: { begin: { mul(n: number): { valueOf(): number } }; end: { mul(n: number): { valueOf(): number } } }; value: { note: string; s: string } }

let tracks = 0;
let notes = 0;
const failures: string[] = [];
for (const file of readdirSync(input).filter((f) => /^SEP[0-9A-F]{2}\.json$/.test(f)).sort()) {
  const music = JSON.parse(readFileSync(path.join(input, file), 'utf8')) as Music;
  for (let s = 0; s < music.sequences.length; s++) {
    const t = transcribe(music, s, `${file.slice(0, 5)}-${s}`, undefined, []);
    if (!t) continue;
    tracks++;
    const seq = music.sequences[s]!;
    const ticksPerBar = (seq.ppq * 4 * seq.beats) / seq.beatUnit;
    const { pattern } = await core.evaluate(t.code, transpiler);
    const haps: Hap[] = pattern.queryArc(0, t.ticksPerCycle / ticksPerBar).filter((h: Hap & { hasOnset(): boolean }) => h.hasOnset());
    const key = (at: number, length: number, note: string) => `${at} ${length} ${note}`;
    // A bar's worth of ticks times the hap's time in bars is its time in ticks, exactly.
    const got = haps.map((h) => key(Number(h.whole.begin.mul(ticksPerBar)), Number(h.whole.end.mul(ticksPerBar)) - Number(h.whole.begin.mul(ticksPerBar)), h.value.note)).sort();
    // What the disc plays over the transcribed pass: from the loop start if nothing sounds before it, to the loop end.
    // A note sounds when its channel's program has a tone covering its key; the SPU plays nothing for the rest.
    const program = new Map<number, number>();
    const sounds = (channel: number, key: number) =>
      music.bank.programs.find((p) => p.index === (program.get(channel) ?? 0))?.tones.some((t) => key >= t.minKey && key <= t.maxKey) ?? false;
    const disc = seq.events.flatMap((e) => {
      if (e.kind === 'program') program.set(e.channel, e.program);
      return e.kind === 'note' && sounds(e.channel, e.key) ? [e] : [];
    });
    const start = seq.loop && !disc.some((n) => n.tick < seq.loop!.start) ? seq.loop.start : 0;
    const end = seq.loop?.end ?? seq.ticks;
    const want = disc
      .filter((n) => n.tick >= start && n.tick < end)
      .map((n) => key(n.tick - start, Math.max(1, Math.min(n.length, end - n.tick)), noteName(n.key)))
      .sort();
    notes += want.length;
    const missing = want.filter((w) => !got.includes(w));
    const extra = got.filter((g) => !want.includes(g));
    if (missing.length || extra.length) failures.push(`${t.id}: ${missing.length} missing (${missing.slice(0, 2).join('; ')}), ${extra.length} extra (${extra.slice(0, 2).join('; ')})`);
  }
}
for (const f of failures) console.log(`FAIL ${f}`);
console.log(`${tracks - failures.length} of ${tracks} tracks play their ${notes} notes exactly`);
process.exit(failures.length ? 1 : 0);
