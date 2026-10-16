// Draw the music research for the owner: the sketches with a link that opens
// each in Strudel ready to play, the cue for every room and cutscene
// (plan/music.ts), and the plan. The full write-up is docs/REBECCA_MUSIC.md.
//
// Each cue's channels are listenable from their renders (render.ts), copied
// into <outdir>/renders, and openable in Strudel.
//
//   node tools/rebecca/music/page.ts <outdir>
import { copyFileSync, existsSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { day } from '../plan/day.ts';
import { CUES, SKETCHES, type Cue, type CueKind } from '../plan/music.ts';
import { CUTSCENES } from '../plan/todo.ts';

const here = path.dirname(fileURLToPath(import.meta.url));
const esc = (s: string) => s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');

/** Strudel's share link: the code, UTF-8, base64, in the hash (core/util.mjs code2hash). */
const strudelUrl = (code: string) => `https://strudel.cc/#${encodeURIComponent(Buffer.from(code, 'utf8').toString('base64'))}`;

const KIND: Record<CueKind, string> = { new: 'New', reuse: "RE1's own", ambience: 'No music' };
const placeName = (id: string) => day.places.find((p) => p.id === id)?.name ?? id;
const stepName = (id: string) => day.steps.find((st) => st.id === id)?.label ?? id;
const sceneName = (id: string) => CUTSCENES.find(([s]) => s === id)?.[1] ?? id;

const renders = path.join(here, 'renders');
const rendered = (sketch: string) => existsSync(path.join(renders, `${sketch}.wav`));
/** Every render's size together, in MB. */
const mb = () => (SKETCHES.filter(rendered).reduce((n, sk) => n + readFileSync(path.join(renders, `${sk}.wav`)).length, 0) / 1e6).toFixed(0);

/** A channel: its render to play, its code to open in Strudel. */
function channel(sketch: string, what: string): string {
  const code = readFileSync(path.join(here, 'sketches', `${sketch}.js`), 'utf8');
  const audio = rendered(sketch) ? `<audio controls preload="none" src="renders/${sketch}.wav"></audio>` : '<p class="dim">Not rendered yet.</p>';
  return `<div class="ch"><b>${esc(what)}</b> <span class="dim">${esc(sketch)}.js</span>
${audio}
<p><a class="play" href="${esc(strudelUrl(code))}" target="_blank" rel="noopener">Open in Strudel</a></p>
<details><summary>The code</summary><pre>${esc(code)}</pre></details></div>`;
}

/** Where a channel plays, and what switches it. */
function switchNote(c: Cue, i: number): string {
  const ch = c.channels[i]!;
  const where = `Plays in ${ch.in ? ch.in.map(placeName).join(', ') : 'all its rooms'}`;
  if (!ch.switched) return `${where}.`;
  return 'on' in ch.switched ? `${where}, once she does this: ${stepName(ch.switched.on)}.` : `${where}, until she does this: ${stepName(ch.switched.off)}.`;
}

function page(): string {
  const sketches = CUES.filter((c) => c.channels.some((ch) => ch.sketch)).map((c) => {
    const chans = c.channels.flatMap((ch, i) => (ch.sketch ? [channel(ch.sketch, i === 0 ? 'The theme' : `Layer: ${ch.what}`) + (i > 0 ? `<p class="dim">${esc(switchNote(c, i))}</p>` : '')] : []));
    return `<div class="sketch"><h3>${esc(c.title)}</h3><p>${esc(c.mood)}</p>${chans.join('\n')}</div>`;
  }).join('\n');
  const cues = CUES.map((c) => {
    const where = [
      c.places.length ? c.places.map(placeName).join(', ') : '',
      c.cutscenes.length ? `Cutscenes: ${c.cutscenes.map(sceneName).join('; ')}` : '',
    ].filter(Boolean);
    return `<tr><td><b>${esc(c.title)}</b><br><span class="k k-${c.kind}">${KIND[c.kind]}</span>${c.channels.some((ch) => ch.sketch) ? ' <span class="k">sketched</span>' : ''}</td>
<td>${esc(c.mood)}<div class="dim">${esc(c.sound)}</div></td>
<td>${where.map(esc).join('<br>')}<div class="dim">Channels: ${c.channels.map((ch) => esc(ch.what)).join('; ')}</div></td></tr>`;
  }).join('\n');
  const fresh = CUES.filter((c) => c.kind === 'new').length;
  return `<!doctype html>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Rebecca's day: music</title>
<script src="/research/rebecca-day/nav.js" defer></script>
<style>
:root{--bg:#121110;--fg:#ddd6c8;--dim:#8b8478;--line:#2a2724;--accent:#c8963c;--ok:#7d9a5a}
body{background:var(--bg);color:var(--fg);font:15px/1.5 system-ui,sans-serif;max-width:1040px;margin:2em auto;padding:0 1em}
h1{font-weight:600;margin-bottom:.2em}h2{margin:1.8em 0 .4em;font-size:1.2em}h3{margin:.2em 0}
p,li{max-width:46em}.dim,.lede{color:var(--dim)}.dim{font-size:.88em;margin-top:.3em}
a{color:var(--accent)}.sketches{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:1em}
.sketch{border:1px solid var(--line);border-radius:6px;padding:.8em 1em}.sketch p{color:var(--dim);margin:.4em 0}\n.ch{border-top:1px solid var(--line);padding-top:.5em;margin-top:.6em}audio{width:100%;margin:.3em 0}
.play{display:inline-block;border:1px solid var(--accent);border-radius:4px;padding:.3em .8em;text-decoration:none}
pre{background:#1b1917;padding:.7em;overflow:auto;font-size:12px;line-height:1.4}
table{border-collapse:collapse;width:100%}td{border-top:1px solid var(--line);padding:.6em .5em;vertical-align:top}
td:first-child{width:12em}td:last-child{width:22em}
.k{font-size:.75em;border:1px solid var(--line);border-radius:3px;padding:0 .4em;color:var(--dim)}
.k-new{color:var(--accent);border-color:var(--accent)}.k-reuse{color:var(--ok);border-color:var(--ok)}
ol li,ul li{margin:.35em 0}
</style>
<h1>Rebecca's day: music</h1>
<p class="lede">First drafts of every piece, 16 October 2026: each one rendered as the game plays it, and openable in Strudel. How RE1's music works, how we make ours without playing an instrument, and where every piece goes.</p>

<h2>Listen first</h2>
<p>Each player holds a render as the game has it: 22 kHz mono with the PlayStation's grit, the first pass, which the game plays once, then the loop it repeats. "Open in Strudel" opens its code, a music-as-code tool in the browser. Press play, or Ctrl+Enter. Change any number and press play again to hear the change. If one sounds close, send the edited link back through the pad.</p>
<p>A layer is a second or third channel of the same piece. The game starts it with the theme in the rooms it plays in, or when she does something: the generator hum joins the station once the power is on. Play a layer alongside its theme to hear them together; in the game they don't start in step.</p>
<p class="dim">First drafts, not finished pieces. A script checked that each one parses and plays, using only CC0 sounds. Nobody has listened to them yet.</p>
<div class="sketches">${sketches}</div>

<h2>What makes RE1 sound like RE1</h2>
<p>Hear it for yourself: <a href="../re1-music/">every track of RE1's music written out as Strudel code</a>, note for note from your PS1 disc, with the game's own instruments. Read its code beside ours.</p>
<ul>
<li>It was written in MIDI and played on the PlayStation over a tiny bank of samples: music got 256 KB. That is where the sound comes from: short looped samples at low quality, dull blurred reverb, a bit of grit.</li>
<li>Many rooms have no music at all, only wind, a clock, footsteps. The silence does as much as the music.</li>
<li>The save room theme is two or three minor chords and a short melody on a loop. Every save room in her day plays it, from the player's own game files.</li>
</ul>

<h2>How we make it</h2>
<ul>
<li><b>Write each piece as code in Strudel.</b> A piece is a short text file in the repository. Claude writes it; you judge it by ear and steer it ("slower", "darker", "less busy"), or change the numbers yourself.</li>
<li><b>Use only sounds we are allowed to ship.</b> VCSL is a free CC0 sample library with two pianos, a harp, bowed vibraphone, wineglass, organs, timpani and an anvil. Strudel's own synths make the pads and drones. The music we make with Strudel is ours.</li>
<li><b>No AI music generators.</b> None can render the same track twice from a file we keep, and their terms don't give us clean rights.</li>
<li><b>Render to WAV the same way every time,</b> then make it sound like a 1996 PlayStation: 22 kHz, mono, a little crushed.</li>
<li><b>The game plays it.</b> RE1 plays music from plain WAV files, and her mode's folder is searched first. It plays an intro once and loops the rest, and up to three layers per room. Her mode reads its own music table from her folder, so Chris's and Jill's games stay as they are.</li>
<li><b>The layers react.</b> Room scripts switch them as she works: the generator hum joins the station, the mill joins the camp, the line hums once the breakers close, and the mine's water stops once the pump runs. When the mine takes her gear, its rooms switch to the chase until she is out.</li>
</ul>

<h2>Where every piece goes</h2>
<p>${CUES.length} cues: ${fresh} new pieces, ${CUES.filter((c) => c.kind === 'ambience').length} with no music, and RE1's own save room music at the end, played from the player's own game. Every room and cutscene is covered, and a test keeps it that way.</p>
<table>${cues}</table>

<h2>The plan</h2>
<ol>
<li><b>Choose the sound.</b> You listen to the drafts and say what is right and wrong.</li>
<li><b>Render a sketch to a WAV</b> with one command that gives the same file every time. Done.</li>
<li><b>Make it sound like the PlayStation:</b> 22 kHz mono and some grit. Done; still to compare with RE1's own tracks by ear.</li>
<li><b>Add loop points,</b> so the intro plays once and the loop joins without a click. Done.</li>
<li><b>Give her mode its own music table.</b> Done: Chris's and Jill's music hasn't changed.</li>
<li><b>Write the pieces.</b> A first draft of every one is above.</li>
<li><b>Make the layers react</b> to what she has done. Done.</li>
<li><b>Test it:</b> the harness visits a room of every area and checks the file each channel plays, and that a step switches a channel. Done.</li>
</ol>

<h2>Questions for you</h2>
<ul>
<li>Do the drafts sound like the right world, or should we try a more orchestral sample library? Some need a credit line.</li>
<li>8-bit or 16-bit? RE1's PC tracks are 8-bit. Ours are 16-bit, ${mb()} MB for every render on this page; 8-bit halves that, with more hiss under the quiet pieces.</li>
<li>Should the renders be committed, so a build needs no Chrome and no network? They are rebuilt, the same bytes, with one command.</li>
<li>Where should the chase play? Today the mine's rooms switch to it the moment the floor gives way in the gallery, and back to the mine's drone once she reaches the quarry or the summit trail.</li>
<li>The dogs far off on the grounds: VCSL has no dog, so they are left to the sound work.</li>
</ul>
<p class="dim">Made ${new Date().toISOString().slice(0, 16).replace('T', ' ')} UTC from tools/rebecca/plan/music.ts, tools/rebecca/music/sketches/ and their renders. The write-up with sources is docs/REBECCA_MUSIC.md.</p>
`;
}

const out = process.argv[2];
if (!out) {
  console.error('usage: node tools/rebecca/music/page.ts <outdir>');
  process.exit(2);
}
mkdirSync(path.join(out, 'renders'), { recursive: true });
for (const sk of SKETCHES) if (rendered(sk)) copyFileSync(path.join(renders, `${sk}.wav`), path.join(out, 'renders', `${sk}.wav`));
writeFileSync(path.join(out, 'index.html'), page());
console.log(path.join(out, 'index.html'));
