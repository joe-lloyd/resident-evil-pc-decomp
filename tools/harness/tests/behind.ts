// Rebecca behind things, in the game: for each camera of each room, stand her
// where its masks (occluders.ts) should cover part of her, and take a
// picture, so a page shows whether she goes behind the post, the truck or the
// hut's corner instead of being drawn over it.
//
//   OVERLAY=<REB build folder> node tools/harness/tests/behind.ts <out dir> [slug ...]
//
// The spot is the one on the camera's floor where the most of her body is
// covered without all of it: some of her hidden, some showing. Writes
// <out dir>/<slug>-cam<N>.png and index.html. Needs the engine and the overlay
// deployed, in the Rebecca game folder (RE1_LAB_GAME_DIR).
import { existsSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import path from 'node:path';
import { open } from '../lab.ts';
import { settle } from '../flows.ts';
import { snapshot } from '../snapshot.ts';
import { occluders, standableIn } from '../../rebecca/occluders.ts';
import { autoFloors, HEIGHT, project, readDepth, type Rect } from '../../rebecca/day/floors.ts';
import { dayRooms } from '../../rebecca/day/rooms.ts';
import { FRAME_W } from '../../rebecca/masks.ts';

const dayDir = path.join(import.meta.dirname, '..', '..', 'rebecca', 'day');
const [out, ...only] = process.argv.slice(2);
if (!out) throw new Error('usage: behind.ts <out dir> [slug ...]');
mkdirSync(out, { recursive: true });

type Cam = { from: [number, number, number]; to: [number, number, number]; fov: number };

/** Where on this camera's floor the masks cover between a fifth and four fifths of her. */
function spot(cam: Cam, cover: Float32Array, floor: readonly Rect[], standable: (x: number, z: number) => boolean) {
  let best: { x: number; z: number; part: number } | undefined;
  for (const r of floor) {
    for (let x = r.x0 + 200; x < r.x1; x += 340) {
      for (let z = r.z0 + 200; z < r.z1; z += 340) {
        if (!standable(x, z)) continue;
        const feet = project(cam, [x, 0, z]);
        const head = project(cam, [x, -HEIGHT, z]);
        if (!feet || !head || feet.x < 20 || feet.x > 300 || head.y < 4 || feet.y > 236) continue;
        let covered = 0;
        let all = 0;
        for (let y = Math.ceil(head.y); y < feet.y; y += 2) {
          const i = y * FRAME_W + Math.round(feet.x);
          all++;
          if (cover[i]! < feet.z - 150) covered++;
        }
        const part = all ? covered / all : 0;
        if (part < 0.2 || part > 0.8) continue;
        // Most covered, then nearest the middle of the screen.
        const score = part - Math.abs(feet.x - 160) / 1000;
        if (!best || score > best.part) best = { x, z, part: score };
      }
    }
  }
  return best;
}

const session = await open(Number(process.env.PORT ?? 7880), '--mode REB --god --boot rebecca');
const link = session.link;
const found: { slug: string; cam: number; file?: string; note: string }[] = [];
try {
  await link.waitFor((s) => s.play, 'gameplay', 180_000);
  await settle(link);
  for (const spec of dayRooms.filter((r) => !only.length || only.includes(r.slug))) {
    const renders = path.join(dayDir, spec.slug, 'renders');
    const json = JSON.parse(readFileSync(path.join(renders, 'room.json'), 'utf8'));
    const depths = json.cameras.map((_: unknown, i: number) => {
      const f = path.join(renders, `cam${i}.depth.png`);
      return existsSync(f) ? readDepth(f) : undefined;
    });
    const floors = spec.cameraFloor === 'auto' ? autoFloors({ ...json, walls: [...json.walls, ...(json.voids ?? [])] }, depths) : spec.cameraFloor;
    const standable = standableIn(json);
    await link.room(spec.stage, spec.room);
    await settle(link);
    for (const [i, cam] of (json.cameras as Cam[]).entries()) {
      const zall = path.join(renders, `cam${i}.zall.png`);
      if (!existsSync(zall)) continue;
      const floor = ([] as Rect[]).concat(floors[i] ?? []);
      const cover = occluders(cam, readDepth(zall), floor, standable);
      const at = spot(cam, cover, floor, standable);
      if (!at) {
        found.push({ slug: spec.slug, cam: i, note: 'no spot where she is partly behind something' });
        continue;
      }
      // Facing the camera, so the picture shows her front.
      const angle = Math.round(((Math.atan2(-(cam.from[2] - at.z), cam.from[0] - at.x) / (2 * Math.PI)) * 4096 + 4096) % 4096);
      await link.place(Math.round(at.x), Math.round(at.z), angle);
      const s = await link.frames(20);
      const name = `${spec.slug}-cam${i}`;
      await snapshot(link, out, name);
      found.push({ slug: spec.slug, cam: i, file: `${name}.png`, note: `${Math.round(at.part * 100)}% of her behind the mask; the game shows camera ${s.camera}` });
      console.log(`${name}: at (${Math.round(at.x)}, ${Math.round(at.z)}), camera ${s.camera}`);
    }
  }
} finally {
  session.end();
}
writeFileSync(
  path.join(out, 'index.html'),
  `<!doctype html><meta charset="utf-8"><title>Rebecca's day: behind things, in the game</title>
<script src="/research/rebecca-day/nav.js" defer></script>
<style>body{background:#121110;color:#ddd6c8;font:15px/1.5 system-ui,sans-serif;max-width:1400px;margin:2em auto;padding:0 1em}
.grid{display:flex;flex-wrap:wrap;gap:12px}figure{margin:0;width:400px}img{width:400px;image-rendering:pixelated}figcaption{color:#8b8478;font-size:.85em}</style>
<h1>Behind things, in the game</h1>
<p>For each camera, Rebecca stood where the masks should cover part of her: some of her hidden behind the thing in front, some showing. If she is drawn over it instead, that camera's mask is wrong.</p>
<div class="grid">${found.map((f) => (f.file ? `<figure><img src="${f.file}" alt=""><figcaption>${f.slug} camera ${f.cam}: ${f.note}</figcaption></figure>` : `<figure><figcaption>${f.slug} camera ${f.cam}: ${f.note}</figcaption></figure>`)).join('')}</div>`,
);
console.log(`${path.join(out, 'index.html')}: ${found.filter((f) => f.file).length} pictures`);
