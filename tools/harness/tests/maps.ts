// Rebecca's map screen in the game: her overview and every area's floor plan,
// before and after she has its map, with her six maps picked up where her
// rooms give them; then Chris's map screen, to show it is still RE1's.
//
//   PORT=7830 RE1_LAB_GAME_DIR='D:\Games\RE1-maps' node tools/harness/tests/maps.ts [<outdir>]
//
// Needs the engine and the overlay deployed, with the day's room scripts
// written by day/scripts.ts. Checks what the screen shows against what the
// map tools drew (tools/rebecca/maps):
//
//   - the browser draws her overview and the name of the area she is in;
//   - each map pickup gives her that map (its g_RoomFlags bit);
//   - on an area's map, a room she has been in is lit, a room she has not
//     been in is dim once the map is hers, and her own room blinks red;
//   - Chris's browser shows RE1's overview, not hers.
//
// Writes <outdir>/index.html (default /tmp/rebecca-maps-game) with every
// screenshot, and exits 1 if any check fails.
import { mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { fetch, open } from '../lab.ts';
import { Key, type GameLink } from '../link.ts';
import { approach, settle, useRoomData } from '../flows.ts';
import { snapshot } from '../snapshot.ts';
import { readBmp, readPng, writePng, type Image } from '../image.ts';
import type { GameState } from '../state.ts';
import { AREAS, MAP_ITEMS, STAGES } from '../../rebecca/plan/maps.ts';
import { day } from '../../rebecca/plan/day.ts';
import { blockOf, drawArea, FILL } from '../../rebecca/maps/draw.ts';
import { BASE_H, BASE_SCREEN, BASE_W, LABEL_H, LABEL_SCREEN, LABEL_W, OV_W, overview } from '../../rebecca/maps/overview.ts';
import { mapIn } from '../../rebecca/maps/pickups.ts';
import { mapRooms } from '../../rebecca/maps/tables.ts';
import { rgbOf } from '../../rebecca/maps/tim.ts';

const here = path.dirname(fileURLToPath(import.meta.url));
const dayDir = path.join(here, '..', '..', 'rebecca', 'day');
const outDir = process.argv[2] ?? '/tmp/rebecca-maps-game';
const port = Number(process.env.PORT ?? 7830);
/** Where snapshot.ts has the game save its shots. */
const SHOT_DIR = process.env.RE1_LAB_SHOT_DIR ?? 'C:\\Users\\joell\\Tools\\wintool';
mkdirSync(outDir, { recursive: true });
useRoomData([process.env.RE1_OVERLAY ?? '/tmp/reb-maps-out-2/REB', process.env.RE1_BASE ?? '/tmp/re1-pc']);

/** Bank 8 is g_RoomFlags: the maps she owns are bits 0x7C + index (src/game/BioCard.h). */
const ROOM_FLAGS = 8;
const MAP_BASE = 0x7c;
/** Bank 3 is the enemies' kill flags: her rooms' enemies have 186-254 (day/foes.ts), set so none is alive. */
const KILLS = 3;
const flagOn = (s: GameState, bank: number, n: number) => ((s.banks[bank]![(n >> 5) * 4 + 3 - ((n & 31) >> 3)]! >> (7 - (n & 7))) & 1) === 1;

const rooms = mapRooms();
const roomOf = (place: string) => rooms.find((r) => r.place === place)!;
const ov = overview();

interface Shot {
  name: string;
  caption: string;
}
interface Section {
  title: string;
  shots: Shot[];
  problems: string[];
  notes: string[];
}
const sections: Section[] = [];
const section = (title: string): Section => {
  const s = { title, shots: [], problems: [], notes: [] };
  sections.push(s);
  return s;
};

async function shoot(link: GameLink, sec: Section, name: string, caption: string): Promise<Image> {
  const file = await snapshot(link, outDir, `maps-${name}`);
  sec.shots.push({ name: path.basename(file), caption });
  return readPng(file);
}

/** `count` frames `gap` frames apart, saved on the game machine as they come and fetched after. */
async function burst(link: GameLink, name: string, count: number, gap: number): Promise<Image[]> {
  const remote = (k: number) => `${SHOT_DIR}\\maps-${name}-${k}.bmp`;
  for (let k = 0; k < count; k++) {
    await link.shot(remote(k));
    await link.frames(gap);
  }
  return Array.from({ length: count }, (_, k) => {
    const bmp = path.join(outDir, `maps-${name}-${k}.bmp`);
    fetch(remote(k), bmp);
    const img = readBmp(bmp);
    writePng(path.join(outDir, `maps-${name}-${k}.png`), img);
    return img;
  });
}

/** The shot is the 320 x 240 screen at twice the size: a screen pixel's colour, the middle of its four. */
const at = (img: Image, x: number, y: number): [number, number, number] => {
  const i = ((y * 2 + 1) * img.width + x * 2 + 1) * 3;
  return [img.rgb[i]!, img.rgb[i + 1]!, img.rgb[i + 2]!];
};

/** Mean difference per channel between a part of the screen and a part of an overview picture. */
function differenceFromOverview(img: Image, sx: number, sy: number, w: number, h: number, pixels: Uint8Array, u: number, v: number, clut: Uint16Array): number {
  let sum = 0;
  let n = 0;
  for (let y = 0; y < h; y++)
    for (let x = 0; x < w; x++) {
      const index = pixels[(v + y) * OV_W + u + x]!;
      if (!index) continue;
      const want = rgbOf(clut[index]!);
      const got = at(img, sx + x, sy + y);
      for (let c = 0; c < 3; c++) sum += Math.abs(want[c]! - got[c]!);
      n++;
    }
  return n ? sum / (n * 3) : Infinity;
}

/**
 * The map display draws an area's picture at (48, 28) of the screen, a pixel
 * to a pixel (g_MapZoomDesc[0] at rest: x 0x80, y 0x4E, about its 80, 50).
 */
const MAP_SCREEN = { x: 48, y: 28 };

/** The middle colour of a room's floor on the map display, channel by channel. */
function roomColour(img: Image, area: string, slot: number): [number, number, number] | undefined {
  const d = drawArea(area);
  const fill = blockOf(slot) + FILL;
  // Floor pixels off the grid's lines; those with floor all round them when
  // the room has any (a narrow trail has none).
  const inner: [number, number, number][] = [];
  const edge: [number, number, number][] = [];
  for (let y = 1; y < 99; y++)
    for (let x = 1; x < 127; x++) {
      if (d.pixels[y * 128 + x] !== fill || (x + MAP_SCREEN.x) % 8 === 7 || (y + MAP_SCREEN.y) % 8 === 7) continue;
      const all = [1, -1, 128, -128].every((o) => d.pixels[y * 128 + x + o] === fill);
      (all ? inner : edge).push(at(img, MAP_SCREEN.x + x, MAP_SCREEN.y + y));
    }
  const samples = inner.length ? inner : edge;
  if (!samples.length) return undefined;
  const median = (c: number) => samples.map((s) => s[c]!).sort((a, b) => a - b)[samples.length >> 1]!;
  return [median(0), median(1), median(2)];
}

const colour = (c: [number, number, number] | undefined) => (c ? `rgb(${c.join(', ')})` : 'none');

/** Red pixels in a part of the shot (shot pixels): the status screen draws the tab its cursor is on in red. */
function redIn(img: Image, x0: number, y0: number, x1: number, y1: number): number {
  let n = 0;
  for (let y = y0; y < y1; y++)
    for (let x = x0; x < x1; x++) {
      const i = (y * img.width + x) * 3;
      if (img.rgb[i]! > 150 && img.rgb[i + 1]! < 90 && img.rgb[i + 2]! < 90) n++;
    }
  return n;
}

/**
 * Open the status screen's MAP tab: the browser. The cursor opens where it
 * was left, so step it until the MAP tab is the red one.
 */
async function openBrowser(link: GameLink): Promise<void> {
  await settle(link);
  await link.tap(Key.menu, 3);
  await link.frames(60);
  for (let tries = 0; ; tries++) {
    if (tries > 10) throw new Error('the cursor never reached the MAP tab');
    const img = readPng(await snapshot(link, outDir, 'maps-cursor'));
    if (redIn(img, 420, 34, 508, 62) > 40) break;
    await link.tap(redIn(img, 514, 34, 606, 62) > 40 ? Key.left : Key.up, 3);
    await link.frames(20);
  }
  await link.tap(Key.action, 3);
  await link.frames(45);
}

/** Back out of the map and the status screen. */
async function closeMenu(link: GameLink): Promise<void> {
  await link.tap(Key.run, 3);
  await link.frames(30);
  await link.tap(Key.menu, 3);
  await link.frames(30);
  await settle(link);
}

/** Go to a place's room, with its first thought read. */
async function visit(link: GameLink, place: string): Promise<GameState> {
  const r = roomOf(place);
  const s = await link.state();
  if (s.stage !== r.stage || s.room !== r.room) await link.room(r.stage, r.room);
  return settle(link);
}

/** The browser in an area: it must show her overview, the stage it is in, and the area's name. */
async function checkBrowser(link: GameLink, sec: Section, area: number, name: string, upTo: number): Promise<void> {
  await openBrowser(link);
  const img = await shoot(link, sec, `${name}-browser`, `The browser in ${AREAS[area]!.name}`);
  const t = ov.stages[upTo]!;
  // The mountain where no stage's cut-out lies over it (those are dimmed or not).
  let worst = 0;
  for (let y = 0; y < BASE_H; y += 8) {
    for (let x = 0; x < BASE_W; x += 8) {
      if (ov.markers.some((m) => x + 8 > m.at.x && x < m.at.x + m.at.w && y + 8 > m.at.y && y < m.at.y + m.at.h)) continue;
      worst = Math.max(worst, differenceFromOverview(img, BASE_SCREEN.x + x, BASE_SCREEN.y + y, 8, 8, t.pixels, x, y, t.clut));
    }
  }
  sec.notes.push(`browser: the mountain is ${worst.toFixed(1)} from stage ${upTo + 1}'s picture at worst`);
  if (worst > 12) sec.problems.push(`the browser's mountain is not her overview's stage ${upTo + 1} (${worst.toFixed(1)} off)`);
  const l = ov.labels[area]!;
  const label = differenceFromOverview(img, LABEL_SCREEN.x, LABEL_SCREEN.y, LABEL_W, LABEL_H, t.pixels, l.u, l.v, t.clut);
  sec.notes.push(`browser: the name is ${label.toFixed(1)} from "${AREAS[area]!.name}"`);
  if (label > 20) sec.problems.push(`the browser does not name ${AREAS[area]!.name} (${label.toFixed(1)} off)`);
}

/**
 * The map display in an area: its rooms she has been in lit, one she has not
 * dim (or not there, without the map), and her own room blinking red.
 */
async function checkDisplay(link: GameLink, sec: Section, area: string, name: string, visited: ReadonlySet<string>, owned: boolean, here: string): Promise<void> {
  await link.tap(Key.action, 3);
  await link.frames(40);
  // The blink runs 80 frames a cycle. Fetching a shot takes seconds of game
  // time, so take a burst first, ten frames apart, and fetch them after.
  const looks = await burst(link, `${name}-map`, 8, 10);
  const a = looks[0]!;
  sec.shots.push({ name: `maps-${name}-map-0.png`, caption: `${AREAS.find((x) => x.id === area)!.name}${owned ? '' : ', without its map'}` });
  sec.shots.push({ name: `maps-${name}-map-4.png`, caption: '40 frames later' });
  const places = AREAS.find((x) => x.id === area)!.places;
  const slot = (p: string) => places.indexOf(p);
  const hereColours = looks.map((img) => roomColour(img, area, slot(here)));
  const reds = hereColours.flatMap((x) => (x ? [x[0]] : []));
  sec.notes.push(`map: her room (${here}) is ${colour(hereColours[0])}; its red runs ${Math.min(...reds)} to ${Math.max(...reds)} over 80 frames`);
  if (!hereColours.some((x) => x && x[0] > 50 && x[0] > x[1] + 35)) sec.problems.push(`her room, ${here}, is not red`);
  if (reds.length < looks.length || Math.max(...reds) - Math.min(...reds) < 20) sec.problems.push(`her room, ${here}, does not blink`);
  const lit = places.find((p) => p !== here && visited.has(p));
  const litColour = lit ? roomColour(a, area, slot(lit)) : undefined;
  if (lit) {
    sec.notes.push(`map: ${lit}, visited, is ${colour(litColour)}`);
    if (!litColour || litColour[1] < 50 || litColour[1] < litColour[0] + 20) sec.problems.push(`${lit}, where she has been, is not lit`);
  }
  const unseen = places.find((p) => !visited.has(p));
  if (unseen) {
    const c = roomColour(a, area, slot(unseen));
    sec.notes.push(`map: ${unseen}, not visited, is ${colour(c)}`);
    if (owned && litColour && c && c[1] > litColour[1] - 10) sec.problems.push(`${unseen}, where she has not been, is not dim`);
    // The grid alone is about (23, 20, 56): a dim room is greener.
    if (owned && c && c[1] < 28) sec.problems.push(`${unseen} is not on the map she owns`);
    if (!owned && c && litColour && c[1] > litColour[1] - 10) sec.problems.push(`${unseen} shows without the map`);
  }
}

const visited = new Set<string>();
const first = roomOf('cabin');
let session = await open(port, `--mode REB --boot rebecca:${first.stage}:${first.room}`);
let link = session.link;
try {
  await link.waitFor((s) => s.play, 'gameplay', 120_000);
  for (let f = 186; f <= 254; f++) await link.setFlag(KILLS, f, true);
  await settle(link);
  visited.add('cabin');

  // Before any map: each area with two of its rooms seen. The overview opens
  // a stage more as she reaches each.
  for (const [i, a] of AREAS.entries()) {
    const sec = section(`${a.name}, before its map`);
    const unseen = a.places.filter((p) => !visited.has(p)).slice(0, 2);
    const go = unseen.length ? unseen : a.places.slice(0, 1);
    try {
      for (const p of go) {
        await visit(link, p);
        visited.add(p);
      }
      // The overview's stage: the furthest one she has been in.
      const reached = Math.max(...[...visited].map((p) => STAGES.findIndex((st) => st.areas.includes(AREAS[roomOf(p).area]!.id))));
      await checkBrowser(link, sec, i, `${a.id}-0`, reached);
      await checkDisplay(link, sec, a.id, `${a.id}-0`, visited, false, go.at(-1)!);
    } catch (err) {
      sec.problems.push((err as Error).message);
      await link.release().catch(() => undefined);
    }
    await closeMenu(link).catch(() => undefined);
    console.log(`${sec.problems.length ? 'FAIL' : 'ok  '}  ${sec.title}${sec.problems.length ? `: ${sec.problems.join('; ')}` : ''}`);
  }

  // Her maps, picked up where her rooms give them.
  for (const [i, m] of MAP_ITEMS.entries()) {
    const sec = section(`Picking up the ${m.name}`);
    const step = day.steps.find((s) => s.id === m.step)!;
    const slug = day.places.find((p) => p.id === step.at)?.room ?? step.at;
    const item = mapIn(slug)!;
    try {
      await visit(link, step.at);
      visited.add(step.at);
      const script = readFileSync(path.join(dayDir, slug, 'room.c'), 'utf8');
      const z = new RegExp(`item_aot_set\\(\\d+, (\\d+), (\\d+), (\\d+), (\\d+), ${item.id}\\b`).exec(script);
      if (!z) throw new Error(`${slug}/room.c has no pickup for item ${item.id}`);
      const [x, zz, w, d] = z.slice(1).map(Number) as [number, number, number, number];
      await approach(link, { x, z: zz, w, d });
      await shoot(link, sec, `pickup-${m.id}-room`, `At the ${m.name.toLowerCase()} in ${step.at}`);
      // Her line on taking it, which the room's main script says.
      const line = new RegExp(`ck\\(FG_ITEM, ${item.flag}, 1\\)\\) \\{\\s*set\\(FG_ROOM, \\d+, 1\\);\\s*message\\((\\d+)`).exec(script);
      if (!line) throw new Error(`${slug}/room.c says nothing on taking the ${m.name}`);
      const said = Number(line[1]);
      await link.tap(Key.action, 3);
      const shown = await link.waitFor((st) => st.messageId === said || st.messageId === said - 128, `her line on the ${m.name}`, 10_000).catch(() => undefined);
      await link.frames(30);
      await shoot(link, sec, `pickup-${m.id}-taken`, 'Picked up');
      if (!shown) sec.problems.push(`she says nothing on taking the ${m.name} (message ${said})`);
      const s = await settle(link);
      if (!flagOn(s, ROOM_FLAGS, MAP_BASE + i)) sec.problems.push(`the ${m.name} is not hers after picking it up (g_RoomFlags ${MAP_BASE + i})`);
    } catch (err) {
      sec.problems.push((err as Error).message);
      await link.release().catch(() => undefined);
    }
    console.log(`${sec.problems.length ? 'FAIL' : 'ok  '}  ${sec.title}${sec.problems.length ? `: ${sec.problems.join('; ')}` : ''}`);
  }

  // With her maps: each area's map again, from a room she has been in.
  for (const [i, a] of AREAS.entries()) {
    const sec = section(`${a.name}, with its map`);
    const owned = MAP_ITEMS.some((m) => m.areas.includes(a.id));
    try {
      const here = [...a.places].reverse().find((p) => visited.has(p))!;
      await visit(link, here);
      await checkBrowser(link, sec, i, `${a.id}-1`, STAGES.length - 1);
      await checkDisplay(link, sec, a.id, `${a.id}-1`, visited, owned, here);
    } catch (err) {
      sec.problems.push((err as Error).message);
      await link.release().catch(() => undefined);
    }
    await closeMenu(link).catch(() => undefined);
    console.log(`${sec.problems.length ? 'FAIL' : 'ok  '}  ${sec.title}${sec.problems.length ? `: ${sec.problems.join('; ')}` : ''}`);
  }
} finally {
  session.end();
}

// Chris's game: RE1's map screen, his first floor's map his and a few rooms seen.
{
  const sec = section("Chris's map screen, still RE1's");
  session = await open(port, '--boot chris:0:9');
  link = session.link;
  try {
    await link.waitFor((s) => s.play, 'gameplay', 120_000);
    await settle(link);
    await link.setFlag(ROOM_FLAGS, MAP_BASE, true);
    for (let r = 0; r < 20; r++) await link.setFlag(ROOM_FLAGS, r, true);
    await openBrowser(link);
    const img = await shoot(link, sec, 'chris-browser', "Chris's browser");
    const t = ov.stages[0]!;
    const off = differenceFromOverview(img, BASE_SCREEN.x, BASE_SCREEN.y, BASE_W, BASE_H, t.pixels, 0, 0, t.clut);
    sec.notes.push(`browser: ${off.toFixed(1)} from her overview`);
    if (off < 25) sec.problems.push(`Chris's browser looks like hers (${off.toFixed(1)} off)`);
    await link.tap(Key.action, 3);
    await link.frames(40);
    await shoot(link, sec, 'chris-map', 'His 1F map');
  } catch (err) {
    sec.problems.push((err as Error).message);
  } finally {
    session.end();
  }
  console.log(`${sec.problems.length ? 'FAIL' : 'ok  '}  ${sec.title}${sec.problems.length ? `: ${sec.problems.join('; ')}` : ''}`);
}

const esc = (s: string) => s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
writeFileSync(
  path.join(outDir, 'index.html'),
  `<!doctype html><html lang="en"><head><meta charset="utf-8"><title>Rebecca's maps in the game</title>
<script src="/research/rebecca-day/nav.js" defer></script>
<style>body{background:#121110;color:#ddd6c8;font:15px/1.45 system-ui,sans-serif;max-width:1400px;margin:1.5em auto;padding:0 1em}
h2{margin:1.6em 0 .3em}.bad{color:#d0604c}.ok{color:#7d9a5a}.strip{display:flex;gap:.8em;overflow-x:auto}.notes{color:#8b8478;font-size:.85em}
figure{margin:0;flex:0 0 320px}img{width:320px;image-rendering:pixelated;border:1px solid #2a2724}figcaption{color:#8b8478;font-size:.85em}a{color:#ddd6c8}</style></head><body>
<h1>Rebecca's maps in the game</h1>
<p>Her map screen, area by area, before and after she picks up its map, and Chris's, which must still be RE1's. Made ${new Date().toISOString().slice(0, 16).replace('T', ' ')} UTC by tools/harness/tests/maps.ts.</p>
${sections
  .map(
    (s) => `<h2>${esc(s.title)} <span class="${s.problems.length ? 'bad' : 'ok'}">${s.problems.length ? esc(s.problems.join('; ')) : 'works'}</span></h2>
<p class="notes">${s.notes.map(esc).join('<br>')}</p>
<div class="strip">${s.shots.map((x) => `<figure><a href="${x.name}"><img src="${x.name}" alt="${esc(x.caption)}"></a><figcaption>${esc(x.caption)}</figcaption></figure>`).join('')}</div>`,
  )
  .join('\n')}
</body></html>
`,
);
const failed = sections.filter((s) => s.problems.length);
console.log(failed.length ? `${failed.length} of ${sections.length} parts failed` : `all ${sections.length} parts work`);
process.exit(failed.length ? 1 : 0);
