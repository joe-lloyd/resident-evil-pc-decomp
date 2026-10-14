// Lay Rebecca's files out for the owner to read and rate: every page as the
// reader would show it, its words beside it, and a rating for the writing
// and the pages of each document. Ratings stay in that browser; "Copy my
// ratings" puts them on the clipboard to hand back.
//
//   node tools/rebecca/files/review.ts <outdir>
import { mkdirSync, writeFileSync } from 'node:fs';
import path from 'node:path';
import { encodePng } from '../../harness/image.ts';
import { DOCUMENTS, type Doc, type Page } from './documents.ts';
import { drawPage, packPix, toImage } from './pages.ts';

const out = process.argv[2];
if (!out) throw new Error('usage: node tools/rebecca/files/review.ts <outdir>');
mkdirSync(path.join(out, 'pages'), { recursive: true });

const esc = (s: string) => s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');

/** The words on a page, as the owner should read them beside its picture. */
function words(doc: Doc, page: Page): string {
  switch (page.kind) {
    case 'title':
      return [doc.title, doc.subtitle].filter(Boolean).join('\n');
    case 'text':
      return page.text.trim().replace(/^[>^]/gm, '');
    case 'calendar':
      return `${page.company}\n${page.town}\n${page.month}\n\nRinged in red: ${page.circled.join(', ')}\nIn the boxes: ${Object.entries(page.notes).map(([d, n]) => `${d} ${n}`).join(', ')}\nAcross the bottom: ${page.scrawl}`;
    case 'map':
      return `${page.heading}\n${page.sub}\n\nMarked: ${page.labels.map(([s]) => s).join(', ')}\nIn red pencil: ${page.notes.map(([s]) => s).join(' ')}\nA bloody thumbprint on No.3 level.`;
    case 'notice':
      return `${page.heading}\n${page.lines.join('\n')}\n(torn off here)`;
    case 'roster':
      return `${page.company}\n${page.heading}\n\n${page.rows.map((r) => `${r.name.padEnd(13)}${r.days.map((d) => (d === 'in' ? 'in  ' : d === 'sick' ? 'SICK' : '--  ')).join(' ')}${r.struck ? '  (struck out)' : ''}`).join('\n')}${page.foot ? `\n\n${page.foot}` : ''}`;
    default:
      return page satisfies never;
  }
}

let pages = 0;
const sections = DOCUMENTS.map((doc, n) => {
  const figures = doc.pages.map((page, i) => {
    const paper = `pages/${doc.id}-${i}.png`;
    writeFileSync(path.join(out, paper), encodePng(toImage(drawPage(doc, i))));
    let black = paper;
    if (page.kind === 'text') {
      black = `pages/${doc.id}-${i}-black.png`;
      writeFileSync(path.join(out, black), encodePng(toImage(drawPage(doc, i, 'black'))));
    }
    pages++;
    return `<figure><a href="${paper}" data-paper="${paper}" data-black="${black}"><img src="${paper}" data-paper="${paper}" data-black="${black}" width="384" height="384" alt="${esc(doc.title)}, page ${i + 1}"></a><figcaption><b>Page ${i + 1}</b><pre>${esc(words(doc, page))}</pre></figcaption></figure>`;
  });
  const pix = packPix(doc.pages.map((_, i) => drawPage(doc, i)));
  const notes = (doc.notes ?? []).map((t) => `<p class="decide">To decide: ${esc(t)}</p>`).join('');
  const stars = (what: string) =>
    `<span class="stars" data-doc="${doc.id}" data-what="${what}">${[1, 2, 3, 4, 5].map((v) => `<button type="button" data-v="${v}" aria-label="${what} ${v} of 5">★</button>`).join('')}</span>`;
  return `<section id="${doc.id}">
<h2>${n + 1}. ${esc(doc.title)}</h2>
<p class="meta">${esc(doc.writer)}. ${esc(doc.where)} File slot ${doc.slot}, ${doc.pages.length} pages, ${(pix.length / 1024).toFixed(1)} KB packed.</p>
${notes}
<div class="rate"><label>Writing ${stars('words')}</label><label>Pages ${stars('pages')}</label><textarea data-doc="${doc.id}" rows="2" placeholder="What to change"></textarea></div>
<div class="strip">${figures.join('\n')}</div>
</section>`;
});

