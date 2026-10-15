// Draw the music research for the owner: the sketches with a link that opens
// each in Strudel ready to play, the cue for every room and cutscene
// (plan/music.ts), and the plan. The full write-up is docs/REBECCA_MUSIC.md.
//
//   node tools/rebecca/music/page.ts <outdir>
import { mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { day } from '../plan/day.ts';
import { CUES, type CueKind } from '../plan/music.ts';
import { CUTSCENES } from '../plan/todo.ts';

const here = path.dirname(fileURLToPath(import.meta.url));
const esc = (s: string) => s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');

/** Strudel's share link: the code, UTF-8, base64, in the hash (core/util.mjs code2hash). */
const strudelUrl = (code: string) => `https://strudel.cc/#${encodeURIComponent(Buffer.from(code, 'utf8').toString('base64'))}`;

const SKETCHES: readonly [file: string, title: string, note: string][] = [
  ['safe', 'Her save-room theme', "RE1's shape, our tune: minor chords held under a slow harp arpeggio, an ocarina on top."],
  ['yard', 'The station yard', 'The hub she keeps coming back to: wind, a low piano note now and then, bowed chords that never resolve.'],
  ['chase', 'The mine, unarmed', 'The one fast piece: she has lost her gear and runs for the lift.'],
];

const KIND: Record<CueKind, string> = { new: 'New', reuse: "RE1's own", ambience: 'No music' };
const placeName = (id: string) => day.places.find((p) => p.id === id)?.name ?? id;
const sceneName = (id: string) => CUTSCENES.find(([s]) => s === id)?.[1] ?? id;

function page(): string {
  const sketches = SKETCHES.map(([file, title, note]) => {
    const code = readFileSync(path.join(here, 'sketches', `${file}.js`), 'utf8');
    return `<div class="sketch"><h3>${esc(title)}</h3><p>${esc(note)}</p>
<p><a class="play" href="${esc(strudelUrl(code))}" target="_blank" rel="noopener">Open in Strudel and press play</a></p>
<details><summary>The code</summary><pre>${esc(code)}</pre></details></div>`;
  }).join('\n');
  const cues = CUES.map((c) => {
    const where = [
      c.places.length ? c.places.map(placeName).join(', ') : '',
      c.cutscenes.length ? `Cutscenes: ${c.cutscenes.map(sceneName).join('; ')}` : '',
    ].filter(Boolean);
    return `<tr><td><b>${esc(c.title)}</b><br><span class="k k-${c.kind}">${KIND[c.kind]}</span>${c.sketch ? ' <span class="k">sketched</span>' : ''}</td>
<td>${esc(c.mood)}<div class="dim">${esc(c.sound)}</div></td>
<td>${where.map(esc).join('<br>')}<div class="dim">Channels: ${c.channels.map(esc).join('; ')}</div></td></tr>`;
  }).join('\n');
  const fresh = CUES.filter((c) => c.kind === 'new').length;
  return `<!doctype html>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Rebecca's day: music</title>
<style>
:root{--bg:#121110;--fg:#ddd6c8;--dim:#8b8478;--line:#2a2724;--accent:#c8963c;--ok:#7d9a5a}
body{background:var(--bg);color:var(--fg);font:15px/1.5 system-ui,sans-serif;max-width:1040px;margin:2em auto;padding:0 1em}
h1{font-weight:600;margin-bottom:.2em}h2{margin:1.8em 0 .4em;font-size:1.2em}h3{margin:.2em 0}
p,li{max-width:46em}.dim,.lede{color:var(--dim)}.dim{font-size:.88em;margin-top:.3em}
a{color:var(--accent)}.sketches{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:1em}
.sketch{border:1px solid var(--line);border-radius:6px;padding:.8em 1em}.sketch p{color:var(--dim);margin:.4em 0}
.play{display:inline-block;border:1px solid var(--accent);border-radius:4px;padding:.3em .8em;text-decoration:none}
pre{background:#1b1917;padding:.7em;overflow:auto;font-size:12px;line-height:1.4}
table{border-collapse:collapse;width:100%}td{border-top:1px solid var(--line);padding:.6em .5em;vertical-align:top}
td:first-child{width:12em}td:last-child{width:22em}
.k{font-size:.75em;border:1px solid var(--line);border-radius:3px;padding:0 .4em;color:var(--dim)}
.k-new{color:var(--accent);border-color:var(--accent)}.k-reuse{color:var(--ok);border-color:var(--ok)}
ol li,ul li{margin:.35em 0}
</style>
<h1>Rebecca's day: music</h1>
<p class="lede">Research, 15 October 2026. How RE1's music works, how we can make ours without playing an instrument, three sketches to listen to, and where every piece goes.</p>

<h2>Listen first</h2>
<p>Each link opens the sketch in Strudel, a music-as-code tool in the browser. Press play, or Ctrl+Enter. Change any number and press play again to hear the change. If one sounds close, send the edited link back through the pad.</p>
<p class="dim">These test the sound, not finished pieces. A script checked that each one parses and plays, using only CC0 sounds; nobody has listened to them yet.</p>
<div class="sketches">${sketches}</div>

<h2>What makes RE1 sound like RE1</h2>
<p>Hear it for yourself: <a href="../re1-music/">every track of RE1's music written out as Strudel code</a>, note for note from your PS1 disc, with the game's own instruments. Read its code beside ours.</p>
<ul>
<li>It was written in MIDI and played on the PlayStation over a tiny bank of samples: music got 256 KB. That is where the sound comes from: short looped samples at low quality, dull blurred reverb, a bit of grit.</li>
<li>Many rooms have no music at all, only wind, a clock, footsteps. The silence does as much as the music.</li>
<li>The save room theme is two or three minor chords and a short melody on a loop. Her save-room theme keeps that shape with a tune of ours.</li>
</ul>

<h2>How we make it</h2>
<ul>
<li><b>Write each piece as code in Strudel.</b> A piece is a short text file in the repository. Claude writes it; you judge it by ear and steer it ("slower", "darker", "less busy"), or change the numbers yourself.</li>
<li><b>Use only sounds we are allowed to ship.</b> VCSL is a free CC0 sample library with two pianos, a harp, bowed vibraphone, wineglass, organs, timpani and an anvil. Strudel's own synths make the pads and drones. The music we make with Strudel is ours.</li>
<li><b>No AI music generators.</b> None can render the same track twice from a file we keep, and their terms don't give us clean rights.</li>
<li><b>Render to WAV the same way every time,</b> then make it sound like a 1996 PlayStation: 22 kHz, mono, a little crushed.</li>
<li><b>The game is ready for it.</b> RE1 plays music from plain WAV files, and her mode's folder is searched first, so new tracks need no engine change. It also plays an intro once and loops the rest, and it plays up to three layers per room. A layer can join when something changes: the generator hum once the power is on, the mill once the race fills.</li>
<li><b>One engine change is needed.</b> Which music plays in which room is a table compiled into the game. Her rooms borrow slots that are silent, so her day has no music today. Her mode needs its own table, read from her folder, so Chris's and Jill's games stay as they are.</li>
</ul>

<h2>Where every piece goes</h2>
<p>${CUES.length} cues: ${fresh} new pieces, ${CUES.filter((c) => c.kind === 'ambience').length} with no music, and RE1's own save room music at the end, played from the player's own game. Every room and cutscene is covered, and a test keeps it that way.</p>
<table>${cues}</table>

<h2>The plan</h2>
<ol>
<li><b>Choose the sound.</b> You listen to the sketches and say what is right and wrong.</li>
<li><b>Render one sketch to a WAV,</b> by hand first, then with one command that gives the same file every time.</li>
<li><b>Make it sound like the PlayStation:</b> 22 kHz mono and some grit. Compare it with RE1's own tracks by ear.</li>
<li><b>Add loop points,</b> so the intro plays once and the loop joins without a click.</li>
<li><b>Give her mode its own music table.</b> Done when a test track plays in the yard in her mode and Jill's hall music hasn't changed.</li>
<li><b>Write the pieces,</b> in order of how long she hears them:
<ol>
<li>the station;</li>
<li>her save-room theme;</li>
<li>the camp, the road and the mine;</li>
<li>the chase;</li>
<li>the dawn, the partner's and Hal's themes;</li>
<li>the rest;</li>
<li>the credits last, built from the others.</li>
</ol></li>
<li><b>Make the layers react</b> to what she has done.</li>
<li><b>Test it:</b> the harness walks the day and checks which track each room plays.</li>
</ol>

<h2>Questions for you</h2>
<ul>
<li>Do the sketches sound like the right world, or should we try a more orchestral sample library? Some need a credit line.</li>
<li>Should the save room at the end use RE1's own save-room music? It's the moment the player knows they're home.</li>
<li>How big can the download be? Fifteen two-minute tracks at RE1's quality come to about 80 MB, or half that at 8-bit.</li>
</ul>
<p class="dim">Made ${new Date().toISOString().slice(0, 16).replace('T', ' ')} UTC from tools/rebecca/plan/music.ts and tools/rebecca/music/sketches/. The write-up with sources is docs/REBECCA_MUSIC.md.</p>
`;
}

const out = process.argv[2];
if (!out) {
  console.error('usage: node tools/rebecca/music/page.ts <outdir>');
  process.exit(2);
}
mkdirSync(out, { recursive: true });
writeFileSync(path.join(out, 'index.html'), page());
console.log(path.join(out, 'index.html'));
