// What the game tests know of a kit room from its scene's records
// (day/<slug>/renders/room.json) and its script (room.c): where she can walk
// from where she comes in, and which doors open on the action button.
// tour.ts, puzzles.ts and music.ts share it.
import { existsSync, readFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import type { GameLink } from '../link.ts';
import { faceTowards } from '../flows.ts';

export const day = path.join(path.dirname(fileURLToPath(import.meta.url)), '..', '..', 'rebecca', 'day');
export type Rect = { x0: number; z0: number; x1: number; z1: number };
export interface Json {
  bounds: Rect;
  doors?: { to: string; zone: Rect; arrive: { x: number; z: number } }[];
  walls?: Rect[];
  voids?: Rect[];
  checks?: { zone: Rect }[];
  spots?: { step: string; zone: Rect }[];
}
export const read = (slug: string): Json | undefined => {
  const f = path.join(day, slug, 'renders', 'room.json');
  return existsSync(f) ? (JSON.parse(readFileSync(f, 'utf8')) as Json) : undefined;
};

/** Her body's reach round the point she stands on, in game units. */
export const BODY = 450;
export const inside = (r: Rect, x: number, z: number, pad = 0) => x > r.x0 - pad && x < r.x1 + pad && z > r.z0 - pad && z < r.z1 + pad;

/** Whether the game has this door firing on the action button (it is in the room script as 0x80). */
export function opens(slug: string, zone: Rect): boolean {
  const c = readFileSync(path.join(day, slug, 'room.c'), 'utf8');
  for (const m of c.matchAll(/door_aot_set\(\d+, (\d+), (\d+), (\d+), (\d+),.*, (\d+)\);/g)) {
    if (Number(m[1]) === zone.x0 && Number(m[2]) === zone.z0) return (Number(m[5]) & 0x80) !== 0;
  }
  throw new Error(`no door at (${zone.x0}, ${zone.z0}) in ${slug}/room.c`);
}

/** Grid step for working out where she can walk, in game units. */
const CELL = 250;

/**
 * The floor she can reach from where she comes into the room (any door's
 * arrival), keeping her body clear of walls and drops and out of the room's
 * walk-through doors, which would take her out. Returns the reachable cell
 * centres.
 */
export function walkable(json: Json, touchZones: Rect[]): [number, number][] {
  const b = json.bounds;
  const blockers = [...(json.walls ?? []), ...(json.voids ?? [])];
  const free = (x: number, z: number) =>
    inside(b, x, z, -BODY) && !blockers.some((r) => inside(r, x, z, BODY)) && !touchZones.some((r) => inside(r, x, z));
  const nx = Math.ceil((b.x1 - b.x0) / CELL);
  const nz = Math.ceil((b.z1 - b.z0) / CELL);
  const at = (i: number, k: number): [number, number] => [b.x0 + (i + 0.5) * CELL, b.z0 + (k + 0.5) * CELL];
  const seen = new Set<number>();
  const queue: [number, number][] = [];
  for (const d of json.doors ?? []) {
    const i = Math.floor((d.arrive.x - b.x0) / CELL);
    const k = Math.floor((d.arrive.z - b.z0) / CELL);
    // She may arrive a little inside a wall's reach: start from the nearest free cell.
    let best: [number, number] | undefined;
    for (let r = 0; r <= 4 && !best; r++) {
      for (let di = -r; di <= r && !best; di++) for (let dk = -r; dk <= r && !best; dk++) {
        const [x, z] = at(i + di, k + dk);
        if (i + di >= 0 && i + di < nx && k + dk >= 0 && k + dk < nz && free(x, z)) best = [i + di, k + dk];
      }
    }
    if (best && !seen.has(best[0] * 4096 + best[1])) {
      seen.add(best[0] * 4096 + best[1]);
      queue.push(best);
    }
  }
  const out: [number, number][] = [];
  while (queue.length) {
    const [i, k] = queue.pop()!;
    out.push(at(i, k));
    for (const [di, dk] of [[1, 0], [-1, 0], [0, 1], [0, -1]]) {
      const ni = i + di!, nk = k + dk!;
      if (ni < 0 || nk < 0 || ni >= nx || nk >= nz || seen.has(ni * 4096 + nk)) continue;
      const [x, z] = at(ni, nk);
      if (!free(x, z)) continue;
      seen.add(ni * 4096 + nk);
      queue.push([ni, nk]);
    }
  }
  return out;
}

/** The reachable spot nearest `x, z` that passes `ok`. */
export function nearest(cells: [number, number][], x: number, z: number, ok: (c: [number, number]) => boolean): [number, number] | undefined {
  let best: [number, number] | undefined;
  for (const c of cells) if (ok(c) && (!best || Math.hypot(c[0] - x, c[1] - z) < Math.hypot(best[0] - x, best[1] - z))) best = c;
  return best && [Math.round(best[0]), Math.round(best[1])];
}

/**
 * A point to face to go through a door: straight out across the edge of the
 * floor the door is nearest. Facing the door's own middle fails when she
 * stands nearly on it, and the game wants her facing the door.
 */
export function outward(json: Json, zone: Rect): [number, number] {
  const b = json.bounds;
  const cx = (zone.x0 + zone.x1) / 2;
  const cz = (zone.z0 + zone.z1) / 2;
  const edges: [number, number, number][] = [
    [zone.x0 - b.x0, -1, 0],
    [b.x1 - zone.x1, 1, 0],
    [zone.z0 - b.z0, 0, -1],
    [b.z1 - zone.z1, 0, 1],
  ];
  const [, dx, dz] = edges.sort((p, q) => p[0] - q[0])[0]!;
  return [cx + dx * 3000, cz + dz * 3000];
}

/** How far ahead of her the game looks for a zone she is acting on or using an item at (update_player_position). */
const REACH = 600;

/** Stand her where the point she reaches falls in the spot, facing its middle. */
export async function stand(link: GameLink, slug: string, zone: Rect): Promise<void> {
  const json = read(slug)!;
  const touch = (json.doors ?? []).filter((d) => !opens(slug, d.zone)).map((d) => d.zone);
  const cx = (zone.x0 + zone.x1) / 2;
  const cz = (zone.z0 + zone.z1) / 2;
  const reaches = ([x, z]: [number, number]) => {
    const d = Math.hypot(cx - x, cz - z) || 1;
    return inside(zone, x + ((cx - x) / d) * REACH, z + ((cz - z) / d) * REACH);
  };
  const at = nearest(walkable(json, touch), cx, cz, reaches);
  if (!at) throw new Error('nowhere she can walk to reaches its spot');
  await link.place(at[0], at[1]);
  await link.frames(6);
  await faceTowards(link, cx, cz);
}
