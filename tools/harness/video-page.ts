// A review page for a recorded playthrough: the video, and every event the
// run logged as a link that jumps the video there, grouped by chapter.
//
//   node tools/harness/video-page.ts <run log> <video file name> <out.html> [title] [scale]
// The log is full-playthrough.ts's output; its [Ns] stamps are seconds of the
// run. `scale` (video seconds per run second, default 1) corrects a video
// whose capture fell behind real time. The video file name is written as given, relative to the page.
import { readFileSync, writeFileSync } from 'node:fs';

const [logPath, video, outPath, title = "Rebecca's scenario: full playthrough", scaleArg = '1'] = process.argv.slice(2);
const scale = Number(scaleArg);
if (!logPath || !video || !outPath) {
  console.error('usage: node tools/harness/video-page.ts <run log> <video file name> <out.html> [title]');
  process.exit(1);
}

/** Where each chapter's function starts, by the first event it logs. */
const chapterStarts: [RegExp, string][] = [
  [/^on the ridge$/, 'Act 1: dawn on the mountain'],
  [/^at the lookout$/, "The ranger's lookout"],
  [/in the mountain trail/, 'Prologue and Chapter 1: the back way in'],
  [/in the save room after the meeting/, "Chapter 2: Bravo's medic"],
  [/in the bar$/, 'Chapter 3: Moonlight'],
  [/in the guardhouse passage/, 'Chapter 4: the guardhouse'],
  [/in the power room/, 'Chapter 5: underground'],
  [/on the stairs, enemies/, 'Chapter 6: the hunters, and the epilogue'],
];

type Event = { t: number; room: string; hp: string; what: string };
const events: Event[] = [];
let result = '';
for (const line of readFileSync(logPath, 'utf8').split('\n')) {
  const m = /^\[(\d+)s\] (\S+) hp (\S+) (.*)$/.exec(line);
  if (m) events.push({ t: Math.round(Number(m[1]) * scale), room: m[2], hp: m[3], what: m[4] });
  else if (/^(PASS|FAIL)/.test(line)) result = line;
  else if (/^ {2}FAILED: /.test(line)) events.push({ t: events.at(-1)?.t ?? 0, room: '', hp: '', what: line.trim() });
}

const esc = (s: string) => s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
const clock = (t: number) => `${Math.floor(t / 60)}:${String(t % 60).padStart(2, '0')}`;
let body = '';
let open = false;
for (const e of events) {
  const chapter = chapterStarts.find(([re]) => re.test(e.what));
  if (chapter) {
    if (open) body += '</ol></section>\n';
    body += `<section><h2>${esc(chapter[1])}</h2><ol>\n`;
    open = true;
  }
  const failed = e.what.startsWith('FAILED');
  body += `<li${failed ? ' class="failed"' : ''}><a href="#t=${e.t}" data-t="${e.t}">${clock(e.t)}</a> <span class="room">${esc(e.room ? `ROOM${e.room}0` : '')}</span> ${esc(e.what)}${e.hp && !failed ? ` <span class="hp">${esc(e.hp)} HP</span>` : ''}</li>\n`;
}
if (open) body += '</ol></section>\n';

writeFileSync(outPath, `<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>${esc(title)}</title>
<style>
  body { margin: 0; background: #111; color: #ddd; font: 15px/1.45 system-ui, sans-serif; }
  main { max-width: 1100px; margin: 0 auto; padding: 16px; display: grid; gap: 16px; grid-template-columns: minmax(0, 3fr) minmax(260px, 2fr); }
  header { grid-column: 1 / -1; }
  h1 { font-size: 20px; margin: 0 0 4px; }
  header p { margin: 0; color: #999; }
  .player { position: sticky; top: 16px; align-self: start; }
  video { width: 100%; background: #000; image-rendering: pixelated; }
  .events { max-height: calc(100vh - 120px); overflow: auto; }
  h2 { font-size: 15px; margin: 14px 0 4px; color: #e8b04a; }
  ol { list-style: none; margin: 0; padding: 0; }
  li { padding: 3px 6px; border-radius: 4px; }
  li.now { background: #2a2a2a; }
  li.failed { color: #ff7a6b; }
  a { color: #7fb8ff; font-variant-numeric: tabular-nums; text-decoration: none; }
  .room { color: #888; font-size: 13px; }
  .hp { color: #8c8; font-size: 13px; }
  @media (max-width: 760px) { main { grid-template-columns: 1fr; } .player { position: static; } .events { max-height: none; } }
</style>
</head>
<body>
<main>
<header>
  <h1>${esc(title)}</h1>
  <p>Played by the test harness from a new game to the title after the ending. ${esc(result)}. No sound: the recording machine has no loopback audio device. Click a time to jump there.</p>
</header>
<div class="player"><video id="v" src="${esc(video)}" controls preload="metadata"></video></div>
<div class="events">
${body}</div>
</main>
<script>
  const v = document.getElementById('v');
  const items = [...document.querySelectorAll('a[data-t]')];
  for (const a of items) a.addEventListener('click', (e) => { e.preventDefault(); v.currentTime = Number(a.dataset.t); v.play(); });
  v.addEventListener('timeupdate', () => {
    let current;
    for (const a of items) if (Number(a.dataset.t) <= v.currentTime) current = a;
    for (const a of items) a.parentElement.classList.toggle('now', a === current);
  });
  const m = /t=(\\d+)/.exec(location.hash);
  if (m) v.currentTime = Number(m[1]);
</script>
</body>
</html>
`);
console.log(`wrote ${outPath} with ${events.length} events`);
