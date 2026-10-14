// Give Rebecca a knife, shotgun and Magnum that look right in her hands.
//
// RE1's weapon table (g_weaponPathTable, 0x004c1ca8) gives her her own file
// for the Beretta only: her knife, shotgun and Magnum load Jill's w11, w13 and
// w14. The game also ships her own versions, W31, W33 and W34, which nothing
// loads. They are shaped for her, but every textured polygon in them still
// points where Jill's art sits on Jill's texture sheet. A weapon's mesh is
// textured from the player's own sheet (LoadEquippedWeaponAnimation hands it
// to ProcessTmdTextures with the player's page), and Rebecca's sheet
// (enemy/char13.emd) has no gun art, so her shotgun drew red and her Magnum in
// skin tones.
//
// This copies the texels each of her weapon files uses from the player's own
// Jill sheet (enemy/char11.emd) into free space on her sheet, puts Jill's
// colours into unused entries of her second palette row, and points every
// weapon polygon at the copy. Her files go into the REB overlay under the
// names her table loads, so only her mode sees them.
//
// File layouts, read here and written in place (sizes never change):
// - EMD: four offsets at its end: skeleton, animation, mesh (a TMD), texture
//   (an 8 bpp 256x256 TIM with two 256-colour palette rows).
// - EMW: two offsets at its end (LoadEquippedWeaponAnimation reads them at
//   (size & ~3) - 8): animation, mesh (a TMD).
// - TMD textured polygon: after its header word, u0 v0 CBA, u1 v1 TSB, u2 v2,
//   and u3 v3 for a quad. CBA picks the palette row: 0x7800 is row 0 and
//   0x7840 row 1; the engine adds the player's own palette and page to both.

const TMD_ID = 0x41;
const SIDE = 256;
const ROW = 256;
const CBA_ROW0 = 0x7800;
const CBA_ROW1 = 0x7840;
/** TSB of the sheet's left page: 8 bpp, x 0. Its u runs over the whole sheet. */
const TSB_LEFT = 0x80;

export interface Poly {
  /** Offset of the polygon's header word in its file. */
  readonly at: number;
  /** The TMD object it belongs to: a body part, for a character. */
  readonly object: number;
  readonly uv: readonly (readonly [number, number])[];
  readonly cba: number;
  readonly tsb: number;
}

/** The textured polygons of every object of the TMD at `tmd`. */
export function tmdPolys(file: Uint8Array, tmd: number): Poly[] {
  const v = new DataView(file.buffer, file.byteOffset, file.byteLength);
  if (v.getUint32(tmd, true) !== TMD_ID) throw new Error(`no TMD at 0x${tmd.toString(16)}`);
  const objects = v.getUint32(tmd + 8, true);
  const base = tmd + 12;
  const out: Poly[] = [];
  for (let o = 0; o < objects; o++) {
    let p = base + v.getUint32(base + o * 28 + 16, true);
    const count = v.getUint32(base + o * 28 + 20, true);
    for (let k = 0; k < count; k++) {
      const head = v.getUint32(p, true);
      const mode = head >>> 24;
      if (mode & 4) {
        const corners = mode & 8 ? 4 : 3;
        const uv = Array.from({ length: corners }, (_, j) => [file[p + 4 + 4 * j]!, file[p + 5 + 4 * j]!] as const);
        out.push({ at: p, object: o, uv, cba: v.getUint16(p + 6, true), tsb: v.getUint16(p + 10, true) });
      }
      p += 4 + ((head >>> 8) & 0xff) * 4;
    }
  }
  return out;
}

const tail = (file: Uint8Array, count: number, end: number) => {
  const v = new DataView(file.buffer, file.byteOffset, file.byteLength);
  return Array.from({ length: count }, (_, i) => v.getUint32(end - 4 * count + 4 * i, true));
};

/** An EMD's mesh and texture offsets. */
export function emdSections(file: Uint8Array): { mesh: number; tim: number } {
  const [, , mesh, tim] = tail(file, 4, file.length);
  return { mesh: mesh!, tim: tim! };
}

/** An EMW's mesh offset. */
export function emwMesh(file: Uint8Array): number {
  return tail(file, 2, file.length & ~3)[1]!;
}

interface Sheet {
  /** Offset of the 512 palette entries. */
  readonly clut: number;
  /** Offset of the 256x256 palette indices. */
  readonly pixels: number;
}

