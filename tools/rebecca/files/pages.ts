// Draw Rebecca's file pages and pack them the way the game reads them.
//
// A page is what RE1 shows in its file reader: a 256x256 4 bpp TIM with one
// 16 colour CLUT, as in item_m2/filem_*.pix. A .pix is 16 little-endian
// offsets (0x40 bytes), one per page plus one to the end of the file, then
// each page LZW packed for unpack_pakfile_ (0x00425ab0). The reader picks a
// page by its offset (pickup_unpack_list, 0x004827c0) and takes the page
// count from g_itemMaxCounts (0x004d2620), not from the file.
//
// Everything here draws from documents.ts with our own font (font.ts) and
// our own art. Nothing is copied from the game's pages.
import { lzwPack, to555 } from '../pak.ts';
import type { Image } from '../harness/image.ts';
import { ADVANCE, GLYPH_H, glyph } from './font.ts';
import type { Calendar, Doc, MineMap, Notice, Page, Paper, Roster } from './documents.ts';

export const PAGE = 256;
const LINE = 16;

// ---------------------------------------------------------------------------
// Colours. Every page has the same 16 slots; a paper fills them its own way.

const C = {
  Clear: 0,
  Paper: 1,
  PaperDark: 2,
  PaperLight: 3,
  Edge: 4,
  Rule: 5,
  Margin: 6,
  Ink: 7,
  InkSoft: 8,
  Red: 9,
  RedSoft: 10,
  Blood: 11,
  BloodDark: 12,
  Line: 13,
  Fill: 14,
  Caption: 15,
} as const;

type Rgb = readonly [number, number, number];
const BLACK: Rgb = [0, 0, 0];
interface Swatch {
  readonly rgb: Rgb;
  /** The PS1 semi-transparency bit. RE1's own ink carries it; its pictures do not. */
  readonly stp: boolean;
}

const op = (r: number, g: number, b: number): Swatch => ({ rgb: [r, g, b], stp: false });
const ink = (r: number, g: number, b: number): Swatch => ({ rgb: [r, g, b], stp: true });

/** Shared by every paper: the reds, the art's pencil, the light caption ink. */
const COMMON: Partial<Record<number, Swatch>> = {
  [C.Red]: op(168, 34, 26),
  [C.RedSoft]: op(150, 92, 76),
  [C.Blood]: op(112, 20, 16),
  [C.BloodDark]: op(70, 12, 10),
  [C.Line]: op(74, 70, 64),
  [C.Fill]: op(120, 132, 140),
  [C.Caption]: ink(206, 206, 200),
};

const PAPERS: Record<Paper, Partial<Record<number, Swatch>>> = {
  // RE1's own look: light grey type on the reader's black.
  black: { [C.Ink]: ink(214, 214, 206), [C.InkSoft]: ink(120, 120, 116) },
  // A ruled notebook, written in blue-black ballpoint.
  notebook: {
    [C.Paper]: op(206, 198, 176),
    [C.PaperDark]: op(186, 176, 152),
    [C.PaperLight]: op(218, 212, 194),
    [C.Edge]: op(150, 138, 112),
    [C.Rule]: op(150, 164, 184),
    [C.Margin]: op(190, 120, 112),
    [C.Ink]: op(34, 40, 78),
    [C.InkSoft]: op(120, 122, 140),
  },
  // A bound log: grey-green ledger paper, a column for the time.
  ledger: {
    [C.Paper]: op(190, 194, 172),
    [C.PaperDark]: op(170, 174, 152),
    [C.PaperLight]: op(204, 206, 188),
    [C.Edge]: op(132, 136, 112),
    [C.Rule]: op(132, 156, 134),
    [C.Margin]: op(112, 134, 112),
    [C.Ink]: op(38, 34, 30),
    [C.InkSoft]: op(120, 120, 106),
  },
  // Typed on good white paper.
  letter: {
    [C.Paper]: op(214, 212, 202),
    [C.PaperDark]: op(196, 194, 182),
    [C.PaperLight]: op(226, 224, 216),
    [C.Edge]: op(160, 156, 140),
    [C.Rule]: op(196, 194, 182),
    [C.Margin]: op(196, 194, 182),
    [C.Ink]: op(28, 26, 26),
    [C.InkSoft]: op(126, 124, 120),
  },
};

