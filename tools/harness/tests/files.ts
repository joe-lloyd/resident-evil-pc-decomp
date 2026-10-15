// Pick up each of Rebecca's files where its room gives it, read every page,
// and find it in the FILE tab. Each page the game draws is compared with the
// page files/pages.ts drew, and every step is saved as a screenshot.
//
//   PORT=7811 node tools/harness/tests/files.ts [<outdir>] [<file id> ...]
//
// Needs the engine and the overlay deployed (docs/REBECCA_FILES.md), with the
// day's room scripts written by day/scripts.ts. Writes <outdir>/index.html
// (default /tmp/rebecca-files-game) and exits 1 if any file fails.
import { mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { open } from '../lab.ts';
import { Key, type GameLink } from '../link.ts';
import { approach, settle, useRoomData } from '../flows.ts';
import { snapshot } from '../snapshot.ts';
import { readPng, type Image } from '../image.ts';
import type { GameState } from '../state.ts';
import { dayRooms } from '../../rebecca/day/rooms.ts';
import { BOOKS, DOCUMENTS, type Doc } from '../../rebecca/files/documents.ts';
import { fileName } from '../../rebecca/files/engine.ts';
import { drawPage, toImage } from '../../rebecca/files/pages.ts';

const here = path.dirname(fileURLToPath(import.meta.url));
const dayDir = path.join(here, '..', '..', 'rebecca', 'day');
const args = process.argv.slice(2);
const outDir = args[0] && !BOOKS.includes(args[0] as (typeof BOOKS)[number]) ? args.shift()! : '/tmp/rebecca-files-game';
const wanted = args.length ? args : [...BOOKS];
const docs = wanted.map((id) => DOCUMENTS.find((d) => d.id === id) ?? fail(`no file ${id}`));
mkdirSync(outDir, { recursive: true });
useRoomData([process.env.RE1_OVERLAY ?? '/tmp/reb-files-out/REB', process.env.RE1_BASE ?? '/tmp/re1-pc']);

function fail(message: string): never {
  throw new Error(message);
}

/** MSF_PICKUP_SCREEN (src/Globals.h): the file reader a pickup opens. */
const PICKUP_SCREEN = 0x100;
/** Bank 8 is g_RoomFlags; a collected file raises ROOM_FLAG_FILE_BASE + slot (src/game/BioCard.h). */
const FILE_FLAGS = 8;
const FILE_FLAG_BASE = 0x82;
const flagOn = (s: GameState, bank: number, n: number) => ((s.banks[bank]![(n >> 5) * 4 + 3 - ((n & 31) >> 3)]! >> (7 - (n & 7))) & 1) === 1;

/** The reader draws a page's top 256x192 at (24, 24) of the 320x240 screen (DAT_004d2888); the shot is twice that. */
const PAGE_X = 48;
const PAGE_Y = 48;
const SHOWN_W = 512;
const SHOWN_H = 384;

/** Mean difference per channel between the shot's page and ours, over the part the reader shows. */
function pageDifference(shot: Image, ours: Image): number {
  let sum = 0;
  for (let y = 0; y < SHOWN_H; y++)
    for (let x = 0; x < SHOWN_W; x++)
      for (let c = 0; c < 3; c++) sum += Math.abs(shot.rgb[((PAGE_Y + y) * shot.width + PAGE_X + x) * 3 + c]! - ours.rgb[(y * ours.width + x) * 3 + c]!);
  return sum / (SHOWN_W * SHOWN_H * 3);
}
/**
 * The game's 5 bit colour keeps a drawn page a few levels off ours: 3.9 to
 * 6.1 for each of the ten files on 2026-10-14. Another page on the same
 * paper was 13.9 or more (the quarry's day and night rosters), so the line
 * is halfway.
 */
const SAME_PAGE = 9;

/** The file's pickup zone, from the item_aot_set its room script carries. */
function pickupZone(doc: Doc): { x: number; z: number; w: number; d: number } {
  const script = readFileSync(path.join(dayDir, doc.room, 'room.c'), 'utf8');
  const m = new RegExp(`item_aot_set\\(\\d+, (\\d+), (\\d+), (\\d+), (\\d+), ${0x5f + doc.slot}\\b`).exec(script);
  if (!m) fail(`${doc.room}/room.c has no pickup for ${doc.id} (run day/scripts.ts)`);
  const [x, z, w, d] = m.slice(1).map(Number) as [number, number, number, number];
  return { x, z, w, d };
}

/** A spot `step` units from the zone's middle toward the middle of the room's floor (renders/room.json). */
function nearSpot(doc: Doc, zone: { x: number; z: number; w: number; d: number }, step: number): { x: number; z: number } | undefined {
  let json: { bounds: { x0: number; z0: number; x1: number; z1: number } };
  try {
    json = JSON.parse(readFileSync(path.join(dayDir, doc.room, 'renders', 'room.json'), 'utf8'));
  } catch {
    return undefined;
  }
  const b = json.bounds;
  const cx = zone.x + zone.w / 2;
  const cz = zone.z + zone.d / 2;
  const mx = (b.x0 + b.x1) / 2 - cx;
  const mz = (b.z0 + b.z1) / 2 - cz;
  const len = Math.hypot(mx, mz) || 1;
  const clamp = (v: number, lo: number, hi: number) => Math.round(Math.min(hi - 300, Math.max(lo + 300, v)));
  return { x: clamp(cx + (mx / len) * step, b.x0, b.x1), z: clamp(cz + (mz / len) * step, b.z0, b.z1) };
}

interface Result {
  doc: Doc;
  shots: { name: string; caption: string }[];
  problems: string[];
}

async function shoot(link: GameLink, r: Result, name: string, caption: string): Promise<string> {
  const file = await snapshot(link, outDir, `${r.doc.id}-${name}`);
  r.shots.push({ name: path.basename(file), caption });
  return file;
}

/** Turn through the reader from its first page, checking each against ours, then close it. */
async function read(link: GameLink, r: Result, prefix: string): Promise<void> {
  for (let i = 0; i < r.doc.pages.length; i++) {
    if (i > 0) await link.tap(Key.right, 3);
    await link.frames(40);
    const shot = await shoot(link, r, `${prefix}${i + 1}`, `${prefix === 'p' ? 'Picked up' : 'From the FILE tab'}: page ${i + 1} of ${r.doc.pages.length}`);
    const diff = pageDifference(readPng(shot), toImage(drawPage(r.doc, i), 2));
    if (diff > SAME_PAGE) r.problems.push(`${prefix === 'p' ? 'pickup' : 'FILE tab'} page ${i + 1} is not ours (difference ${diff.toFixed(1)})`);
  }
  // Past the last page lights EXIT; confirm closes the reader.
  await link.tap(Key.right, 3);
  await link.frames(20);
  await link.tap(Key.action, 3);
  await link.frames(40);
}

const results: Result[] = docs.map((doc) => ({ doc, shots: [], problems: [] }));
const bySlug = new Map(dayRooms.map((r) => [r.slug, r]));
const first = bySlug.get(docs[0]!.room)!;
const session = await open(Number(process.env.PORT ?? 7811), `--mode REB --boot rebecca:${first.stage}:${first.room}`);
const link = session.link;
try {
  await link.waitFor((s) => s.play, 'gameplay', 120_000);
  for (const r of results) {
    const room = bySlug.get(r.doc.room)!;
    try {
      let s = await link.state();
      if (s.stage !== room.stage || s.room !== room.room) await link.room(room.stage, room.room);
      await settle(link);
      // Stand her a step from the pickup first, so the walk to it is short
      // and never crosses one of the room's touch doors.
      // Furniture can stop her on the way; then try again from nearer.
      const zone = pickupZone(r.doc);
      for (const step of [900, 450]) {
        const near = nearSpot(r.doc, zone, step);
        if (near) await link.place(near.x, near.z);
        await link.frames(4);
        try {
          await approach(link, zone);
          break;
        } catch (err) {
          if (step === 450) throw err;
        }
      }
      await shoot(link, r, 'room', `In ${r.doc.room}, at the ${r.doc.title.toLowerCase()}`);
      await link.tap(Key.action, 3);
      s = await link.waitFor((st) => (st.msf & PICKUP_SCREEN) !== 0, 'the file reader', 10_000);
      await read(link, r, 'p');
      await link.frames(60); // the message types itself out
      await shoot(link, r, 'filed', 'Filed');
      s = await settle(link);
      if (!flagOn(s, FILE_FLAGS, FILE_FLAG_BASE + r.doc.slot)) r.problems.push('not marked collected');
      const again = await link.frames(4);
      if ((again.msf & PICKUP_SCREEN) !== 0) r.problems.push('the reader opened again');
    } catch (err) {
      r.problems.push((err as Error).message);
      await link.release().catch(() => undefined);
    }
    console.log(`${r.problems.length ? 'FAIL' : 'ok  '}  ${r.doc.id}${r.problems.length ? `: ${r.problems.join('; ')}` : ''}`);
  }

  // The FILE tab: menu, up twice to MAP, right to FILE, confirm. Her books
  // list the files in BOOKS order; down steps to the next found file, right
  // turns to the second book.
  await settle(link);
  await link.tap(Key.menu, 3);
  await link.frames(60);
  for (const k of [Key.up, Key.up, Key.right, Key.action]) {
    await link.tap(k, 3);
    await link.frames(45);
  }
  const found = BOOKS.filter((id) => wanted.includes(id));
  // The tab opens on book 1: turn to a file's book before stepping to it,
  // even the first, which is in book 2 when only book 2's files are wanted.
  let book = 0;
  for (let i = 0; i < found.length; i++) {
    const r = results.find((x) => x.doc.id === found[i])!;
    const its = BOOKS.indexOf(found[i]!) >> 3;
    if (its !== book) {
      await link.tap(Key.right, 3);
      await link.frames(60);
      book = its;
    } else if (i > 0) {
      await link.tap(Key.down, 3);
      await link.frames(30);
    }
    await shoot(link, r, 'book', `In the FILE tab: ${fileName(r.doc.title)}, book ${(BOOKS.indexOf(found[i]!) >> 3) + 1}`);
  }
  // Read the last one again from the book.
  const last = results.find((x) => x.doc.id === found.at(-1))!;
  await link.tap(Key.action, 3);
  await link.frames(40);
  await read(link, last, 'f');
} finally {
  session.end();
}

const esc = (s: string) => s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
writeFileSync(
  path.join(outDir, 'index.html'),
  `<!doctype html><html lang="en"><head><meta charset="utf-8"><title>Rebecca's files in the game</title>
<script src="/research/rebecca-day/nav.js" defer></script>
<style>body{background:#121110;color:#ddd6c8;font:15px/1.45 system-ui,sans-serif;max-width:1400px;margin:1.5em auto;padding:0 1em}
h2{margin:1.6em 0 .3em}.bad{color:#d0604c}.ok{color:#7d9a5a}.strip{display:flex;gap:.8em;overflow-x:auto}
figure{margin:0;flex:0 0 320px}img{width:320px;image-rendering:pixelated;border:1px solid #2a2724}figcaption{color:#8b8478;font-size:.85em}a{color:#ddd6c8}</style></head><body>
<h1>Rebecca's files in the game</h1>
<p>Each file picked up where its room gives it, read page by page, then found in her FILE tab. Each page the game drew was compared with the page the tools drew. Made ${new Date().toISOString().slice(0, 16).replace('T', ' ')} UTC by tools/harness/tests/files.ts. The pages and their words are on <a href="../">the review page</a>.</p>
${results
  .map(
    (r) => `<h2>${esc(r.doc.title)} <span class="${r.problems.length ? 'bad' : 'ok'}">${r.problems.length ? esc(r.problems.join('; ')) : 'works'}</span></h2>
<div class="strip">${r.shots.map((s) => `<figure><a href="${s.name}"><img src="${s.name}" alt="${esc(s.caption)}"></a><figcaption>${esc(s.caption)}</figcaption></figure>`).join('')}</div>`,
  )
  .join('\n')}
</body></html>
`,
);
const failed = results.filter((r) => r.problems.length);
console.log(failed.length ? `${failed.length} of ${results.length} files failed` : `all ${results.length} files work`);
process.exit(failed.length ? 1 : 0);
