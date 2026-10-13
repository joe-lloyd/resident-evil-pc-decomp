// Write the scripts and messages of the rooms built with blender/kit.py from
// what their scenes record (renders/room.json: doors, things to check, the
// thought on first coming in). A door from A to B lands her where B's door
// back to A says to arrive; the hand-written rooms give their arrivals in
// BUILT_ARRIVALS. A door to a room not rendered yet is left out.
//
//   node tools/rebecca/day/scripts.ts
//
// Writes day/<slug>/room.c and room.msg.txt for every kit room. Edit the
// scene, not these files.
import { existsSync, readFileSync, writeFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { dayRooms } from './rooms.ts';
import type { DayRoom } from './room.ts';

const here = path.dirname(fileURLToPath(import.meta.url));

type Zone = { x0: number; z0: number; x1: number; z1: number };
type Arrive = { x: number; z: number; angle: number };
interface KitDoor {
  to: string;
  zone: Zone;
  arrive: Arrive;
}
interface KitJson {
  doors?: KitDoor[];
  checks?: { zone: Zone; text: string }[];
  entry?: string | null;
}

/** Where she stands in a hand-written room on arriving from a kit room, by that room's slug. */
const BUILT_ARRIVALS: Record<string, Record<string, Arrive>> = {
  // The yard (x 2-18 m, y 2-12.2 m): in from the forestry road on the truck's
  // tyre tracks at the west edge, facing east; in from the woods at the
  // north-east, where the drag marks go into the trees, facing west.
  yard: {
    road: { x: 6120, z: 18360, angle: 0 },
    woods: { x: 27200, z: 10880, angle: 2048 },
  },
  // The bridge: on its far bank (y 15-18 m) from the gondola station, facing
  // back over the bridge; on its near bank from the flume's ride down.
  bridge: {
    platform: { x: 10200, z: 27710, angle: 1024 },
    flume: { x: 14450, z: 6800, angle: 3072 },
  },
};

/** Common flags for "she has been here", one per kit room with a first thought; the built rooms use 200-206. */
const FIRST_FLAG = 207;
const LAST_FLAG = 255;
/** Message text: lines this many characters at most, three lines to a page. */
const LINE = 26;
const PAGE_LINES = 3;

/** The hand-written rooms indoors; the kit rooms say so themselves. */
const BUILT_INSIDE = new Set(['lookout', 'shed']);
const isInside = (r: DayRoom) => ('inside' in r ? r.inside : BUILT_INSIDE.has(r.slug));

const roomName = (r: Pick<DayRoom, 'stage' | 'room'>) => `ROOM_${r.stage + 1}${r.room.toString(16).toUpperCase().padStart(2, '0')}`;

function readKit(slug: string): KitJson | undefined {
  const file = path.join(here, slug, 'renders', 'room.json');
  if (!existsSync(file)) return undefined;
  const json = JSON.parse(readFileSync(file, 'utf8')) as KitJson;
  return json.doors ? json : undefined;
}

/** Wrap a page's words to LINE characters, and spill past PAGE_LINES onto more pages. */
export function pages(text: string): string[] {
  const out: string[] = [];
  for (const para of text.split('\n')) {
    const lines: string[] = [];
    let line = '';
    for (const word of para.split(/\s+/).filter(Boolean)) {
      if (line && (line + ' ' + word).length > LINE) {
        lines.push(line);
        line = word;
      } else line = line ? `${line} ${word}` : word;
    }
    if (line) lines.push(line);
    // Pages of PAGE_LINES; a last page of one line borrows one from the page before.
    const sizes: number[] = [];
    for (let left = lines.length; left > 0; left -= PAGE_LINES) sizes.push(Math.min(PAGE_LINES, left));
    if (sizes.length > 1 && sizes.at(-1) === 1 && sizes.at(-2) === PAGE_LINES) {
      sizes[sizes.length - 2]! -= 1;
      sizes[sizes.length - 1]! += 1;
    }
    let at = 0;
    for (const n of sizes) {
      out.push(lines.slice(at, at + n).join('\\n'));
      at += n;
    }
  }
  return out;
}

const message = (n: number, text: string) => `${n}: ${pages(text).map((p) => `\\n${p}`).join('\\p{0}')}`;

const size = (z: Zone) => `${z.x0}, ${z.z0}, ${z.x1 - z.x0}, ${z.z1 - z.z0}`;

function main(): void {
  const bySlug = new Map(dayRooms.map((r) => [r.slug, r]));
  const kits = new Map(dayRooms.flatMap((r) => {
    const k = readKit(r.slug);
    return k ? [[r.slug, k] as const] : [];
  }));
  let flag = FIRST_FLAG;
  for (const [slug, kit] of kits) {
    const spec = bySlug.get(slug)!;
    const lines: string[] = [
      `// ${slug} (${roomName(spec).slice(5)}), written by day/scripts.ts from day/${slug}/scene.py: edit the scene, not this file.`,
      '// init procedure 0',
    ];
    let id = 0;
    for (const d of kit.doors ?? []) {
      const target = bySlug.get(d.to);
      const back = kits.get(d.to)?.doors?.find((b) => b.to === slug)?.arrive ?? BUILT_ARRIVALS[d.to]?.[slug];
      if (!target || !back) {
        lines.push(`// To ${d.to}: not built yet.`);
        continue;
      }
      // Between two outdoor rooms she walks the dark path and leaves on touch;
      // into or out of a building a door opens, with the action button.
      const walk = !isInside(spec) && !isInside(target);
      const [variant, sfx, type] = walk ? [0, 15, 48] : [0, 0, 0];
      lines.push(`// To ${d.to}.`);
      lines.push(`door_aot_set(${id++}, ${size(d.zone)}, ${variant}, ${sfx}, ${type}, 4, 0, ${roomName(target)}, ${back.x}, 0, ${back.z}, ${back.angle}, UNLOCKED, ${walk ? 1 : 129});`);
    }
    const msgs = [kit.entry ?? '...'];
    for (const c of kit.checks ?? []) {
      lines.push(`aot_set(${id++}, ${size(c.zone)}, SCE_MESSAGE, 129, ${128 + msgs.length}, 0, 255, 0, 0, 0);`);
      msgs.push(c.text);
    }
    lines.push('return;', '', '// main procedure 0');
    if (kit.entry && flag <= LAST_FLAG) {
      lines.push(`if (ck(FG_COMMON, ${flag}, 1)) {`, `    set(FG_COMMON, ${flag}, 0);`, '    message(128, 255, 0);', '}');
      flag++;
    }
    lines.push('return;', '');
    writeFileSync(path.join(here, slug, 'room.c'), lines.join('\n'));
    writeFileSync(path.join(here, slug, 'room.msg.txt'), msgs.map((m, i) => message(i, m)).join('\n') + '\n');
    console.log(`${slug}: ${kit.doors?.length ?? 0} doors, ${kit.checks?.length ?? 0} checks`);
  }
}

if (process.argv[1] === fileURLToPath(import.meta.url)) main();