function palette(paper: Paper): Swatch[] {
  const fill = { ...PAPERS.letter, ...PAPERS[paper], ...COMMON };
  return Array.from({ length: 16 }, (_, i) => {
    if (i === C.Clear) return { rgb: [0, 0, 0], stp: false };
    const s = fill[i];
    if (!s) throw new Error(`the ${paper} paper has no colour ${i}`);
    return s;
  });
}

// ---------------------------------------------------------------------------
// A page being drawn.

export interface Drawn {
  readonly pixels: Uint8Array; // PAGE * PAGE palette indices
  readonly palette: readonly Swatch[];
}

class Canvas {
  readonly px = new Uint8Array(PAGE * PAGE);
  readonly rand: () => number;
  constructor(rand: () => number) {
    this.rand = rand;
  }
  get(x: number, y: number): number {
    return x < 0 || y < 0 || x >= PAGE || y >= PAGE ? C.Clear : this.px[y * PAGE + x];
  }
  set(x: number, y: number, c: number): void {
    if (x >= 0 && y >= 0 && x < PAGE && y < PAGE) this.px[y * PAGE + x] = c;
  }
  rect(x0: number, y0: number, x1: number, y1: number, c: number): void {
    for (let y = y0; y < y1; y++) for (let x = x0; x < x1; x++) this.set(x, y, c);
  }
  line(x0: number, y0: number, x1: number, y1: number, c: number, width = 1): void {
    const n = Math.max(Math.abs(x1 - x0), Math.abs(y1 - y0), 1);
    for (let i = 0; i <= n; i++) {
      const x = Math.round(x0 + ((x1 - x0) * i) / n);
      const y = Math.round(y0 + ((y1 - y0) * i) / n);
      const h = width >> 1;
      this.rect(x - h, y - h, x - h + width, y - h + width, c);
    }
  }
  /** A hand-drawn loop: an ellipse whose radius wanders, drawn twice over itself. */
  loop(cx: number, cy: number, rx: number, ry: number, c: number): void {
    for (let pass = 0; pass < 2; pass++) {
      const wob = this.rand() * 6;
      for (let a = 0; a < Math.PI * 2.15; a += 0.02) {
        const k = 1 + 0.08 * Math.sin(a * 3 + wob) + pass * 0.05;
        this.set(Math.round(cx + Math.cos(a) * rx * k), Math.round(cy + Math.sin(a) * ry * k), c);
      }
    }
  }
}

