// How RE1 spaces its save rooms, measured from the player's own PC room files:
// how many typewriter rooms, and how many doors each room is from the nearest
// one. saves.ts holds her day to the same numbers (RE1 there).
//
//   node tools/rebecca/plan/re1-saves.ts <rae cli.mjs> <game folder with Stage1..Stage5>
//
// Reads Chris's rooms (ROOMsrr0.RDT) in stages 1 to 5; 6 and 7 are the mansion
// again. A door counts both ways, locked or not. Rooms no door reaches
// (cutscene rooms) are left out.
import { execFileSync } from 'node:child_process';
import { readdirSync } from 'node:fs';
import path from 'node:path';

const [cli, game] = process.argv.slice(2);
if (!cli || !game) {
  console.error('usage: node tools/rebecca/plan/re1-saves.ts <rae cli.mjs> <game folder>');
  process.exit(2);
}
const next = new Map<string, Set<string>>();
const link = (a: string, b: string) => {
  if (!next.has(a)) next.set(a, new Set());
  next.get(a)!.add(b);
};
const saves: string[] = [];
const sideRooms: string[] = [];
// Rooms rae can't read the script of; the doors into them still count.
const unread: string[] = [];
for (let stage = 1; stage <= 5; stage++) {
  const dir = path.join(game, `Stage${stage}`);
  for (const file of readdirSync(dir).filter((f) => /^ROOM[0-9A-F]{3}0\.RDT$/i.test(f))) {
    const room = file.slice(4, 7).toUpperCase();
    if (!next.has(room)) next.set(room, new Set());
    let script: string;
    try {
      script = execFileSync('node', [cli, 'script', path.join(dir, file)], { encoding: 'utf8', stdio: ['ignore', 'pipe', 'ignore'] });
    } catch {
      unread.push(room);
      continue;
    }
    if (script.includes('SCE_TYPEWRITER')) saves.push(room);
    // ROOM_Srr is a room in the same stage, ROOM_srr one in stage s.
    for (const m of script.matchAll(/door_aot_set\([^;]*?ROOM_(S|\d)([0-9A-F]{2})/g)) {
      const to = (m[1] === 'S' ? room[0] : m[1]) + m[2];
      if (to[0]! > '5') continue;
      link(room, to);
      link(to, room);
    }
  }
}
for (const s of saves) if (next.get(s)!.size === 1) sideRooms.push(s);
const dist = new Map(saves.map((s) => [s, 0]));
let edge = [...saves];
for (let d = 1; edge.length; d++) {
  edge = [...new Set(edge.flatMap((r) => [...next.get(r)!]))].filter((r) => !dist.has(r));
  for (const r of edge) dist.set(r, d);
}
const doors = [...dist.values()];
console.log(`${dist.size} rooms reached by a door, ${saves.length} with a typewriter: ${saves.join(' ')}`);
console.log(`doors to the nearest typewriter: mean ${(doors.reduce((a, b) => a + b, 0) / doors.length).toFixed(2)}, most ${Math.max(...doors)}`);
if (unread.length) console.log(`scripts rae couldn't read: ${unread.join(' ')}`);
console.log(`dead-end save rooms (one door): ${sideRooms.length} of ${saves.length}`);
