// The player page for RE1's music in Strudel (re1.ts writes the tracks): each
// track's code in an editable box with Play and Stop, on the game's samples
// and, where re1.ts wrote one, on free sounds. Run by Strudel's own
// browser build next to the page, so the game's samples load from the same
// site. LAN only: this is Capcom's music from the player's disc.
//
//   node tools/rebecca/music/page-re1.ts <outdir from re1.ts> <@strudel/web 1.2.5 dist folder>
import { cpSync, readFileSync, writeFileSync } from 'node:fs';
import path from 'node:path';
import type { Track } from './re1.ts';

type Meta = Omit<Track, 'code' | 'played'> & { free?: boolean };
const esc = (s: string) => s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
const title = (rooms: readonly string[]) => (rooms[0] ?? 'Not placed in a room').toLowerCase().replace(/^./, (c) => c.toUpperCase());

const version = (kind: 'game' | 'free', label: string, code: string) =>
  `<div class="version" data-version="${kind}"><button data-play>${label}</button>
<details><summary>The code</summary><textarea spellcheck="false" rows="24">${esc(code)}</textarea></details></div>`;

function card(t: Meta, code: string, free: string | undefined): string {
  const where = t.rooms.length ? t.rooms.map((r) => r.toLowerCase()).join(', ') : 'no room in the PC table';
  return `<section class="track" id="${t.id}">
<h3>${esc(title(t.rooms))} <span class="dim">${esc(t.name ?? 'no PC name')} · ${t.id}</span></h3>
<p class="dim">${t.bpm} BPM, ${t.bars} bars, ${t.notes} notes in ${t.voices} voices. Plays in: ${esc(where)}.</p>
<div class="versions">${version('game', "Play on the game's samples", code)}${free ? version('free', 'Play on free sounds', free) : ''}<button data-stop>Stop</button></div>
</section>`;
}

const [out, web] = process.argv.slice(2);
if (!out || !web) {
  console.error('usage: node tools/rebecca/music/page-re1.ts <outdir> <@strudel/web dist folder>');
  process.exit(2);
}
const tracks = JSON.parse(readFileSync(path.join(out, 'tracks.json'), 'utf8')) as Meta[];
const named = (prefix: string) => tracks.filter((t) => t.name?.startsWith(prefix));
const music = named('Bgm_');
const loops = tracks.filter((t) => !music.includes(t));
const cards = (list: Meta[]) =>
  list.map((t) => card(t, readFileSync(path.join(out, `${t.id}.js`), 'utf8'), t.free ? readFileSync(path.join(out, `${t.id}.free.js`), 'utf8') : undefined)).join('\n');
cpSync(web, path.join(out, 'strudel'), { recursive: true });
writeFileSync(path.join(out, 'index.html'), `<!doctype html>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>RE1's music in Strudel</title>
<style>
:root{--bg:#121110;--fg:#ddd6c8;--dim:#8b8478;--line:#2a2724;--accent:#c8963c}
body{background:var(--bg);color:var(--fg);font:15px/1.5 system-ui,sans-serif;max-width:1040px;margin:2em auto;padding:0 1em}
h1{font-weight:600;margin-bottom:.2em}h2{margin:1.8em 0 .4em;font-size:1.2em}h3{margin:.2em 0;font-size:1.05em}
p,li{max-width:48em}.dim{color:var(--dim);font-size:.9em;font-weight:400}
a{color:var(--accent)}.track{border-top:1px solid var(--line);padding:.6em 0}
button{background:none;color:var(--accent);border:1px solid var(--accent);border-radius:4px;padding:.25em .9em;font:inherit;cursor:pointer}
button.on{background:var(--accent);color:var(--bg)}
textarea{width:100%;box-sizing:border-box;background:#1b1917;color:var(--fg);border:1px solid var(--line);font:12px/1.4 ui-monospace,monospace;padding:.6em}
.versions{display:flex;flex-wrap:wrap;gap:.5em 1em;align-items:flex-start}.version{flex:1 1 20em}.versions>button{align-self:flex-start}
#status{position:sticky;top:0;background:var(--bg);padding:.4em 0;color:var(--dim);font-size:.9em;border-bottom:1px solid var(--line)}
</style>
<h1>RE1's music in Strudel</h1>
<p>Every piece of music on the PS1 disc, written out as Strudel code: ${music.length} tracks of music and ${loops.length} sound loops. The notes and their timing are the disc's own, checked note for note by a script, and the instruments are the game's own samples. The envelopes are worked out from the game's sound bank, so they are close but not exact. Pitch bends and the PS1's reverb are missing, so leads that slide in the game hold still here.</p>
<p>Each track plays two ways. <b>On the game's samples</b> is as close to the game as Strudel gets. <b>On free sounds</b> plays the same notes on sounds we are allowed to use: VCSL, a CC0 sample library, and Strudel's own synths. A script picked each free sound by measuring the game's sample it replaces: its harmonics, how noisy and how bright it is, how it fades. Its low-pass filter is set to match how muffled the game's sample is. Nobody picked them by ear yet, so some will be wrong. Say which and they get fixed.</p>
<p>Open the code, change anything and press Play again. One bar is one cycle, so a track's code lines up bar by bar with the others, and with ours.</p>
<p class="dim">Made from your own disc and shown only on the home network. It is Capcom's music, so none of it goes in the public repositories. Rebuild it with <code>pnpm rae music</code> and <code>tools/rebecca/music/re1.ts</code>.</p>
<p>To open them elsewhere, <a href="re1-music-strudel.zip">download them all</a>. That zip holds every track in both versions and the game's samples, with a README that lists each track's rooms. Or open any track's own file: <code>SEP0F-0.js</code> is on the game's samples, and <code>SEP0F-0.free.js</code> is on free sounds.</p>
<div id="status">Loading Strudel…</div>
<h2>Music</h2>
${cards(music)}
<h2>Sound loops and unplaced tracks</h2>
${cards(loops)}
<script src="strudel/index.js"></script>
<script>
const status = document.getElementById('status');
const ready = initStrudel().then(() => { status.textContent = 'Ready. Press Play on any track.'; });
let playing;
document.addEventListener('click', async (e) => {
  const b = e.target.closest('button');
  if (!b) return;
  if (b.dataset.stop !== undefined) {
    strudel.hush();
    playing?.classList.remove('on');
    status.textContent = 'Stopped.';
    return;
  }
  const card = b.closest('.track');
  const v = b.closest('.version');
  await ready;
  try {
    status.textContent = 'Loading ' + card.id + '…';
    await strudel.evaluate(v.querySelector('textarea').value);
    playing?.classList.remove('on');
    playing = b;
    b.classList.add('on');
    status.textContent = 'Playing ' + card.querySelector('h3').firstChild.textContent.trim() + ' (' + card.id + ') on ' + (v.dataset.version === 'free' ? 'free sounds.' : "the game's samples.");
  } catch (err) {
    status.textContent = 'Error in ' + card.id + ': ' + err.message;
  }
});
</script>
`);
console.log(`${path.join(out, 'index.html')}: ${music.length} music tracks, ${loops.length} loops`);