function sheet(file: Uint8Array, tim: number): Sheet {
  const v = new DataView(file.buffer, file.byteOffset, file.byteLength);
  if (v.getUint32(tim, true) !== 0x10 || v.getUint32(tim + 4, true) !== 9) throw new Error('not an 8 bpp TIM with a palette');
  const clutLen = v.getUint32(tim + 8, true);
  if (v.getUint16(tim + 16, true) !== ROW || v.getUint16(tim + 18, true) !== 2) throw new Error('expected two 256-colour palette rows');
  const img = tim + 8 + clutLen;
  if (v.getUint16(img + 8, true) * 2 !== SIDE || v.getUint16(img + 10, true) !== SIDE) throw new Error('expected a 256x256 sheet');
  return { clut: tim + 20, pixels: img + 12 };
}

const colourAt = (file: Uint8Array, s: Sheet, row: number, index: number) => file[s.clut + (row * ROW + index) * 2]! | (file[s.clut + (row * ROW + index) * 2 + 1]! << 8);
const rowOf = (p: Poly) => (p.cba - CBA_ROW0) >> 6;
/** A polygon's corners in sheet texels: a page further right adds 128 to u. */
const corners = (p: Poly) => p.uv.map(([u, v]) => [u + (p.tsb & 0xf) * 128, v] as const);

/** Texels whose centres a polygon covers, edges included. Quads are corners 0-1-2 and 1-3-2. */
function cover(p: Poly, into: Uint8Array): void {
  const c = corners(p);
  const tris = c.length === 4 ? [[c[0]!, c[1]!, c[2]!], [c[1]!, c[3]!, c[2]!]] : [[c[0]!, c[1]!, c[2]!]];
  for (const [a, b, d] of tris) {
    const x0 = Math.max(0, Math.floor(Math.min(a![0], b![0], d![0])));
    const x1 = Math.min(SIDE - 1, Math.ceil(Math.max(a![0], b![0], d![0])));
    const y0 = Math.max(0, Math.floor(Math.min(a![1], b![1], d![1])));
    const y1 = Math.min(SIDE - 1, Math.ceil(Math.max(a![1], b![1], d![1])));
    const edge = (p: readonly number[], q: readonly number[], x: number, y: number) => (q[0]! - p[0]!) * (y - p[1]!) - (q[1]! - p[1]!) * (x - p[0]!);
    for (let y = y0; y <= y1; y++)
      for (let x = x0; x <= x1; x++) {
        const e = [edge(a!, b!, x + 0.5, y + 0.5), edge(b!, d!, x + 0.5, y + 0.5), edge(d!, a!, x + 0.5, y + 0.5)];
        if (e.every((n) => n >= 0) || e.every((n) => n <= 0)) into[y * SIDE + x] = 1;
      }
  }
  // A sliver can cover no texel centre at all: its corners and edges still sample.
  c.forEach((q, i) => {
    const r = c[(i + 1) % c.length]!;
    const steps = Math.max(Math.abs(r[0] - q[0]), Math.abs(r[1] - q[1]), 1);
    for (let k = 0; k <= steps; k++) {
      const x = Math.min(SIDE - 1, Math.round(q[0] + ((r[0] - q[0]) * k) / steps));
      const y = Math.min(SIDE - 1, Math.round(q[1] + ((r[1] - q[1]) * k) / steps));
      into[y * SIDE + x] = 1;
    }
  });
}

function dilate(mask: Uint8Array, by: number): Uint8Array {
  const out = new Uint8Array(mask.length);
  for (let y = 0; y < SIDE; y++)
    for (let x = 0; x < SIDE; x++) {
      if (!mask[y * SIDE + x]) continue;
      for (let dy = -by; dy <= by; dy++)
        for (let dx = -by; dx <= by; dx++) {
          const yy = y + dy;
          const xx = x + dx;
          if (yy >= 0 && yy < SIDE && xx >= 0 && xx < SIDE) out[yy * SIDE + xx] = 1;
        }
    }
  return out;
}

/** The connected pieces of a mask (touching sideways or corner to corner), as lists of texel indices. */
function pieces(mask: Uint8Array): number[][] {
  const seen = new Uint8Array(mask.length);
  const out: number[][] = [];
  for (let i = 0; i < mask.length; i++) {
    if (!mask[i] || seen[i]) continue;
    const piece: number[] = [];
    const stack = [i];
    seen[i] = 1;
    while (stack.length) {
      const t = stack.pop()!;
      piece.push(t);
      const x = t % SIDE;
      const y = (t / SIDE) | 0;
      for (let dy = -1; dy <= 1; dy++)
        for (let dx = -1; dx <= 1; dx++) {
          const xx = x + dx;
          const yy = y + dy;
          const n = yy * SIDE + xx;
          if (xx >= 0 && xx < SIDE && yy >= 0 && yy < SIDE && mask[n] && !seen[n]) {
            seen[n] = 1;
            stack.push(n);
          }
        }
    }
    out.push(piece);
  }
  return out;
}

