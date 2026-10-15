// RE1's own music as Strudel code, transcribed from the player's PS1 disc, so
// new pieces can be written beside the real thing in the same language. The
// notes and their timing are exact: each comes from the disc's sequence,
// with weights in the sequence's own ticks. The instruments are the game's
// samples, keyed at their centre note, with envelopes worked out from the
// bank's ADSR (close, not exact). Pitch bends and the PS1's reverb are not
// reproduced.
//
// This is Capcom's music, so nothing it writes goes in the repository: it is
// made from the player's disc and published on the LAN only.
//
//   pnpm rae music re1.img /tmp/re1-music          (retro-archive-explorer)
//   node tools/rebecca/music/re1.ts /tmp/re1-music <outdir> [voices.json]
//
// <outdir> gets one .js per sequence with notes, the samples they play, and
// tracks.json; page-re1.ts draws the player page from it. With voices.json
// (re1-voices.ts) each track also gets a .free.js on free sounds; choices
// in re1-voices.fix.json beside this file win over the measured ones.
import { copyFileSync, mkdirSync, readFileSync, readdirSync, writeFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { loadVoices, type Voice } from './re1-voices.ts';

// The shapes `rae music` writes (retro-archive-explorer, electron/parsers/audio/psxSeq.ts).
interface Tone { program: number; minKey: number; maxKey: number; center: number; fine: number; volume: number; pan: number; sample: number; adsr1: number; adsr2: number }
interface Program { index: number; volume: number; pan: number; tones: Tone[] }
type SeqEvent =
  | { tick: number; kind: 'note'; channel: number; key: number; velocity: number; length: number }
  | { tick: number; kind: 'program'; channel: number; program: number }
  | { tick: number; kind: 'control'; channel: number; control: number; value: number }
  | { tick: number; kind: 'bend'; channel: number; value: number }
  | { tick: number; kind: 'tempo'; usPerQuarter: number };
interface Sequence { id: number; ppq: number; usPerQuarter: number; beats: number; beatUnit: number; ticks: number; loop?: { start: number; end: number }; events: SeqEvent[] }
interface Sample { index: number; file: string; frames: number; loop?: { start: number; end: number } }
export interface Music { file: string; bank: { volume: number; pan: number; programs: Program[] }; sequences: Sequence[]; samples: Sample[] }

/** A note as the Strudel code should play it, in ticks from the start of the transcribed span. */
export interface Played { readonly at: number; readonly length: number; readonly key: number; readonly sound: string }

export interface Track {
  readonly id: string;
  readonly name: string | undefined;
  readonly rooms: readonly string[];
  readonly bpm: number;
  readonly bars: number;
  readonly notes: number;
  readonly voices: number;
  readonly code: string;
  /** What the code should play, for the round-trip check. */
  readonly played: readonly Played[];
  readonly ticksPerCycle: number;
}

const NAMES = ['c', 'db', 'd', 'eb', 'e', 'f', 'gb', 'g', 'ab', 'a', 'bb', 'b'];
export const noteName = (midi: number) => `${NAMES[midi % 12]}${Math.floor(midi / 12) - 1}`;
const round = (x: number, places = 3) => Number(x.toFixed(places));

/**
 * The SPU's envelope as Strudel's attack, decay, sustain and release, in
 * seconds and a level (psx-spx, "SPU ADSR"). Each phase steps the level by
 * `step << max(0, 11 - shift)` every `1 << max(0, shift - 11)` samples at
 * 44.1 kHz; exponential phases scale the step by the level. A sustain that
 * falls while the key is held, as a piano's does, becomes part of the decay.
 */
export function spuEnvelope(adsr1: number, adsr2: number): { attack: number; decay: number; sustain: number; release: number } {
  const per = (rate: number, rising: boolean) => {
    const shift = rate >> 2;
    const step = rising ? 7 - (rate & 3) : -8 + (rate & 3);
    return { change: Math.abs(step) * 2 ** Math.max(0, 11 - shift), every: 2 ** Math.max(0, shift - 11) };
  };
  const seconds = (samples: number) => samples / 44100;
  const linear = (span: number, rate: number, rising: boolean) => {
    const { change, every } = per(rate, rising);
    return seconds((span / change) * every);
  };
  // Time for an exponential fall from `from` to `to`: the level loses change/0x8000 of itself each step.
  const falling = (from: number, to: number, rate: number) => {
    const { change, every } = per(rate, false);
    return seconds(((0x8000 / change) * every) * Math.log(from / Math.max(to, 1)));
  };
  const attackRate = (adsr1 >> 8) & 0x7f;
  const attack = adsr1 & 0x8000
    ? linear(0x6000, attackRate, true) + 4 * linear(0x2000, attackRate, true)
    : linear(0x7fff, attackRate, true);
  const level = (((adsr1 & 0x0f) + 1) * 0x800);
  const decay = level >= 0x7fff ? 0 : falling(0x7fff, level, ((adsr1 >> 4) & 0x0f) << 2);
  const sustainRate = (adsr2 >> 6) & 0x7f;
  const sustainFalls = (adsr2 & 0x4000) !== 0 && sustainRate < 0x7f;
  const releaseRate = (adsr2 & 0x1f) << 2;
  const release = adsr2 & 0x20 ? falling(Math.min(level, 0x7fff), 0x7fff / 100, releaseRate) : linear(Math.min(level, 0x7fff), releaseRate, false);
  // Held notes fade to silence (-40 dB) if the sustain falls within eight seconds; otherwise it holds.
  const fade = !sustainFalls ? Infinity : adsr2 & 0x8000 ? falling(level, level / 100, sustainRate) : linear(level, sustainRate, false);
  const held = fade < 8;
  return {
    attack: round(Math.max(attack, 0.001)),
    decay: round(held ? decay + fade : decay),
    sustain: round(held ? 0 : Math.min(level, 0x7fff) / 0x7fff),
    release: round(Math.min(Math.max(release, 0.01), 8)),
  };
}

interface Voiced { at: number; length: number; key: number; gain: number; pan: number; voice: string }

/** VCSL's sample map at the commit the sketches use. */
const VCSL_MAP = 'https://raw.githubusercontent.com/felixroos/dough-samples/9eacfc86ec4393e68a463ff52b01c19cfaa77f38/vcsl.json';

/**
 * Sequence `s` of `music` as Strudel code, or undefined when it plays no
 * notes. With `free` (re1-voices.ts, by sample) it plays on free sounds in
 * place of the game's samples; the notes are the same either way.
 */
export function transcribe(music: Music, s: number, id: string, name: string | undefined, rooms: readonly string[], free?: Readonly<Record<string, Voice>>): Track | undefined {
  const seq = music.sequences[s]!;
  const notes = seq.events.filter((e) => e.kind === 'note');
  if (notes.length === 0) return undefined;
  // From the loop start when nothing plays before it (the lead-in is set-up), to the loop end.
  const start = seq.loop && !notes.some((n) => n.tick < seq.loop!.start) ? seq.loop.start : 0;
  const end = seq.loop?.end ?? seq.ticks;
  const ticksPerBar = (seq.ppq * 4 * seq.beats) / seq.beatUnit;
  const span = end - start;
  const programs = new Map(music.bank.programs.map((p) => [p.index, p]));
  const prefix = id.toLowerCase().replace(/[^a-z0-9]/g, '');

  // Each channel's program, volume, expression and pan as the sequence runs; libsnd starts them at 0, 127, 127, 64.
  const state = new Map<number, { program: number; volume: number; expression: number; pan: number }>();
  const at = (ch: number) => state.get(ch) ?? state.set(ch, { program: 0, volume: 127, expression: 127, pan: 64 }).get(ch)!;
  const sounds = new Map<string, { tone: Tone; program: Program }>();
  const voiced: Voiced[] = [];
  const skipped: string[] = [];
  let bends = 0;
  let tempos = 0;
  for (const e of seq.events) {
    switch (e.kind) {
      case 'program': at(e.channel).program = e.program; break;
      case 'control':
        if (e.control === 7) at(e.channel).volume = e.value;
        if (e.control === 11) at(e.channel).expression = e.value;
        if (e.control === 10) at(e.channel).pan = e.value;
        break;
      case 'bend': if (e.value !== 0) bends++; break;
      case 'tempo': tempos++; break;
      case 'note': {
        if (e.tick >= end || e.tick < start) break;
        const c = at(e.channel);
        const program = programs.get(c.program);
        const tone = program?.tones.find((t) => e.key >= t.minKey && e.key <= t.maxKey);
        if (!program || !tone) {
          skipped.push(`ch ${e.channel} program ${c.program} key ${e.key}`);
          break;
        }
        const voice = `${prefix}_p${program.index}t${program.tones.indexOf(tone)}`;
        sounds.set(voice, { tone, program });
        const gain = (e.velocity / 127) * (c.volume / 127) * (c.expression / 127) * (tone.volume / 127) * (program.volume / 127) * (music.bank.volume / 127);
        const pan = Math.min(127, Math.max(0, c.pan + (tone.pan - 64) + (program.pan - 64))) / 127;
        voiced.push({ at: e.tick - start, length: Math.max(1, Math.min(e.length, end - e.tick)), key: e.key, gain: round(gain, 2), pan: round(pan, 2), voice: `${voice}|ch${e.channel}` });
      }
    }
  }

  // Lanes: each a monophonic line of notes and chords (same start, same length) on one sound and channel.
  type Chord = { at: number; length: number; keys: number[]; gain: number; pan: number };
  const lanes: { sound: string; channel: string; chords: Chord[] }[] = [];
  const byVoice = Map.groupBy(voiced, (v) => v.voice);
  for (const [voice, list] of byVoice) {
    const [sound, channel] = voice.split('|') as [string, string];
    const chords: Chord[] = [];
    for (const v of [...list].sort((a, b) => a.at - b.at || a.key - b.key)) {
      const same = chords.find((c) => c.at === v.at && c.length === v.length);
      if (same) {
        same.keys.push(v.key);
        same.gain = Math.max(same.gain, v.gain);
      } else chords.push({ at: v.at, length: v.length, keys: [v.key], gain: v.gain, pan: v.pan });
    }
    const mine: Chord[][] = [];
    for (const c of chords) {
      const lane = mine.find((l) => l.at(-1)!.at + l.at(-1)!.length <= c.at);
      if (lane) lane.push(c);
      else mine.push([c]);
    }
    for (const l of mine) lanes.push({ sound, channel, chords: l });
  }
  lanes.sort((a, b) => a.channel.localeCompare(b.channel, 'en', { numeric: true }) || a.sound.localeCompare(b.sound));

  // A lane as mini-notation weighted in ticks, one line per bar it starts in.
  const mini = (chords: Chord[], value: (c: Chord) => string) => {
    const parts: string[] = [];
    let cursor = 0;
    let bar = -1;
    const put = (token: string, from: number, ticks: number) => {
      const b = Math.floor(from / ticksPerBar);
      parts.push(`${b !== bar && parts.length ? '\n    ' : ''}${token}${ticks === 1 ? '' : `@${ticks}`}`);
      bar = b;
    };
    for (const c of chords) {
      if (c.at > cursor) put('~', cursor, c.at - cursor);
      put(value(c), c.at, c.length);
      cursor = c.at + c.length;
    }
    if (span > cursor) put('~', cursor, span - cursor);
    return parts.join(' ').replace(/ \n/g, '\n');
  };
  const sampleOf = new Map(music.samples.map((x) => [x.index, x]));
  const constOr = (name: string, chords: Chord[], value: (c: Chord) => number) => {
    const values = new Set(chords.map(value));
    return values.size === 1 ? `.${name}(${[...values][0]})` : `.${name}(\`${mini(chords, (c) => String(value(c)))}\`)`;
  };
  const hz = (key: number) => 440 * 2 ** ((key - 69) / 12);
  const freeSounds = new Set<string>();
  const code = lanes.map(({ sound, channel, chords }) => {
    const { tone } = sounds.get(sound)!;
    const env = spuEnvelope(tone.adsr1, tone.adsr2);
    const sample = sampleOf.get(tone.sample)!;
    const notes = mini(chords, (c) => (c.keys.length === 1 ? noteName(c.keys[0]!) : `[${c.keys.map(noteName).join(',')}]`));
    const envelope = `.attack(${env.attack}).decay(${env.decay}).sustain(${env.sustain}).release(${env.release})`;
    if (free) {
      const tag = sound.split('_')[1]!;
      const v: Voice = free[`${id.slice(0, 5)}/${tag}`] ?? { family: 'piano', s: 'steinway', kind: 'sample', level: 1, about: '', heard: 'not sorted' };
      if (v.kind === 'sample' || v.kind === 'bank') freeSounds.add(v.s);
      const calls = [
        `.s('${v.s}')${v.chain ?? ''}`,
        // A drum from a VCSL bank sounds at its own pitch on the game sample's centre key.
        v.kind === 'bank' ? `.speed(${round(2 ** ((36 - tone.center) / 12), 4)})` : '',
        constOr('gain', chords, (c) => round(c.gain * v.level, 2)),
        constOr('pan', chords, (c) => c.pan),
        v.harmonics ? constOr('lpf', chords, (c) => Math.min(16000, Math.round(v.harmonics! * hz(Math.min(...c.keys))))) : v.lpf ? `.lpf(${v.lpf})` : '',
        `.attack(${Math.max(env.attack, v.attack ?? 0)}).decay(${env.decay}).sustain(${env.sustain}).release(${Math.max(env.release, v.release ?? 0)})`,
        '.clip(1)',
      ];
      return `  // ${channel}, ${tag}: ${v.family} for the game's ${sample.file} (${v.heard})\n  note(\`${notes}\`)\n    ${calls.filter(Boolean).join('')}`;
    }
    const gains = new Set(chords.map((c) => c.gain));
    const pans = new Set(chords.map((c) => c.pan));
    const calls = [
      `.s('${sound}')`,
      tone.fine ? `.speed(${round(2 ** (tone.fine / 128 / 12), 4)})` : '',
      gains.size === 1 ? `.gain(${[...gains][0]})` : `.gain(\`${mini(chords, (c) => String(c.gain))}\`)`,
      pans.size === 1 ? `.pan(${[...pans][0]})` : `.pan(\`${mini(chords, (c) => String(c.pan))}\`)`,
      envelope,
      sample.loop ? `.loop(1).loopBegin(${round(sample.loop.start / sample.frames, 4)}).loopEnd(${round(Math.min(1, sample.loop.end / sample.frames), 4)})` : '',
      '.clip(1)',
    ];
    return `  // ${channel}, ${sound.split('_')[1]}\n  note(\`${notes}\`)\n    ${calls.filter(Boolean).join('')}`;
  });

  const bpm = round(60e6 / seq.usPerQuarter, 1);
  const bars = round(span / ticksPerBar, 4);
  const map = [...sounds].map(([sound, { tone }]) => `  ${sound}: { '${noteName(tone.center)}': '${sampleOf.get(tone.sample)!.file}' },`);
  const limits = [
    bends ? `${bends} pitch bends` : '',
    tempos ? `${tempos} tempo changes (this plays the first tempo)` : '',
    skipped.length ? `${skipped.length} notes with no tone in the bank` : '',
  ].filter(Boolean);
  const header = [
    `// RE1's music from the PS1 disc: ${music.file}, sequence ${s}${name ? `, which the PC port plays as ${name}` : ''}.`,
    rooms.length ? `// Plays in: ${rooms.join(', ')}.` : '',
    `// ${bpm} BPM in ${seq.beats}/${seq.beatUnit}, ${bars} bars${seq.loop ? ', looping' : ''}. ${voiced.length} notes in ${lanes.length} voices.`,
    free
      ? "// Notes and timing are exact. The instruments are free sounds, VCSL (CC0) and Strudel's synths: each of the game's is sorted into a family (strings, harp, kick...) by re1-voices.ts and played on that family's sound. Envelopes are the game's."
      : "// Notes and timing are exact. The instruments are the game's own samples, with envelopes from its bank.",
    limits.length ? `// Not reproduced: ${limits.join(', ')}, and the PS1's reverb.` : "// Not reproduced: the PS1's reverb.",
    "// Generated by tools/rebecca/music/re1.ts from the player's disc. Capcom's music: keep it out of the repository.",
  ].filter(Boolean);
  const text = `${header.join('\n')}
setcpm(${round(bpm / ((seq.beats * 4) / seq.beatUnit), 4)})
${free ? (freeSounds.size ? `samples('${VCSL_MAP}')\n` : '') : `samples({\n${map.join('\n')}\n})\n`}
stack(
${code.join(',\n')}
)${free ? '.room(0.3).roomsize(3)' : ''}.slow(${span} / ${ticksPerBar}) // ${bars} bars of ${ticksPerBar} ticks
`;
  const played = voiced.map((v) => ({ at: v.at, length: v.length, key: v.key, sound: v.voice.split('|')[0]! }));
  return { id, name, rooms, bpm, bars, notes: voiced.length, voices: lanes.length, code: text, played, ticksPerCycle: span };
}

/** The PC port's track names per group and channel, and the rooms that play each group, from the decomp's tables. */
export function catalogue(src: string): { names: (string | undefined)[][]; rooms: Map<number, string[]> } {
  const sound = readFileSync(path.join(src, 'game/SoundTables.cpp'), 'utf8');
  const names = [...sound.matchAll(/\{ ("[^"]*"|NULL),\s+("[^"]*"|NULL),\s+("[^"]*"|NULL),\s+("[^"]*"|NULL)\s*\}, \/\/\s+\d+ @/g)]
    .map((m) => m.slice(1, 4).map((x) => (x === 'NULL' ? undefined : x!.slice(1, -1))));
  const debug = readFileSync(path.join(src, 'game/DebugMenu.cpp'), 'utf8');
  const list = (v: string) => [...debug.match(new RegExp(`${v}\\[\\d+\\] = \\{([^}]*)\\}`))![1]!.matchAll(/"([^"]*)"/g)].map((m) => m[1]!);
  const floors = ['s_dbgRoomsMansion1F', 's_dbgRoomsMansion2F', 's_dbgRoomsCourtyard', 's_dbgRoomsGuardhouse', 's_dbgRoomsLaboratory'].map(list);
  const stageNames = [0, 1, 2, 3, 4, 0, 1].map((i) => floors[i]!);
  const table = sound.slice(sound.indexOf('g_BgmRoomData[7][32][4]'));
  const rooms = new Map<number, string[]>();
  let stage = -1;
  for (const line of table.split('\n')) {
    const st = line.match(/\/\/ stage (\d)/);
    if (st) stage = Number(st[1]);
    const row = line.match(/\{ (0x[0-9A-F]{2}), (0x[0-9A-F]{2}), (0x[0-9A-F]{2}), (0x[0-9A-F]{2}) \}, \/\/ room ([0-9A-F]{2})/);
    if (!row || stage < 0) continue;
    const room = parseInt(row[5]!, 16);
    const label = `${stageNames[stage]![room] ?? `stage ${stage} room ${room}`}${stage >= 5 ? ' (return)' : ''}`;
    for (const g of new Set(row.slice(1, 5).map((x) => parseInt(x!, 16)).filter((g) => g !== 0xff))) {
      const r = rooms.get(g) ?? rooms.set(g, []).get(g)!;
      if (!r.includes(label)) r.push(label);
    }
    if (line.startsWith('};')) break;
  }
  return { names, rooms };
}

if (process.argv[1] === fileURLToPath(import.meta.url)) {
  const [input, out, voicesFile] = process.argv.slice(2);
  if (!input || !out) {
    console.error('usage: node tools/rebecca/music/re1.ts <rae music dir> <outdir> [voices.json]');
    process.exit(2);
  }
  const here = path.dirname(fileURLToPath(import.meta.url));
  const src = path.join(here, '../../../src');
  const free = voicesFile ? loadVoices(voicesFile) : undefined;
  const { names, rooms } = catalogue(src);
  mkdirSync(out, { recursive: true });
  const tracks: (Omit<Track, 'code' | 'played'> & { free: boolean })[] = [];
  for (const file of readdirSync(input).filter((f) => /^SEP[0-9A-F]{2}\.json$/.test(f)).sort()) {
    const music = JSON.parse(readFileSync(path.join(input, file), 'utf8')) as Music;
    const group = parseInt(file.slice(3, 5), 16);
    music.sequences.forEach((_, s) => {
      const id = `${file.slice(0, 5)}-${s}`;
      const t = transcribe(music, s, id, names[group]?.[s], rooms.get(group) ?? []);
      if (!t) return;
      writeFileSync(path.join(out, `${id}.js`), t.code);
      if (free) writeFileSync(path.join(out, `${id}.free.js`), transcribe(music, s, id, names[group]?.[s], rooms.get(group) ?? [], free)!.code);
      for (const m of t.code.matchAll(/'(SEP[0-9A-F]{2}\/s\d+\.wav)'/g)) {
        mkdirSync(path.join(out, path.dirname(m[1]!)), { recursive: true });
        copyFileSync(path.join(input, m[1]!), path.join(out, m[1]!));
      }
      const { code: _c, played: _p, ...meta } = t;
      tracks.push({ ...meta, free: free !== undefined });
    });
  }
  writeFileSync(path.join(out, 'tracks.json'), JSON.stringify(tracks, null, 1));
  console.log(`${tracks.length} tracks, ${tracks.reduce((a, t) => a + t.notes, 0)} notes, in ${out}`);
}
