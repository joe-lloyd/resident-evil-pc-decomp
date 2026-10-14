// Research: the day's places as one world for the map drafts. Writes JSON
// for world_maps.py: every place with its spot on the mountain (layout.ts), floor size,
// whether it is indoors and its map area, the plan's links, and the
// proposed path places (paths.ts).
//
//   node tools/rebecca/plan/research/world.ts > /tmp/world.json
import { existsSync, readFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { kitRooms } from '../../day/rooms.ts';
import { day } from '../day.ts';
import { AREAS } from '../maps.ts';
import { LAYOUT } from './layout.ts';
import { PATHS } from './paths.ts';

const here = path.dirname(fileURLToPath(import.meta.url));
const inside = new Set([...kitRooms.filter((r) => r.inside).map((r) => r.slug), 'lookout', 'shed', 'save']);

type Rect = { x0: number; z0: number; x1: number; z1: number };
interface RoomJson {
  bounds: Rect;
  walls?: Rect[];
  voids?: Rect[];
  doors?: { to: string; zone: Rect }[];
}
const M = 1700;
const read = (folder: string): RoomJson | undefined => {
  const file = path.join(here, '..', '..', 'day', folder, 'renders', 'room.json');
  return existsSync(file) ? (JSON.parse(readFileSync(file, 'utf8')) as RoomJson) : undefined;
};

function floor(folder: string): [number, number] {
  const b = read(folder)?.bounds;
  return b ? [(b.x1 - b.x0) / M, (b.z1 - b.z0) / M] : [6, 4];
}

/**
 * Where she can stand, as half-metre cells across the floor (1 floor, 0 not:
 * a wall or a drop), and each door's middle, both from the floor's centre in
 * metres. Undefined for a room with no scene record.
 */
const CELL = 0.5;
function walkable(folder: string, indoors: boolean) {
  const j = read(folder);
  if (!j) return undefined;
  const b = j.bounds;
  const cx = (b.x0 + b.x1) / 2 / M;
  const cz = (b.z0 + b.z1) / 2 / M;
  const nx = Math.max(1, Math.round((b.x1 - b.x0) / M / CELL));
  const nz = Math.max(1, Math.round((b.z1 - b.z0) / M / CELL));
  // A map shows the ground, not the furniture: drops always, and outdoors the
  // big things in the way (a building, a cliff, a log stack), not a crate.
  const big = (r: Rect) => ((r.x1 - r.x0) / M) * ((r.z1 - r.z0) / M) >= 6;
  const blocked = [...(indoors ? [] : (j.walls ?? []).filter(big)), ...(j.voids ?? [])];
  const rows: string[] = [];
  for (let k = 0; k < nz; k++) {
    let row = '';
    for (let i = 0; i < nx; i++) {
      const x = b.x0 + (i + 0.5) * CELL * M;
      const z = b.z0 + (k + 0.5) * CELL * M;
      row += blocked.some((r) => x > r.x0 && x < r.x1 && z > r.z0 && z < r.z1) ? '0' : '1';
    }
    rows.push(row);
  }
  const doors = (j.doors ?? []).map((d) => ({ to: d.to, at: [(d.zone.x0 + d.zone.x1) / 2 / M - cx, (d.zone.z0 + d.zone.z1) / 2 / M - cz] }));
  return { cell: CELL, origin: [b.x0 / M - cx, b.z0 / M - cz], rows, doors };
}

const places = day.places.map((p) => ({
  id: p.id,
  name: p.name,
  at: LAYOUT[p.id] ?? p.at,
  floor: floor(p.room ?? p.id),
  walkable: walkable(p.room ?? p.id, inside.has(p.room ?? p.id)),
  inside: inside.has(p.room ?? p.id),
  area: AREAS.find((a) => a.places.includes(p.id))?.id ?? null,
}));
const links = day.links.map((l) => ({ from: l.from, to: l.to, kind: l.kind }));
// A path built into its host is part of that room's floor now; a dropped one is not a place.
console.log(JSON.stringify({ places, links, paths: PATHS.filter((p) => p.host === undefined && process.env.WITH_DROPPED), areas: AREAS }, null, 1));