/**
 * Where a piece goes on her sheet: the corner of its turned bounding box, and
 * how many quarter turns clockwise. Quarter turns keep every texel whole, so
 * the copy samples exactly as the original does.
 */
interface Spot {
  readonly x0: number;
  readonly y0: number;
  readonly w: number;
  readonly h: number;
  readonly to: { x: number; y: number };
  readonly turns: number;
}

/** A texel of the box, (rx, ry) from its corner, after `turns` quarter turns clockwise. */
function turnTexel(rx: number, ry: number, w: number, h: number, turns: number): [number, number] {
  switch (turns) {
    case 0:
      return [rx, ry];
    case 1:
      return [h - 1 - ry, rx];
    case 2:
      return [w - 1 - rx, h - 1 - ry];
    default:
      return [ry, w - 1 - rx];
  }
}

/** A sampling point, (u, v) from the box's corner in texel edges, after `turns` quarter turns. */
function turnPoint(u: number, v: number, w: number, h: number, turns: number): [number, number] {
  switch (turns) {
    case 0:
      return [u, v];
    case 1:
      return [h - v, u];
    case 2:
      return [w - u, h - v];
    default:
      return [v, w - u];
  }
}

/**
 * The first spot, top to bottom and left to right, upright first and then
 * turned, where every texel of `piece` lands on free sheet. Marks those texels
 * and one round them used. Nothing reaches the last row or column, so a
 * turned UV of 256 never needs a byte.
 */
function place(free: Uint8Array, piece: readonly number[]): Spot {
  const xs = piece.map((t) => t % SIDE);
  const ys = piece.map((t) => (t / SIDE) | 0);
  const x0 = Math.min(...xs);
  const y0 = Math.min(...ys);
  const w = Math.max(...xs) - x0 + 1;
  const h = Math.max(...ys) - y0 + 1;
  const cells = piece.map((t) => (((t / SIDE) | 0) - y0) * SIDE + (t % SIDE) - x0);
  for (let turns = 0; turns < 4; turns++) {
    const [bw, bh] = turns % 2 ? [h, w] : [w, h];
    const rel = cells.map((c) => turnTexel(c % SIDE, (c / SIDE) | 0, w, h, turns));
    for (let y = 0; y + bh < SIDE; y++)
      for (let x = 0; x + bw < SIDE; x++) {
        if (!rel.every(([rx, ry]) => free[(y + ry) * SIDE + x + rx] === 1)) continue;
        for (const [rx, ry] of rel)
          for (let yy = Math.max(0, y + ry - 1); yy <= Math.min(SIDE - 1, y + ry + 1); yy++)
            for (let xx = Math.max(0, x + rx - 1); xx <= Math.min(SIDE - 1, x + rx + 1); xx++) free[yy * SIDE + xx] = 0;
        return { x0, y0, w, h, to: { x, y }, turns };
      }
  }
  throw new Error(`no room on her sheet for a ${w}x${h} piece`);
}

/** The body part that is the right hand, object 14 of a character's mesh; the weapon files replace it. */
const HAND = 14;

type Tri = readonly [readonly [number, number], readonly [number, number], readonly [number, number]];

const triangles = (p: Poly): Tri[] => {
  const c = corners(p);
  return c.length === 4 ? [[c[0]!, c[1]!, c[2]!], [c[1]!, c[3]!, c[2]!]] : [[c[0]!, c[1]!, c[2]!]];
};

function barycentric(t: Tri, x: number, y: number): [number, number, number] {
  const [[x0, y0], [x1, y1], [x2, y2]] = t;
  const d = (y1 - y2) * (x0 - x2) + (x2 - x1) * (y0 - y2);
  if (d === 0) return [-Infinity, -Infinity, -Infinity];
  const a = ((y1 - y2) * (x - x2) + (x2 - x1) * (y - y2)) / d;
  const b = ((y2 - y0) * (x - x2) + (x0 - x2) * (y - y2)) / d;
  return [a, b, 1 - a - b];
}

