// Camera flicker on a built overlay, worked out from its room files with the
// engine's own switch test (Room.cpp check_camera_switch, ported as
// camera-zones.ts inQuad): at every spot of the floor (a 600-unit grid) and in eight
// directions, she walks in, then sways 150 units back and forth three times.
// Two or more cuts during the sway is a flicker.
//
//   node tools/rebecca/day/sway.ts <REB build folder> [<another to compare>]
import { existsSync, readFileSync, readdirSync } from 'node:fs';
import path from 'node:path';
import { blocked, collisionShapes } from '../../harness/room-map.ts';
import { inQuad, type Quad } from './camera-zones.ts';

type Trigger = { from: number; to: number; quad: Quad };

/** The switch-zone table at RDT+0x48: groups by camFrom, each opening with a header that is not tested. */
export function triggers(rdt: Uint8Array): Trigger[] {
  const view = new DataView(rdt.buffer, rdt.byteOffset, rdt.byteLength);
  const cameras = view.getUint8(1);
  const out: Trigger[] = [];
  let group = -1;
  for (let at = view.getUint32(0x48, true); at + 20 <= view.byteLength; at += 20) {
    const to = view.getUint16(at, true);
    const from = view.getUint16(at + 2, true);
    if (from >= cameras) break;
    if (from !== group) {
      group = from;
      continue;
    }
    const p = (i: number) => [view.getUint16(at + 4 + i * 4, true), view.getUint16(at + 6 + i * 4, true)] as const;
    out.push({ from, to, quad: [p(0), p(1), p(2), p(3)] });
  }
  return out;
}

/** Each camera's triggers with their bounds, so a step tests only the quads it could be in. */
function byCamera(table: Trigger[]): Map<number, (Trigger & { x0: number; z0: number; x1: number; z1: number })[]> {
  const out = new Map<number, (Trigger & { x0: number; z0: number; x1: number; z1: number })[]>();
  for (const t of table) {
    const xs = t.quad.map((p) => p[0]);
    const zs = t.quad.map((p) => p[1]);
    const list = out.get(t.from) ?? [];
    list.push({ ...t, x0: Math.min(...xs), z0: Math.min(...zs), x1: Math.max(...xs), z1: Math.max(...zs) });
    out.set(t.from, list);
  }
  return out;
}

/** The camera after each step of a walk, from `camera`, as check_camera_switch cuts. */
function walk(groups: ReturnType<typeof byCamera>, camera: number, steps: readonly (readonly [number, number])[]): number[] {
  return steps.map(([x, z]) => {
    const hit = groups.get(camera)?.find((t) => x >= t.x0 && x <= t.x1 && z >= t.z0 && z <= t.z1 && inQuad(t.quad, x, z));
    if (hit) camera = hit.to;
    return camera;
  });
}

/** Share of spots and directions where swaying flickers, and of those where any cut happens at all. */
export function swayRoom(rdt: Uint8Array): { tries: number; flicker: number; borders: number } {
  const table = triggers(rdt);
  const groups = byCamera(table);
  const shapes = collisionShapes(rdt);
  const xs = shapes.flatMap((s) => [s.xMin, s.xMax]);
  const zs = shapes.flatMap((s) => [s.zMin, s.zMax]);
  let tries = 0;
  let flicker = 0;
  let borders = 0;
  for (let x = Math.min(...xs); x < Math.max(...xs); x += 600) {
    for (let z = Math.min(...zs); z < Math.max(...zs); z += 600) {
      if (blocked(shapes, x, z)) continue;
      for (let d = 0; d < 8; d++) {
        const dx = Math.cos((d * Math.PI) / 4);
        const dz = Math.sin((d * Math.PI) / 4);
        const at = (t: number) => [x + dx * t, z + dz * t] as const;
        // Walk in from 1200 back, from whatever camera the start of the walk leaves her on.
        const lead: (readonly [number, number])[] = [];
        for (let t = -1200; t <= 0; t += 30) lead.push(at(t));
        const start = walk(groups, table[0]?.from ?? 0, [at(-1200), at(-1200)]).at(-1)!;
        const into = walk(groups, start, lead).at(-1)!;
        const sway: (readonly [number, number])[] = [];
        for (let k = 0; k < 3; k++) {
          for (let t = 0; t >= -150; t -= 30) sway.push(at(t));
          for (let t = -150; t <= 0; t += 30) sway.push(at(t));
        }
        const cams = walk(groups, into, sway);
        const cuts = cams.filter((c, i) => c !== (i ? cams[i - 1] : into)).length;
        tries++;
        if (cuts) borders++;
        if (cuts >= 2) flicker++;
      }
    }
  }
  return { tries, flicker, borders };
}

if (import.meta.url === `file://${process.argv[1]}`) {
  const dirs = process.argv.slice(2);
  if (!dirs.length) throw new Error('usage: sway.ts <REB build folder> [<another>]');
  const rooms = new Map<string, string[]>();
  dirs.forEach((dir, i) => {
    for (let s = 1; s <= 7; s++) {
      const stage = path.join(dir, 'REB', `Stage${s}`);
      if (!existsSync(stage)) continue;
      for (const f of readdirSync(stage).filter((f) => /^ROOM\w{3}0\.RDT$/.test(f))) {
        const row = rooms.get(f) ?? new Array(dirs.length).fill('');
        row[i] = path.join(stage, f);
        rooms.set(f, row);
      }
    }
  });
  const total = dirs.map(() => ({ tries: 0, flicker: 0 }));
  for (const [name, files] of [...rooms].sort()) {
    const cells = files.map((f, i) => {
      const rdt = f ? new Uint8Array(readFileSync(f)) : undefined;
      // A file too short for its header is a stub, not a room.
      if (!rdt || rdt.length < 0x94) return '-';
      const r = swayRoom(rdt);
      total[i]!.tries += r.tries;
      total[i]!.flicker += r.flicker;
      return `${r.flicker} of ${r.tries} sways flicker`;
    });
    console.log(`${name.slice(4, 7)}  ${cells.join('   |   ')}`);
  }
  console.log(`all  ${total.map((t) => `${t.flicker} of ${t.tries} (${((100 * t.flicker) / Math.max(1, t.tries)).toFixed(2)}%)`).join('   |   ')}`);
}
