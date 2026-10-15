// Prove the RE1 transcriptions play the disc's notes: evaluate each track's
// generated Strudel code with Strudel's own engine, query one pass of it, and
// compare every note's start, length, pitch and sound with the sequence, as
// exact fractions of a bar. Notes cut at the loop end are compared cut, and
// notes the bank has no tone for are left out: the PS1 plays nothing for them.
// The sound is the game's sample for the note's tone, or on free sounds the
// family voices.json and re1-voices.fix.json give that tone.
// Strudel isn't a dependency here; see check.ts for
// the scratch install.
//
//   node tools/rebecca/music/re1-check.ts /tmp/strudel /tmp/re1-music [voices.json]
//
// With voices.json the free-sound versions are checked too.
import { readFileSync, readdirSync } from 'node:fs';
import { createRequire } from 'node:module';
import path from 'node:path';
import { pathToFileURL } from 'node:url';
import { noteName, transcribe, type Music } from './re1.ts';
import { FAMILIES, loadVoices, readFixes, type Voice } from './re1-voices.ts';

const [dir, input, voicesFile] = process.argv.slice(2);
const free = voicesFile ? loadVoices(voicesFile) : undefined;
// Worked out here from the files, not by loadVoices, so a fix it drops or mangles shows.
const sorted = voicesFile ? (JSON.parse(readFileSync(voicesFile, 'utf8')) as Record<string, Voice>) : {};
const fixes = readFixes();
const freeSound = (tone: string) => {
  const family = fixes[tone] ?? fixes[tone.replace(/t\d+$/, '')] ?? sorted[tone]?.family;
  return family ? FAMILIES[family].s : 'steinway';
};
if (!dir || !input) {
  console.error('usage: node re1-check.ts <folder with @strudel installed> <rae music dir>');
  process.exit(2);
}
const from = createRequire(path.join(path.resolve(dir), 'package.json'));
const load = (name: string) => import(pathToFileURL(from.resolve(name)).href);
const [core, mini, tonal, { transpiler }] = await Promise.all(['@strudel/core', '@strudel/mini', '@strudel/tonal', '@strudel/transpiler'].map(load));
await core.evalScope(core, mini, tonal);
Object.assign(globalThis, { samples: () => {}, setcpm: () => {} });

interface Hap { whole: { begin: { mul(n: number): { valueOf(): number } }; end: { mul(n: number): { valueOf(): number } } }; value: { note: string; s: string; gain: unknown } }

/** What is left of `a` once each item of `b` takes one equal item out of it. */
const less = (a: readonly string[], b: readonly string[]) => {
  const left = new Map<string, number>();
  for (const x of b) left.set(x, (left.get(x) ?? 0) + 1);
  return a.filter((x) => {
    const n = left.get(x) ?? 0;
    left.set(x, n - 1);
    return n <= 0;
  });
};

let tracks = 0;
let notes = 0;
const failures: string[] = [];
for (const file of readdirSync(input).filter((f) => /^SEP[0-9A-F]{2}\.json$/.test(f)).sort()) {
  const music = JSON.parse(readFileSync(path.join(input, file), 'utf8')) as Music;
  for (let s = 0; s < music.sequences.length; s++) {
    for (const voices of free ? [undefined, free] : [undefined]) {
      const t = transcribe(music, s, `${file.slice(0, 5)}-${s}${voices ? '.free' : ''}`, undefined, [], voices);
      if (!t) continue;
      tracks++;
      const seq = music.sequences[s]!;
      const ticksPerBar = (seq.ppq * 4 * seq.beats) / seq.beatUnit;
      const { pattern } = await core.evaluate(t.code, transpiler);
      const haps: Hap[] = pattern.queryArc(0, t.ticksPerCycle / ticksPerBar).filter((h: Hap & { hasOnset(): boolean }) => h.hasOnset());
      const key = (at: number, length: number, note: string, sound: string) => `${at} ${length} ${note} ${sound}`;
      // A bar's worth of ticks times the hap's time in bars is its time in ticks, exactly.
      const got = haps.map((h) => key(Number(h.whole.begin.mul(ticksPerBar)), Number(h.whole.end.mul(ticksPerBar)) - Number(h.whole.begin.mul(ticksPerBar)), h.value.note, h.value.s)).sort();
      const silent = haps.filter((h) => typeof h.value.gain !== 'number' || !Number.isFinite(h.value.gain)).length;
      // What the disc plays over the transcribed pass: from the loop start if nothing sounds before it, to the loop end.
      // A note sounds when its channel's program has a tone covering its key; the SPU plays nothing for the rest.
      const program = new Map<number, number>();
      const toneOf = (channel: number, key: number) => {
        const p = music.bank.programs.find((p) => p.index === (program.get(channel) ?? 0));
        const t = p?.tones.findIndex((t) => key >= t.minKey && key <= t.maxKey) ?? -1;
        return t < 0 ? undefined : `p${p!.index}t${t}`;
      };
      const game = file.slice(0, 5).toLowerCase() + String(s);
      const disc = seq.events.flatMap((e) => {
        if (e.kind === 'program') program.set(e.channel, e.program);
        const tone = e.kind === 'note' ? toneOf(e.channel, e.key) : undefined;
        return e.kind === 'note' && tone ? [{ ...e, sound: voices ? freeSound(`${file.slice(0, 5)}/${tone}`) : `${game}_${tone}` }] : [];
      });
      const start = seq.loop && !disc.some((n) => n.tick < seq.loop!.start) ? seq.loop.start : 0;
      const end = seq.loop?.end ?? seq.ticks;
      const want = disc
        .filter((n) => n.tick >= start && n.tick < end)
        .map((n) => key(n.tick - start, Math.max(1, Math.min(n.length, end - n.tick)), noteName(n.key), n.sound))
        .sort();
      notes += want.length;
      // As multisets: a note the disc plays twice must play twice, and once only once.
      const missing = less(want, got);
      const extra = less(got, want);
      if (missing.length || extra.length || silent) failures.push(`${t.id}: ${missing.length} missing (${missing.slice(0, 2).join('; ')}), ${extra.length} extra (${extra.slice(0, 2).join('; ')}), ${silent} with no gain`);
    }
  }
}
for (const f of failures) console.log(`FAIL ${f}`);
console.log(`${tracks - failures.length} of ${tracks} tracks play their ${notes} notes exactly`);
process.exit(failures.length ? 1 : 0);