/**
 * Capcom drew every character's hand with the same polygons, each at its own
 * place on its own sheet. Pairing Jill's hand with Rebecca's polygon by
 * polygon carries a point of Jill's hand art to the same spot of Rebecca's,
 * triangle by triangle. Returns the point, with the palette and page her
 * hand draws with, or nothing for a point off Jill's hand.
 */
function handMap(jill: Uint8Array, rebecca: Uint8Array): (x: number, y: number) => { x: number; y: number; cba: number; tsb: number } | undefined {
  const theirs = tmdPolys(jill, emdSections(jill).mesh).filter((p) => p.object === HAND);
  const hers = tmdPolys(rebecca, emdSections(rebecca).mesh).filter((p) => p.object === HAND);
  if (theirs.length !== hers.length || theirs.some((p, i) => p.uv.length !== hers[i]!.uv.length)) throw new Error("Jill's and Rebecca's hands are not the same mesh");
  const pairs = theirs.flatMap((p, i) => triangles(p).map((t, k) => ({ from: t, to: triangles(hers[i]!)[k]!, cba: hers[i]!.cba, tsb: hers[i]!.tsb })));
  return (x, y) => {
    let best: { w: [number, number, number]; pair: (typeof pairs)[number] } | undefined;
    for (const pair of pairs) {
      const w = barycentric(pair.from, x, y);
      if (!best || Math.min(...w) > Math.min(...best.w)) best = { w, pair };
    }
    // A corner on the hand's outline sits a little outside every triangle:
    // pull it onto the nearest one, so it always lands on her hand.
    if (!best || Math.min(...best.w) < -0.15) return undefined;
    const [w0, w1, w2] = best.w.map((n) => Math.max(0, n));
    const sum = w0! + w1! + w2!;
    const [a, b, c] = [w0! / sum, w1! / sum, w2! / sum];
    const t = best.pair.to;
    return { x: a * t[0][0] + b * t[1][0] + c * t[2][0], y: a * t[0][1] + b * t[1][1] + c * t[2][1], cba: best.pair.cba, tsb: best.pair.tsb };
  };
}

export interface Weapon {
  /** Her own file, e.g. W33.EMW. */
  readonly file: Uint8Array;
}

export interface Arms {
  /** Her model with the weapons' art on its sheet. */
  readonly rebecca: Uint8Array;
  /** Her weapon files, in the order given, pointed at that art. */
  readonly weapons: Uint8Array[];
}

/**
 * Copy what each of her weapon files samples from Jill's sheet onto hers and
 * point the files at it. `jill` is enemy/char11.emd and `rebecca`
 * enemy/char13.emd, both the player's own. `keep` are weapon files already
 * drawn for her sheet (her Beretta, W32), whose texels stay as they are.
 * Nothing passed in is modified.
 */