const html = `<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Rebecca's files: review</title>
<style>
:root{--bg:#121110;--fg:#ddd6c8;--dim:#8b8478;--line:#2a2724;--gold:#c8963c;--good:#7d9a5a}
body{background:var(--bg);color:var(--fg);font:15px/1.45 system-ui,sans-serif;max-width:1400px;margin:1.5em auto;padding:0 1em}
h1{font-weight:600;margin:.2em 0}h2{margin:1.8em 0 .2em;font-size:1.2em}p{margin:.3em 0 .5em}.meta,.lede{color:var(--dim)}
.decide{color:var(--gold)}
.tools{display:flex;flex-wrap:wrap;gap:.6em;align-items:center;position:sticky;top:0;background:var(--bg);padding:.6em 0;z-index:1;border-bottom:1px solid var(--line)}
.tools button{background:#1d1b19;color:var(--fg);border:1px solid #3a3632;border-radius:4px;padding:.35em .7em;font:inherit;cursor:pointer}
.tools button[aria-pressed=true]{border-color:var(--gold);color:var(--gold)}#status{color:var(--dim);font-size:.9em}#copied{color:var(--good)}
.rate{display:flex;flex-wrap:wrap;gap:1.2em;align-items:center;margin:.4em 0 .8em}.rate textarea{flex:1;min-width:16em;background:#1d1b19;color:var(--fg);border:1px solid #3a3632;border-radius:4px;font:inherit;padding:.3em .5em}
.stars button{all:unset;cursor:pointer;font-size:1.35em;color:#3a3632;padding:0 .05em}.stars button.on{color:var(--gold)}
.strip{display:flex;gap:1em;overflow-x:auto;padding-bottom:.6em}
figure{margin:0;flex:0 0 384px}figure img{display:block;image-rendering:pixelated;background:#000;border:1px solid var(--line)}
figcaption b{display:block;margin:.4em 0 .2em;color:var(--dim);font-weight:500;font-size:.85em}
pre{white-space:pre-wrap;font:13px/1.4 ui-monospace,Menlo,monospace;margin:0;color:var(--fg)}
nav a{color:var(--dim);margin-right:.8em}
</style></head><body>
<h1>Rebecca's files</h1>
<p class="lede">The ten papers she reads on her day, drawn as RE1 file pages: 256 by 256 pixels, 16 colours, packed in the game's own format. Each page is shown at twice its size, with its words beside it. Rate the writing and the pages of each file, then press Copy my ratings and paste the result back. Ratings stay in this browser until you copy them.</p>
<p class="lede">The first page of each file is its title on black, as in RE1. The text pages come in two looks: on paper (a notebook, a ledger, a typed letter), or RE1's own light type on black. Switch between them below, and say which you want.</p>
<p class="decide">In the game, the reader shows only the top 192 of each page's 256 rows, so the bottom quarter of these pages is cut off. Screenshots of every file picked up and read in the game are on <a href="game/" style="color:var(--gold)">the in-game page</a>.</p>
<p class="lede">Everything still to do for her day is on the tracker: <a href="https://home.arpa/research/rebecca-todo/" style="color:var(--fg)">home.arpa/research/rebecca-todo</a>.</p>
<nav>${DOCUMENTS.map((d) => `<a href="#${d.id}">${esc(d.title)}</a>`).join('')}</nav>
<div class="tools">
<span>Text pages:</span><button type="button" data-look="paper" aria-pressed="true">On paper</button><button type="button" data-look="black" aria-pressed="false">RE1 black</button>
<button type="button" id="copy">Copy my ratings</button><span id="status"></span><span id="copied"></span>
</div>
${sections.join('\n')}
<p class="meta">${DOCUMENTS.length} files, ${pages} pages. Made ${new Date().toISOString().slice(0, 16).replace('T', ' ')} UTC by tools/rebecca/files/review.ts.</p>
<script>
const KEY = 'reb-files-ratings-v1';
const DOCS = ${JSON.stringify(DOCUMENTS.map((d) => ({ id: d.id, title: d.title })))};
const state = JSON.parse(localStorage.getItem(KEY) || '{"look":"paper","docs":{}}');
const save = () => { localStorage.setItem(KEY, JSON.stringify(state)); paint(); };
const doc = (id) => (state.docs[id] ||= {});
function paint() {
  document.querySelectorAll('.stars').forEach((el) => {
    const v = (state.docs[el.dataset.doc] || {})[el.dataset.what] || 0;
    el.querySelectorAll('button').forEach((b) => b.classList.toggle('on', +b.dataset.v <= v));
  });
  document.querySelectorAll('[data-look]').forEach((b) => b.setAttribute('aria-pressed', String(b.dataset.look === state.look)));
  document.querySelectorAll('img[data-paper]').forEach((img) => { img.src = img.dataset[state.look]; img.parentElement.href = img.dataset[state.look]; });
  const rated = DOCS.filter((d) => state.docs[d.id]?.words && state.docs[d.id]?.pages).length;
  document.getElementById('status').textContent = rated + ' of ' + DOCS.length + ' files rated';
}
document.querySelectorAll('.stars button').forEach((b) => b.addEventListener('click', () => {
  const el = b.parentElement, d = doc(el.dataset.doc);
  d[el.dataset.what] = d[el.dataset.what] === +b.dataset.v ? 0 : +b.dataset.v;
  save();
}));
document.querySelectorAll('textarea[data-doc]').forEach((t) => {
  t.value = (state.docs[t.dataset.doc] || {}).note || '';
  t.addEventListener('input', () => { doc(t.dataset.doc).note = t.value; save(); });
});
document.querySelectorAll('[data-look]').forEach((b) => b.addEventListener('click', () => { state.look = b.dataset.look; save(); }));
document.getElementById('copy').addEventListener('click', async () => {
  const lines = ["Rebecca's files: my ratings", 'Text pages: ' + (state.look === 'black' ? 'RE1 black' : 'on paper'), ''];
  for (const d of DOCS) {
    const r = state.docs[d.id] || {};
    lines.push(d.title + ' (' + d.id + '): writing ' + (r.words || '-') + '/5, pages ' + (r.pages || '-') + '/5');
    if (r.note) lines.push('  ' + r.note.replace(/\\n/g, '\\n  '));
  }
  const text = lines.join('\\n');
  try { await navigator.clipboard.writeText(text); document.getElementById('copied').textContent = 'Copied.'; }
  catch { prompt('Copy this:', text); }
});
paint();
</script>
</body></html>
`;
writeFileSync(path.join(out, 'index.html'), html);
console.log(`${DOCUMENTS.length} files, ${pages} pages -> ${out}`);
