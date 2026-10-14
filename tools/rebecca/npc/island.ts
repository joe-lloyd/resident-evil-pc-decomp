// Give a body part its own place on the texture sheet. RE1's people share
// texels between left and right limbs (both forearms sample the same island),
// and Barry's head between its crown and its cheeks, so anything painted on
// one shows on the other. This moves one part's UVs
// onto free texels, in the same half of the sheet if it fits there (keeping
// its palette row and page) or else the other half (with the other half's
// page and row), so the skin can paint it alone. Only the texture fields of
// the moved triangles change.
import { readMesh } from './emd.ts';

const SIDE = 256;
const HALF = SIDE / 2;
/**
 * Free texels kept between a moved island and anything else. The game samples
 * texels without blending (point sampling), so one keeps a texel's rounding
 * at an island's edge on its own island.
 */
const MARGIN = 1;

/** Texels a triangle can sample: its interior and every texel its edges touch. */
function cover(uv: readonly (readonly [number, number])[], mark: (x: number, y: number) => void) {
  const [a, b, c] = uv;
  const xs = uv.map(([u]) => u);
  const ys = uv.map(([, v]) => v);
  const area = (b![0] - a![0]) * (c![1] - a![1]) - (c![0] - a![0]) * (b![1] - a![1]);
  for (let y = Math.min(...ys); y <= Math.max(...ys); y++)
    for (let x = Math.min(...xs); x <= Math.max(...xs); x++) {
      // Any corner of the texel inside the triangle (or a sliver) counts.
      const inside = [0, 1].some((ox) =>
        [0, 1].some((oy) => {
          if (Math.abs(area) < 1e-6) return true;
          const px = x + ox;
          const py = y + oy;
          const w1 = ((px - a![0]) * (c![1] - a![1]) - (c![0] - a![0]) * (py - a![1])) / area;
          const w2 = ((b![0] - a![0]) * (py - a![1]) - (px - a![0]) * (b![1] - a![1])) / area;
          return w1 >= -0.01 && w2 >= -0.01 && 1 - w1 - w2 >= -0.01;
        }),
      );
      if (inside) mark(x, y);
    }
}

/**
 * What to move: a body part's triangles, or with `apart` only those that
 * share texels with one of the part's own triangles at least that many game
 * units higher (Barry's head reuses texels between its crown and its cheeks).
 */
export interface Island {
  readonly part: number;
  readonly apart?: number;
}

/** The TMD with the island's triangles sampling their own copy of their texels. */
export function ownIsland(tmd: Uint8Array, island: Island): Uint8Array {
  const mesh = readMesh(tmd);
  const tris = mesh[island.part]?.triangles ?? [];
  if (!tris.length) throw new Error(`no part ${island.part}`);
  const covers = tris.map((t) => {
    const out = new Set<number>();
    cover(t.uv, (x, y) => out.add(y * SIDE + x));
    return out;
  });
  const height = tris.map((t) => -t.vertices.reduce((sum, i) => sum + mesh[island.part]!.vertices[i]![1], 0) / 3);
  const chosen = tris
    .map((_, i) => i)
    .filter((i) => island.apart === undefined || tris.some((_, j) => height[j]! - height[i]! >= island.apart! && [...covers[i]!].some((k) => covers[j]!.has(k))));
  // What everything else samples, grown by the margin.
  const used = new Uint8Array(SIDE * SIDE);
  const claim = (k: number) => {
    const [x, y] = [k % SIDE, Math.floor(k / SIDE)];
    for (let j = -MARGIN; j <= MARGIN; j++) for (let i = -MARGIN; i <= MARGIN; i++) if (x + i >= 0 && x + i < SIDE && y + j >= 0 && y + j < SIDE) used[(y + j) * SIDE + x + i] = 1;
  };
  mesh.forEach((o, p) =>
    o.triangles.forEach((t, i) => {
      if (p === island.part && chosen.includes(i)) return;
      cover(t.uv, (x, y) => claim(y * SIDE + x));
    }),
  );
  // The chosen triangles in pieces that share texels, each moved whole.
  const pieces: number[][] = [];
  for (const i of chosen) {
    const touching = pieces.filter((piece) => piece.some((j) => [...covers[i]!].some((k) => covers[j]!.has(k))));
    pieces.splice(0, pieces.length, ...pieces.filter((piece) => !touching.includes(piece)), [i, ...touching.flat()]);
  }
  const out = tmd.slice();
  const view = new DataView(out.buffer, out.byteOffset, out.byteLength);
  /** Move a piece to free texels in either half; false when nowhere fits. */
  const move = (piece: number[]): boolean => {
    const shape = [...new Set(piece.flatMap((i) => [...covers[i]!]))];
    const xs = shape.map((k) => k % SIDE);
    const ys = shape.map((k) => Math.floor(k / SIDE));
    const [x0, y0, x1, y1] = [Math.min(...xs), Math.min(...ys), Math.max(...xs), Math.max(...ys)];
    const own = x0 < HALF ? 0 : 1;
    if (x1 >= (own + 1) * HALF) throw new Error(`part ${island.part} spans both halves of the sheet`);
    for (const half of [own, 1 - own])
      for (let dy = -y0; dy + y1 < SIDE; dy++)
        for (let dx = half * HALF - x0; dx + x1 < (half + 1) * HALF; dx++) {
          if (shape.some((k) => used[k + dy * SIDE + dx])) continue;
          for (const k of shape) claim(k + dy * SIDE + dx);
          for (const i of piece) {
            const t = tris[i]!;
            // The other half is the other page and palette row (emd.ts rowAt).
            const turn = half - own;
            view.setUint16(t.at + 6, view.getUint16(t.at + 6, true) + turn * 0x40, true);
            view.setUint16(t.at + 10, view.getUint16(t.at + 10, true) + turn, true);
            for (let c = 0; c < 3; c++) {
              const at = t.at + 4 + c * 4;
              out[at] = tmd[at]! + dx - turn * HALF;
              out[at + 1] = tmd[at + 1]! + dy;
            }
          }
          return true;
        }
    return false;
  };
  // Largest first; a piece that fits nowhere goes a triangle at a time.
  for (const piece of pieces.sort((a, b) => b.length - a.length)) {
    if (move(piece)) continue;
    for (const i of piece) if (!move([i])) throw new Error(`no free place for a triangle of part ${island.part}`);
  }
  return out;
}
