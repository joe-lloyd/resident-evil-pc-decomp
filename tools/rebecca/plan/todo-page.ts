// Draw what Rebecca's day still needs (todo.ts) as one page: progress by
// section and overall, a row per thing with its status. Ticking a row keeps
// the tick in that browser, and "Copy my changes" puts the ticks on the
// clipboard to hand back, to be set in todo.ts.
//
//   node tools/rebecca/plan/todo-page.ts <outdir>
import { existsSync, mkdirSync, readFileSync, readdirSync, writeFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { day } from './day.ts';
import { sections, type Facts, type RoomFacts, type Status } from './todo.ts';

const here = path.dirname(fileURLToPath(import.meta.url));
const dayDir = path.join(here, '..', 'day');

interface RoomJson {
  doors?: { to: string }[];
  checks?: unknown[];
  entry?: string | null;
}

function readFacts(): Facts {
  const rooms = new Map<string, RoomFacts>();
  for (const slug of readdirSync(dayDir)) {
    const file = path.join(dayDir, slug, 'renders', 'room.json');
    if (!existsSync(file)) continue;
    const json = JSON.parse(readFileSync(file, 'utf8')) as RoomJson;
    rooms.set(slug, { doors: (json.doors ?? []).map((d) => d.to), checks: json.checks?.length ?? 0, entry: Boolean(json.entry) });
  }
  return { rooms };
}

const esc = (s: string) => s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
const LABEL: Record<Status, string> = { done: 'Done', doing: 'Under way', todo: 'To do' };

function page(): string {
  const all = sections(day, readFacts());
  const count = (s: Status) => all.reduce((n, sec) => n + sec.items.filter((i) => i.status === s).length, 0);
  const total = all.reduce((n, sec) => n + sec.items.length, 0);
  const body = all
    .map((sec) => {
      const done = sec.items.filter((i) => i.status === 'done').length;
      const doing = sec.items.filter((i) => i.status === 'doing').length;
      const rows = sec.items
        .map(
          (i) => `<li data-id="${esc(i.id)}" data-status="${i.status}"><label><input type="checkbox"${i.status === 'done' ? ' checked' : ''}><span class="t">${esc(i.title)}</span>${i.note ? `<span class="n">${esc(i.note)}</span>` : ''}<span class="s">${LABEL[i.status]}</span></label></li>`,
        )
        .join('');
      // A section with nothing left starts folded, so what's left comes first.
      const open = done < sec.items.length;
      const hide = open ? '' : ' class="hide"';
      return `<section data-section="${sec.id}"><h2><button class="fold" aria-expanded="${open}">${esc(sec.title)}</button><span class="c"><b class="d">${done}</b> of ${sec.items.length}${doing ? `, ${doing} under way` : ''}</span></h2>
<div class="bar"><i style="width:${(100 * done) / sec.items.length}%"></i><i class="w" style="width:${(100 * doing) / sec.items.length}%"></i></div>
<p${hide}>${esc(sec.blurb)}</p><ul${hide}>${rows}</ul></section>`;
    })
    .join('\n');
  const done = count('done');
  const doing = count('doing');
  return `<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Rebecca's day: what's left</title>
<script src="/research/rebecca-day/nav.js" defer></script>
<style>
:root{--bg:#121110;--fg:#ddd6c8;--dim:#8b8478;--line:#2a2724;--done:#7d9a5a;--doing:#c8963c;--todo:#5a5550;--mine:#5f8fb0}
body{background:var(--bg);color:var(--fg);font:15px/1.45 system-ui,sans-serif;max-width:980px;margin:2em auto;padding:0 1em}
h1{font-weight:600;margin-bottom:.2em}h2{display:flex;align-items:baseline;gap:1em;margin:1.6em 0 .3em;font-size:1.15em}
.fold{all:unset;cursor:pointer;font-weight:600}.fold::before{content:"▾ ";color:var(--dim)}.fold[aria-expanded=false]::before{content:"▸ "}
.c{color:var(--dim);font-size:.85em;font-weight:400}p{color:var(--dim);margin:.3em 0 .6em}
.bar{height:6px;background:var(--line);display:flex;border-radius:3px;overflow:hidden}.bar i{background:var(--done)}.bar i.w{background:var(--doing)}
.big{height:12px;margin:.6em 0 1.2em}
ul{list-style:none;padding:0;margin:0}li{border-bottom:1px solid var(--line)}
label{display:grid;grid-template-columns:1.6em 1fr auto;grid-template-rows:auto auto;column-gap:.5em;padding:.45em .2em;cursor:pointer}
label input{grid-row:1/3;margin-top:.25em;accent-color:var(--done)}.t{grid-column:2}.n{grid-column:2;color:var(--dim);font-size:.88em}
.s{grid-column:3;grid-row:1;font-size:.8em;color:var(--todo)}li[data-status=done] .s{color:var(--done)}li[data-status=doing] .s{color:var(--doing)}
li[data-status=done] .t{color:var(--dim)}li.mine .s::after{content:" (your tick)";color:var(--mine)}
.tools{display:flex;flex-wrap:wrap;gap:.5em;align-items:center;position:sticky;top:0;background:var(--bg);padding:.6em 0;z-index:1;border-bottom:1px solid var(--line)}
.tools button,.tools input{background:#1d1b19;color:var(--fg);border:1px solid #3a3632;border-radius:4px;padding:.35em .7em;font:inherit}
.tools button[aria-pressed=true]{border-color:var(--doing);color:var(--doing)}.tools input{flex:1;min-width:10em}
#copied{color:var(--done);font-size:.85em}.hide{display:none}section.empty{display:none}
</style>
<h1>Rebecca's day: what's left</h1>
<p>Everything that makes it a whole game, from the plan and the repository. Rows the repository can show, such as a room with its renders or a path joined at both ends, are worked out each time this page is made. Tick a row when you see it working: the tick stays in this browser, and <b>Copy my changes</b> gives you a list to paste back to Claude, who records it for everyone.</p>
<div class="bar big"><i style="width:${(100 * done) / total}%"></i><i class="w" style="width:${(100 * doing) / total}%"></i></div>
<p><b id="total-done">${done}</b> of ${total} done, ${doing} under way. Made ${new Date().toISOString().slice(0, 16).replace('T', ' ')} UTC.</p>
<div class="tools"><button data-filter="all" aria-pressed="true">All</button><button data-filter="todo" aria-pressed="false">Still to do</button><button data-filter="done" aria-pressed="false">Done</button><input type="search" placeholder="Search" aria-label="Search"><button id="copy">Copy my changes</button><button id="reset">Clear my ticks</button><span id="copied"></span></div>
${body}
<script>
const KEY = 'rebecca-todo-v1';
const mine = JSON.parse(localStorage.getItem(KEY) || '{}');
const rows = [...document.querySelectorAll('li[data-id]')];
const save = () => localStorage.setItem(KEY, JSON.stringify(mine));
function paint() {
  for (const li of rows) {
    const id = li.dataset.id, base = li.dataset.status, box = li.querySelector('input');
    const ticked = id in mine ? mine[id] : base === 'done';
    box.checked = ticked;
    li.classList.toggle('mine', id in mine);
    li.dataset.shown = ticked ? 'done' : base === 'doing' ? 'doing' : 'todo';
  }
  for (const sec of document.querySelectorAll('section')) {
    const r = [...sec.querySelectorAll('li')];
    sec.querySelector('.d').textContent = r.filter((li) => li.dataset.shown === 'done').length;
  }
  document.getElementById('total-done').textContent = rows.filter((li) => li.dataset.shown === 'done').length;
  filter();
}
let mode = 'all';
function filter() {
  const q = document.querySelector('.tools input').value.toLowerCase();
  for (const li of rows) {
    const hit = !q || li.textContent.toLowerCase().includes(q);
    const want = mode === 'all' || (mode === 'done' ? li.dataset.shown === 'done' : li.dataset.shown !== 'done');
    li.classList.toggle('hide', !(hit && want));
  }
  for (const sec of document.querySelectorAll('section')) sec.classList.toggle('empty', !sec.querySelector('li:not(.hide)'));
}
for (const li of rows) li.querySelector('input').addEventListener('change', (e) => {
  const id = li.dataset.id, base = li.dataset.status === 'done';
  if (e.target.checked === base) delete mine[id]; else mine[id] = e.target.checked;
  save(); paint();
});
for (const b of document.querySelectorAll('[data-filter]')) b.addEventListener('click', () => {
  mode = b.dataset.filter;
  for (const x of document.querySelectorAll('[data-filter]')) x.setAttribute('aria-pressed', String(x === b));
  filter();
});
document.querySelector('.tools input').addEventListener('input', filter);
for (const f of document.querySelectorAll('.fold')) f.addEventListener('click', () => {
  const open = f.getAttribute('aria-expanded') === 'true';
  f.setAttribute('aria-expanded', String(!open));
  for (const el of f.closest('section').querySelectorAll('ul,p,.bar')) el.classList.toggle('hide', open);
});
document.getElementById('copy').addEventListener('click', async () => {
  const lines = Object.entries(mine).map(([id, v]) => {
    const li = rows.find((r) => r.dataset.id === id);
    return (v ? 'done: ' : 'not done: ') + (li ? li.querySelector('.t').textContent : '') + ' [' + id + ']';
  });
  const text = lines.length ? "Rebecca's day, my ticks:\\n" + lines.join('\\n') : 'No ticks of my own yet.';
  try { await navigator.clipboard.writeText(text); document.getElementById('copied').textContent = lines.length + ' copied'; }
  catch { prompt('Copy this:', text); }
});
document.getElementById('reset').addEventListener('click', () => {
  if (!confirm('Clear your ticks in this browser?')) return;
  for (const k of Object.keys(mine)) delete mine[k];
  save(); paint();
});
paint();
</script>
`;
}

const out = process.argv[2];
if (!out) throw new Error('usage: todo-page.ts <outdir>');
mkdirSync(out, { recursive: true });
writeFileSync(path.join(out, 'index.html'), page());
console.log(`${path.join(out, 'index.html')} written`);
