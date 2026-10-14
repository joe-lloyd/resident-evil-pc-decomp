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

function floor(folder: string): [number, number] {
  const file = path.join(here, '..', '..', 'day', folder, 'renders', 'room.json');
  if (!existsSync(file)) return [6, 4];
  const b = (JSON.parse(readFileSync(file, 'utf8')) as { bounds: { x0: number; z0: number; x1: number; z1: number } }).bounds;
  return [(b.x1 - b.x0) / 1700, (b.z1 - b.z0) / 1700];
}

const places = day.places.map((p) => ({
  id: p.id,
  name: p.name,
  at: LAYOUT[p.id] ?? p.at,
  floor: floor(p.room ?? p.id),
  inside: inside.has(p.room ?? p.id),
  area: AREAS.find((a) => a.places.includes(p.id))?.id ?? null,
}));
const links = day.links.map((l) => ({ from: l.from, to: l.to, kind: l.kind }));
console.log(JSON.stringify({ places, links, paths: PATHS, areas: AREAS }, null, 1));