function mulberry(seed: number): () => number {
  let a = seed >>> 0;
  return () => {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

const hash = (s: string) => [...s].reduce((h, ch) => Math.imul(h ^ ch.charCodeAt(0), 16777619) >>> 0, 2166136261);

// ---------------------------------------------------------------------------
// Text.

interface Pen {
  readonly c: number;
  /** 2 draws every pixel as a 2x2 block. */
  readonly scale?: number;
  /** How unsteady the hand is: 0 is steady, 2 is barely holding the pen. */
  readonly shaky?: number;
  /** Extra pixels between letters, as RE1 spaces out its file titles. */
  readonly spacing?: number;
}

/** Draw one line of text with its capitals' top at y. Returns the x after it. */
function write(cv: Canvas, s: string, x: number, y: number, pen: Pen): number {
  const scale = pen.scale ?? 1;
  const shaky = pen.shaky ?? 0;
  // An unsteady hand drifts off the line and back, with now and then a jolt.
  const phase = cv.rand() * 6;
  for (const ch of s) {
    const g = glyph(ch);
    const jolt = shaky > 1 && cv.rand() < 0.15 ? (cv.rand() < 0.5 ? -1 : 1) : 0;
    const dy = shaky ? Math.round(Math.sin(x / 31 + phase) * (shaky - 0.3)) + jolt : 0;
    const dx = shaky > 1 && cv.rand() < 0.2 ? 1 : 0;
    for (let gy = 0; gy < GLYPH_H; gy++)
      for (let gx = 0; gx < g[gy].length; gx++)
        if (g[gy][gx]) cv.rect(x + dx + gx * scale, y + dy + gy * scale, x + dx + (gx + 1) * scale, y + dy + (gy + 1) * scale, pen.c);
    x += ADVANCE * scale + (pen.spacing ?? 0);
  }
  return x;
}

const width = (s: string, scale = 1, spacing = 0) => [...s].length * (ADVANCE * scale + spacing) - spacing;

/** Soften ink: a paper pixel touched by ink on two sides takes the soft ink, as a pen's line bleeds. */
function bleed(cv: Canvas, inkC: number, softC: number, x0 = 0, y0 = 0, x1 = PAGE, y1 = PAGE): void {
  const soft: number[] = [];
  for (let y = y0; y < y1; y++)
    for (let x = x0; x < x1; x++) {
      const here = cv.get(x, y);
      if (here === inkC || here === softC) continue;
      const n = +(cv.get(x - 1, y) === inkC) + +(cv.get(x + 1, y) === inkC) + +(cv.get(x, y - 1) === inkC) + +(cv.get(x, y + 1) === inkC);
      if (n >= 2) soft.push(y * PAGE + x);
    }
  for (const i of soft) cv.px[i] = softC;
}

/** Break a paragraph into lines no wider than `cols` characters. */
export function wrap(paragraph: string, cols: number): string[] {
  const out: string[] = [];
  let cur = '';
  for (const word of paragraph.split(/ +/)) {
    if (!word) continue;
    if ([...word].length > cols) throw new Error(`a word is wider than the page: ${word}`);
    const next = cur ? `${cur} ${word}` : word;
    if ([...next].length > cols) {
      out.push(cur);
      cur = word;
    } else cur = next;
  }
  out.push(cur);
  return out;
}

// ---------------------------------------------------------------------------
// Paper.

const SHEET = { x0: 8, y0: 6, x1: 248, y1: 250 };

function sheet(cv: Canvas, box = SHEET): void {
  const { x0, y0, x1, y1 } = box;
  cv.rect(x0, y0, x1, y1, C.Paper);
  for (let y = y0; y < y1; y++)
    for (let x = x0; x < x1; x++) {
      const r = cv.rand();
      const edge = Math.min(x - x0, x1 - 1 - x, y - y0, y1 - 1 - y);
      if (edge === 0 || (edge === 1 && r < 0.5)) cv.set(x, y, C.Edge);
      else if (r < 0.05 || (edge < 6 && r < 0.2)) cv.set(x, y, C.PaperDark);
      else if (r > 0.96) cv.set(x, y, C.PaperLight);
    }
  // A dog-eared top right corner.
  for (let i = 0; i < 12; i++)
    for (let j = 0; j < 12 - i; j++) {
      cv.set(x1 - 1 - j, y0 + i, C.Clear);
      if (j === 12 - i - 1) cv.set(x1 - 1 - j, y0 + i, C.Edge);
    }
}

interface Layout {
  /** Where text starts and stops on a line. */
  readonly left: number;
  readonly right: number;
  /** The top of the first line's capitals. */
  readonly top: number;
  readonly rows: number;
  /** The ledger's time column, left of `left`. */
  readonly time?: number;
}

const LAYOUTS: Record<Paper, Layout> = {
  black: { left: 16, right: 240, top: 14, rows: 14 },
  notebook: { left: 40, right: 240, top: 22, rows: 14 },
  ledger: { left: 58, right: 240, top: 22, rows: 14, time: 18 },
  letter: { left: 22, right: 236, top: 22, rows: 14 },
};

function ruling(cv: Canvas, paper: Paper, top: number): void {
  const lay = LAYOUTS[paper];
  if (paper === 'notebook' || paper === 'ledger') {
    for (let y = top + 11; y < SHEET.y1 - 4; y += LINE)
      for (let x = SHEET.x0 + 2; x < SHEET.x1 - 2; x++) if (cv.get(x, y) !== C.Clear) cv.set(x, y, C.Rule);
    const mx = paper === 'notebook' ? lay.left - 6 : lay.left - 5;
    for (let y = SHEET.y0 + 2; y < SHEET.y1 - 2; y++) if (cv.get(mx, y) !== C.Clear) cv.set(mx, y, C.Margin);
    if (paper === 'ledger') for (let y = SHEET.y0 + 2; y < SHEET.y1 - 2; y++) if (cv.get(lay.time! - 4, y) !== C.Clear) cv.set(lay.time! - 4, y, C.Margin);
  }
}

// ---------------------------------------------------------------------------
// Pages.

/** Draw a document's title page: its name, spaced out, in the middle of the reader's black. */
function titlePage(cv: Canvas, doc: Doc): void {
  const lines = doc.title.toUpperCase().split('\n');
  const y0 = PAGE / 2 - (lines.length * LINE) / 2 - 4;
  lines.forEach((s, i) => {
    write(cv, s, Math.round((PAGE - width(s, 1, 3)) / 2), y0 + i * LINE, { c: C.Caption, spacing: 3 });
  });
  if (doc.subtitle) {
    const s = doc.subtitle;
    write(cv, s, Math.round((PAGE - width(s)) / 2), y0 + lines.length * LINE + 8, { c: C.Caption });
  }
}

const TIME = /^(\d{4}|\d\d\.\d\d) (.*)$/;

/**
 * Lay a text page out. Paragraphs are split by blank lines and wrapped; a
 * single newline forces a break. A line starting with '>' is set to the
 * right (a signature), '^' is centred (a heading). On ledger paper a line
 * that opens with a time ("0305" or "01.20") puts the time in its column.
 */
export function layoutText(text: string, paper: Paper, rows = LAYOUTS[paper].rows): { row: number; x: 'left' | 'right' | 'centre'; time?: string; s: string }[] {
  const lay = LAYOUTS[paper];
  const cols = Math.floor((lay.right - lay.left) / ADVANCE);
  const out: { row: number; x: 'left' | 'right' | 'centre'; time?: string; s: string }[] = [];
  let row = 0;
  const paragraphs = text.replace(/^\n+|\n+$/g, '').split(/\n\s*\n/);
  paragraphs.forEach((para, pi) => {
    if (pi > 0) row++;
    for (const raw of para.split('\n')) {
      const line = raw.trim();
      if (line.startsWith('>') || line.startsWith('^')) {
        const s = line.slice(1).trim();
        if ([...s].length > cols) throw new Error(`a set line is wider than the page: ${s}`);
        out.push({ row: row++, x: line[0] === '>' ? 'right' : 'centre', s });
        continue;
      }
      const t = lay.time !== undefined ? TIME.exec(line) : null;
      const body = t ? t[2] : line;
      wrap(body, cols).forEach((s, i) => out.push({ row: row++, x: 'left', time: i === 0 && t ? t[1] : undefined, s }));
    }
  });
  if (row > rows) throw new Error(`a page runs to ${row} lines, more than the ${rows} that fit:\n${text}`);
  return out;
}

function textPage(cv: Canvas, page: Extract<Page, { kind: 'text' }>, paper: Paper): void {
  const lay = LAYOUTS[paper];
  let top = lay.top;
  if (paper !== 'black') sheet(cv);
  if (page.letterhead) top = letterhead(cv, paper) + 4;
  ruling(cv, paper, top);
  const pen: Pen = { c: C.Ink, shaky: page.shaky };
  const rows = Math.min(lay.rows, Math.floor((SHEET.y1 - 2 - top) / LINE));
  for (const l of layoutText(page.text, paper, rows)) {
    const y = top + l.row * LINE;
    const x = l.x === 'left' ? lay.left : l.x === 'right' ? lay.right - width(l.s) : Math.round((lay.left + lay.right - width(l.s)) / 2);
    if (l.time) write(cv, l.time, lay.time!, y, pen);
    write(cv, l.s, x, y, pen);
  }
  if (paper !== 'black') bleed(cv, C.Ink, C.InkSoft);
  for (const mark of page.marks ?? []) stain(cv, mark);
}

/** Umbrella's letterhead: the eight-panel umbrella and the company's name. Returns the y under it. */
function letterhead(cv: Canvas, paper: Paper): number {
  const cx = 38;
  const cy = 34;
  const r = 15;
  for (let y = -r; y <= r; y++)
    for (let x = -r; x <= r; x++) {
      const d = Math.max(Math.abs(x), Math.abs(y), (Math.abs(x) + Math.abs(y)) / 1.41);
      if (d > r) continue;
      const seg = Math.floor(((Math.atan2(y, x) + Math.PI) / (Math.PI * 2)) * 8 + 0.5) % 8;
      cv.set(cx + x, cy + y, seg % 2 ? C.Red : paper === 'black' ? C.Caption : C.PaperLight);
    }
  write(cv, 'UMBRELLA CORPORATION', 62, 22, { c: paper === 'black' ? C.Caption : C.Ink });
  write(cv, 'Raccoon City Office', 62, 36, { c: paper === 'black' ? C.Caption : C.InkSoft });
  cv.line(22, 56, 234, 56, C.Red);
  return 58;
}

type Mark = NonNullable<Extract<Page, { kind: 'text' }>['marks']>[number];

/** A smear of blood on a page: a thumbprint or a drip. */
function stain(cv: Canvas, m: Mark): void {
  if (m.kind === 'thumb') {
    for (let y = -9; y <= 9; y++)
      for (let x = -7; x <= 7; x++) {
        const e = (x / 7) ** 2 + (y / 9) ** 2;
        if (e > 1 || cv.rand() < 0.15) continue;
        const ridge = Math.round(Math.sqrt(x * x + y * y * 0.6) + cv.rand() * 0.8) % 3 === 0;
        cv.set(m.x + x, m.y + y, ridge ? C.BloodDark : e > 0.7 ? C.RedSoft : C.Blood);
      }
  } else {
    let x = m.x;
    for (let y = m.y; y < m.y + m.len; y++) {
      cv.rect(x - 1, y, x + 2, y + 1, C.Blood);
      if (cv.rand() < 0.1) x += cv.rand() < 0.5 ? -1 : 1;
    }
    cv.rect(x - 2, m.y + m.len, x + 3, m.y + m.len + 3, C.Blood);
  }
}

/** The bunkhouse calendar: a supply company's July 1998, three days ringed in red. */
function calendarPage(cv: Canvas, cal: Calendar): void {
  sheet(cv, { x0: 14, y0: 6, x1: 242, y1: 250 });
  // The company's pine and name across the top.
  for (let i = 0; i < 9; i++) cv.line(34 - i, 14 + i * 2, 34 + i, 14 + i * 2, C.Line);
  cv.rect(33, 32, 36, 37, C.Line);
  write(cv, cal.company, 50, 14, { c: C.Ink });
  write(cv, cal.town, 50, 27, { c: C.InkSoft });
  write(cv, cal.month, Math.round((PAGE - width(cal.month, 2)) / 2), 46, { c: C.Ink, scale: 2 });
  const gx = 22;
  const gy = 76;
  const cw = 30;
  const ch = 28;
  ['S', 'M', 'T', 'W', 'T', 'F', 'S'].forEach((d, i) => write(cv, d, gx + i * cw + 12, gy - 12, { c: i === 0 ? C.Red : C.Ink }));
  for (let r = 0; r <= 5; r++) cv.line(gx, gy + r * ch, gx + 7 * cw, gy + r * ch, C.Line);
  for (let c = 0; c <= 7; c++) cv.line(gx + c * cw, gy, gx + c * cw, gy + 5 * ch, C.Line);
  for (let day = 1; day <= cal.days; day++) {
    const cell = cal.firstWeekday + day - 1;
    const x = gx + (cell % 7) * cw;
    const y = gy + Math.floor(cell / 7) * ch;
    const s = String(day);
    write(cv, s, x + cw - 3 - width(s), y + 3, { c: cell % 7 === 0 ? C.Red : C.Ink });
    const note = cal.notes[day];
    if (note) write(cv, note, x + 2, y + 15, { c: C.InkSoft, shaky: 1 });
    if (cal.circled.includes(day)) cv.loop(x + cw - 3 - width(s) / 2 - 1, y + 7, 10, 8, C.Red);
  }
  bleed(cv, C.Ink, C.InkSoft, 14, 6, 242, 250);
  write(cv, cal.scrawl, Math.round((PAGE - width(cal.scrawl, 2)) / 2), 222, { c: C.Red, scale: 2, shaky: 1 });
}

/** The shift boss's map of the workings, in pencil, with Hal's bloody thumb on the gallery. */
function mapPage(cv: Canvas, map: MineMap): void {
  sheet(cv);
  write(cv, map.heading, 20, 16, { c: C.Ink });
  write(cv, map.sub, 20, 30, { c: C.InkSoft });
  const tunnel = (pts: [number, number][], w = 7) => {
    for (let i = 1; i < pts.length; i++) cv.line(pts[i - 1][0], pts[i - 1][1], pts[i][0], pts[i][1], C.Line, w);
    for (let i = 1; i < pts.length; i++) cv.line(pts[i - 1][0], pts[i - 1][1], pts[i][0], pts[i][1], C.PaperLight, w - 4);
  };
  // The adit from the quarry cut to the junction.
  tunnel([[18, 92], [150, 92]]);
  // The office off the adit.
  cv.rect(70, 60, 98, 82, C.Line);
  cv.rect(72, 62, 96, 80, C.PaperLight);
  tunnel([[84, 82], [84, 90]], 5);
  // The junction, the pump house east of it, the lift north.
  tunnel([[150, 92], [150, 60]]);
  cv.rect(140, 44, 162, 62, C.Line);
  cv.line(140, 44, 162, 62, C.Line);
  cv.line(162, 44, 140, 62, C.Line);
  tunnel([[150, 92], [196, 92]]);
  cv.rect(196, 82, 222, 104, C.Line);
  cv.rect(198, 84, 220, 102, C.PaperLight);
  for (let a = 0; a < Math.PI * 2; a += 0.05) cv.set(Math.round(209 + Math.cos(a) * 6), Math.round(93 + Math.sin(a) * 6), C.Line);
  // The decline down to the old third level and the gallery, under water.
  tunnel([[150, 92], [150, 120], [128, 150]]);
  cv.rect(40, 146, 214, 176, C.Line);
  cv.rect(42, 148, 212, 174, C.Fill);
  for (let y = 152; y < 172; y += 5) for (let x = 46; x < 208; x += 9) cv.line(x, y, x + 4, y + (x % 2 ? 1 : 0), C.PaperLight);
  // The winze at the gallery's east end, roped off.
  cv.rect(200, 176, 212, 196, C.Line);
  // Labels.
  for (const [s, x, y] of map.labels) write(cv, s, x, y, { c: C.Ink });
  write(cv, 'N', 230, 18, { c: C.Ink });
  cv.line(232, 30, 232, 44, C.Ink);
  cv.line(229, 33, 232, 30, C.Ink);
  cv.line(235, 33, 232, 30, C.Ink);
  bleed(cv, C.Ink, C.InkSoft);
  for (const [s, x, y] of map.notes) write(cv, s, x, y, { c: C.Red, shaky: 1 });
  stain(cv, { kind: 'thumb', x: map.thumb[0], y: map.thumb[1] });
}

/** A printed notice nailed to a tree, the bottom half torn away. */
function noticePage(cv: Canvas, n: Notice): void {
  const box = { x0: 30, y0: 20, x1: 226, y1: 236 };
  sheet(cv, box);
  // Nail holes, rust running from them.
  for (const x of [42, 214]) {
    cv.rect(x - 1, 27, x + 2, 30, C.BloodDark);
    for (let y = 30; y < 60; y++) if (cv.rand() < 0.7) cv.set(x + (cv.rand() < 0.2 ? 1 : 0), y, C.RedSoft);
  }
  write(cv, n.heading, Math.round((PAGE - width(n.heading, 2)) / 2), 40, { c: C.Red, scale: 2 });
  let y = 68;
  for (const l of n.lines) {
    write(cv, l, Math.round((PAGE - width(l)) / 2), y, { c: C.Ink });
    y += LINE;
  }
  // The tear: a ragged line under which the paper is gone, cutting through the last line.
  let tear = n.tearAt;
  for (let x = box.x0; x < box.x1; x++) {
    tear += Math.round((cv.rand() - 0.5) * 4);
    tear = Math.max(n.tearAt - 10, Math.min(n.tearAt + 10, tear));
    cv.set(x, tear, C.Edge);
    if (cv.rand() < 0.5) cv.set(x, tear - 1, C.PaperLight);
    for (let yy = tear + 1; yy < box.y1; yy++) cv.set(x, yy, C.Clear);
  }
  bleed(cv, C.Ink, C.InkSoft, box.x0, box.y0, box.x1, box.y1);
}

/** A week's shift roster on the quarry office board: who came in, who went SICK. */
function rosterPage(cv: Canvas, r: Roster): void {
  sheet(cv);
  write(cv, r.company, 20, 16, { c: C.Ink });
  write(cv, r.heading, 20, 30, { c: C.Ink });
  const days = ['MON', 'TUE', 'WED', 'THU', 'FRI'];
  const nx = 18;
  const dx = 104;
  const cw = 28;
  const top = 52;
  const rh = 18;
  days.forEach((d, i) => write(cv, d, dx + i * cw + 2, top, { c: C.Ink }));
  for (let i = 0; i <= r.rows.length; i++) cv.line(nx, top + 12 + i * rh, dx + 5 * cw, top + 12 + i * rh, C.Line);
  for (let i = 0; i <= 5; i++) cv.line(dx + i * cw, top + 12, dx + i * cw, top + 12 + r.rows.length * rh, C.Line);
  r.rows.forEach((row, i) => {
    const y = top + 16 + i * rh;
    write(cv, row.name, nx, y, { c: C.Ink });
    row.days.forEach((mark, d) => {
      const x = dx + d * cw;
      if (mark === 'in') {
        cv.line(x + 9, y + 5, x + 12, y + 8, C.Ink);
        cv.line(x + 12, y + 8, x + 18, y, C.Ink);
      } else if (mark === 'sick' && row.days[d - 1] !== 'sick') write(cv, 'SICK', x + 1, y, { c: C.Red });
    });
    if (row.struck) cv.line(nx - 2, y + 4 + (i % 2), nx + width(row.name) + 2, y + 3, C.Red);
  });
  bleed(cv, C.Ink, C.InkSoft);
  const fy = top + 22 + r.rows.length * rh;
  if (r.foot) layoutText(r.foot, 'letter').forEach((l) => write(cv, l.s, 20, fy + l.row * LINE, { c: C.Red, shaky: 1 }));
}

/** Draw one page of a document. */
export function drawPage(doc: Doc, index: number, paper: Paper = doc.paper): Drawn {
  const page = doc.pages[index];
  const cv = new Canvas(mulberry(hash(`${doc.id}:${index}`)));
  const pagePaper = page.kind === 'text' ? (paper === 'black' ? 'black' : (page.paper ?? paper)) : paper;
  switch (page.kind) {
    case 'title':
      titlePage(cv, doc);
      break;
    case 'text':
      textPage(cv, page, pagePaper);
      break;
    case 'calendar':
      calendarPage(cv, page);
      break;
    case 'map':
      mapPage(cv, page);
      break;
    case 'notice':
      noticePage(cv, page);
      break;
    case 'roster':
      rosterPage(cv, page);
      break;
    default:
      page satisfies never;
  }
  // Art pages are paper objects whatever the document's paper; give them a paper's colours.
  const pal = page.kind === 'text' ? pagePaper : page.kind === 'title' ? 'black' : page.kind === 'roster' ? 'ledger' : page.kind === 'notice' ? 'letter' : 'notebook';
  return { pixels: cv.px, palette: palette(pal) };
}

// ---------------------------------------------------------------------------
// The game's formats.

const TIM_SIZE = 20 + 32 + 12 + (PAGE * PAGE) / 2;

/** One page as a 4 bpp TIM, its header laid out as the game's own pages have it. */
export function pageTim(d: Drawn): Uint8Array {
  const tim = new Uint8Array(TIM_SIZE);
  const v = new DataView(tim.buffer);
  v.setUint32(0, 0x10, true);
  v.setUint32(4, 8, true); // 4 bpp, with a CLUT
  v.setUint32(8, 12 + 32, true);
  v.setInt16(12, 0, true);
  v.setInt16(14, 0x1e0, true);
  v.setUint16(16, 16, true);
  v.setUint16(18, 1, true);
  d.palette.forEach((s, i) => {
    const c = i === C.Clear ? 0 : to555(...s.rgb) || 0x0421; // 0 is see-through on the PS1; keep black opaque
    v.setUint16(20 + i * 2, c | (s.stp && i !== C.Clear ? 0x8000 : 0), true);
  });
  v.setUint32(52, 12 + (PAGE * PAGE) / 2, true);
  v.setInt16(56, 0, true);
  v.setInt16(58, 0, true);
  v.setUint16(60, PAGE / 4, true);
  v.setUint16(62, PAGE, true);
  for (let i = 0; i < (PAGE * PAGE) / 2; i++) tim[64 + i] = (d.pixels[i * 2] & 15) | ((d.pixels[i * 2 + 1] & 15) << 4);
  return tim;
}

/** A document's .pix: the page offsets, then the packed pages. */
export function packPix(pages: readonly Drawn[]): Uint8Array {
  if (pages.length > 15) throw new Error('a .pix holds at most 15 pages');
  const packed = pages.map((p) => lzwPack(pageTim(p)));
  const size = 0x40 + packed.reduce((n, p) => n + p.length, 0);
  const out = new Uint8Array(size);
  const v = new DataView(out.buffer);
  let at = 0x40;
  packed.forEach((p, i) => {
    v.setUint32(i * 4, at, true);
    out.set(p, at);
    at += p.length;
  });
  v.setUint32(packed.length * 4, at, true);
  return out;
}

/** Read a page back out of a TIM: its palette indices and its CLUT. */
export function readTim(tim: Uint8Array): { pixels: Uint8Array; clut: number[] } {
  const v = new DataView(tim.buffer, tim.byteOffset, tim.byteLength);
  if (v.getUint32(0, true) !== 0x10 || v.getUint32(4, true) !== 8) throw new Error('not a 4 bpp TIM with a CLUT');
  const clut = Array.from({ length: 16 }, (_, i) => v.getUint16(20 + i * 2, true));
  const w = v.getUint16(60, true) * 4;
  const h = v.getUint16(62, true);
  const pixels = new Uint8Array(w * h);
  for (let i = 0; i < (w * h) / 2; i++) {
    pixels[i * 2] = tim[64 + i] & 15;
    pixels[i * 2 + 1] = tim[64 + i] >> 4;
  }
  return { pixels, clut };
}

export { TIM_SIZE };

/** A page as the reader shows it on black, for the review page. */
export function toImage(d: Drawn, zoom = 2): Image {
  const w = PAGE * zoom;
  const rgb = new Uint8Array(w * w * 3);
  for (let y = 0; y < w; y++)
    for (let x = 0; x < w; x++) {
      const c = d.pixels[Math.floor(y / zoom) * PAGE + Math.floor(x / zoom)];
      const s = c === C.Clear ? BLACK : d.palette[c].rgb;
      rgb.set(s, (y * w + x) * 3);
    }
  return { width: w, height: w, rgb };
}