export function buildArms(jill: Uint8Array, rebecca: Uint8Array, weapons: readonly Weapon[], keep: readonly Uint8Array[] = []): Arms {
  const her = rebecca.slice();
  const jillSheet = sheet(jill, emdSections(jill).tim);
  const herSheet = sheet(her, emdSections(her).tim);
  const body = tmdPolys(her, emdSections(her).mesh);

  // Where her body and kept weapons draw, with room for filtering, and the palette entries her second row already uses.
  const used = new Uint8Array(SIDE * SIDE);
  const row1 = new Uint8Array(SIDE * SIDE);
  for (const p of [...body, ...keep.flatMap((f) => tmdPolys(f, emwMesh(f)))]) cover(p, rowOf(p) === 1 ? row1 : used);
  for (let i = 0; i < used.length; i++) used[i] = used[i]! | row1[i]!;
  const free = dilate(used, 1).map((u) => (u ? 0 : 1));
  const takenRow1 = new Set<number>([0]);
  dilate(row1, 1).forEach((m, i) => m && takenRow1.add(her[herSheet.pixels + i]!));

  const out = weapons.map((w) => w.file.slice());
  const polys = out.map((f) => tmdPolys(f, emwMesh(f)));
  for (const p of polys.flat()) {
    if (rowOf(p) !== 0 || p.tsb !== TSB_LEFT) throw new Error(`a weapon polygon at 0x${p.at.toString(16)} is not on Jill's first palette row and left page`);
  }

  // Copy each piece with Jill's colours, giving every new colour a free entry of her second row.
  const entries = new Map<number, number>();
  const freeEntries = Array.from({ length: ROW }, (_, i) => i).filter((i) => !takenRow1.has(i));
  const entryFor = (colour: number) => {
    let e = entries.get(colour);
    if (e === undefined) {
      e = freeEntries.shift();
      if (e === undefined) throw new Error("her second palette row has no free entry for Jill's colours");
      entries.set(colour, e);
      her[herSheet.clut + (ROW + e) * 2] = colour & 0xff;
      her[herSheet.clut + (ROW + e) * 2 + 1] = colour >> 8;
    }
    return e;
  };
  // A polygon drawn from Jill's hand art takes the same spot of Rebecca's own hand.
  const toHer = handMap(jill, her);
  type OnHer = NonNullable<ReturnType<typeof toHer>>;
  const mapped = new Map<Poly, OnHer[]>();
  for (const p of polys.flat()) {
    const to = corners(p).map(([x, y]) => toHer(x, y));
    const onHer = to.filter((q): q is OnHer => q !== undefined);
    if (onHer.length === to.length) mapped.set(p, onHer);
  }

  // The rest is gun: what each polygon samples on Jill's sheet, one texel wider for filtering.
  const all = polys.flatMap((list, file) => list.filter((p) => !mapped.has(p)).map((p) => ({ p, file })));
  const masks = all.map(({ p }) => {
    const m = new Uint8Array(SIDE * SIDE);
    cover(p, m);
    return dilate(m, 1);
  });
  const texelsOf = (m: Uint8Array) => m.reduce<number[]>((acc, on, i) => (on ? (acc.push(i), acc) : acc), []);

  // Copy the connected pieces whole where they fit; split one that does not into its polygons.
  const need = new Uint8Array(SIDE * SIDE);
  masks.forEach((m) => m.forEach((on, i) => on && (need[i] = 1)));
  const units = pieces(need)
    .map((texels) => {
      const inside = new Set(texels);
      return { texels, members: all.map((_, i) => i).filter((i) => masks[i]!.some((on, t) => on && inside.has(t))) };
    })
    .sort((a, b) => b.texels.length - a.texels.length);
  const spotOf = new Map<number, Spot>();
  const copy = (texels: readonly number[], members: readonly number[]) => {
    const spot = place(free, texels);
    for (const t of texels) {
      const [rx, ry] = turnTexel((t % SIDE) - spot.x0, ((t / SIDE) | 0) - spot.y0, spot.w, spot.h, spot.turns);
      her[herSheet.pixels + (spot.to.y + ry) * SIDE + spot.to.x + rx] = entryFor(colourAt(jill, jillSheet, 0, jill[jillSheet.pixels + t]!));
    }
    for (const i of members) spotOf.set(i, spot);
  };
  for (const u of units) {
    try {
      copy(u.texels, u.members);
    } catch {
      // Too big to go whole: each polygon on its own, largest first.
      for (const i of [...u.members].sort((a, b) => texelsOf(masks[b]!).length - texelsOf(masks[a]!).length)) copy(texelsOf(masks[i]!), [i]);
    }
  }

  // Point every hand polygon at her own hand, with the palette and page her hand draws with.
  polys.forEach((list, file) => {
    const f = out[file]!;
    for (const p of list) {
      const to = mapped.get(p);
      if (!to) continue;
      const page = (to[0]!.tsb & 0xf) * 128;
      to.forEach((q, j) => {
        f[p.at + 4 + 4 * j] = Math.round(q.x) - page;
        f[p.at + 5 + 4 * j] = Math.round(q.y);
      });
      f[p.at + 6] = to[0]!.cba & 0xff;
      f[p.at + 7] = to[0]!.cba >> 8;
      f[p.at + 10] = to[0]!.tsb & 0xff;
      f[p.at + 11] = to[0]!.tsb >> 8;
    }
  });

  // Point every gun polygon at its copy, on her second palette row.
  all.forEach(({ p, file }, i) => {
    const f = out[file]!;
    const m = spotOf.get(i)!;
    p.uv.forEach(([pu, pv], j) => {
      const [tu, tv] = turnPoint(pu + (p.tsb & 0xf) * 128 - m.x0, pv - m.y0, m.w, m.h, m.turns);
      f[p.at + 4 + 4 * j] = m.to.x + tu;
      f[p.at + 5 + 4 * j] = m.to.y + tv;
    });
    f[p.at + 6] = CBA_ROW1 & 0xff;
    f[p.at + 7] = CBA_ROW1 >> 8;
  });
  return { rebecca: her, weapons: out };
}

/** A texel's colour as a polygon on palette `row` sees it. */
export function texel(file: Uint8Array, row: number, x: number, y: number): number {
  const s = sheet(file, emdSections(file).tim);
  return colourAt(file, s, row, file[s.pixels + y * SIDE + x]!);
}
