// A page of every room's foreground masks, to judge them room by room: each
// camera's background with what will be drawn over Rebecca tinted red, worked
// out the way the build works it out (room.ts: the scene's tagged objects and
// occluders.ts), and whether the camera's masks fit the engine's texture.
//
//   node tools/rebecca/day/masks-page.ts <out dir> [slug ...]
//
// Reads each room's renders (cam<N>.png, .depth.png, .zall.png). Writes
// <out dir>/index.html and a PNG per camera.
import { existsSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { readPng, writePng } from '../../harness/image.ts';
import { buildMasks } from '../masks.ts';
import { occluders, standableIn } from '../occluders.ts';
import { readDepth } from './floors.ts';
import { roomZones } from './camera-zones.ts';
import { dayRooms } from './rooms.ts';
import { look } from './look.ts';

const here = path.dirname(fileURLToPath(import.meta.url));
const [out, ...only] = process.argv.slice(2);
if (!out) throw new Error('usage: masks-page.ts <out dir> [slug ...]');
mkdirSync(out, { recursive: true });

interface Shot { file: string; front: number; tagged: number; fit: string }
const rooms: { slug: string; shots: Shot[]; missing: boolean }[] = [];
for (const spec of dayRooms.filter((r) => !only.length || only.includes(r.slug))) {
  const renders = path.join(here, spec.slug, 'renders');
  const json = JSON.parse(readFileSync(path.join(renders, 'room.json'), 'utf8'));
  const depths = json.cameras.map((_: unknown, i: number) => {
    const f = path.join(renders, `cam${i}.depth.png`);
    return existsSync(f) ? readDepth(f) : undefined;
  });
  const zones = roomZones({ ...json, walls: [...json.walls, ...(json.voids ?? [])] }, depths, spec.cameraFloor === 'auto' ? undefined : spec.cameraFloor);
  const standable = standableIn(json);
  const shots: Shot[] = [];
  let missing = false;
  json.cameras.forEach((c: { from: [number, number, number]; to: [number, number, number]; fov: number }, i: number) => {
    const zall = path.join(renders, `cam${i}.zall.png`);
    if (!existsSync(zall)) {
      missing = true;
      return;
    }
    const background = look(readPng(path.join(renders, `cam${i}.png`)));
    const found = occluders(c, readDepth(zall), [json.bounds], (x, z) => standable(x, z) && zones.holds(i, x, z));
    const tagged = depths[i] as Float32Array | undefined;
    const depth = found.map((d, k) => Math.min(d, tagged ? tagged[k]! : Infinity));
    let fit: string;
    try {
      fit = `${buildMasks(background, depth).sprites.length} sprites`;
    } catch (err) {
      fit = `does not fit: ${(err as Error).message}`;
    }
    const rgb = Uint8Array.from(background.rgb);
    let front = 0;
    let wasTagged = 0;
    for (let k = 0; k < depth.length; k++) {
      if (tagged && Number.isFinite(tagged[k]!)) wasTagged++;
      if (!Number.isFinite(depth[k]!)) continue;
      front++;
      rgb[k * 3] = Math.min(255, rgb[k * 3]! * 0.5 + 128);
      rgb[k * 3 + 1] = rgb[k * 3 + 1]! * 0.5;
      rgb[k * 3 + 2] = rgb[k * 3 + 2]! * 0.5;
    }
    const file = `${spec.slug}-cam${i}.png`;
    writePng(path.join(out, file), { width: background.width, height: background.height, rgb });
    shots.push({ file, front, tagged: wasTagged, fit });
  });
  rooms.push({ slug: spec.slug, shots, missing });
  console.log(`${spec.slug}: ${shots.map((s) => s.fit).join(', ')}${missing ? ' (some cameras have no zall render)' : ''}`);
}

const card = (s: Shot) =>
  `<figure><img src="${s.file}" alt=""><figcaption>${s.file.replace(/\.png$/, '')}: ${s.front} px in front of her (tagged by hand: ${s.tagged}); ${s.fit.startsWith('does not') ? `<b class="bad">${s.fit}</b>` : s.fit}</figcaption></figure>`;
writeFileSync(
  path.join(out, 'index.html'),
  `<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Rebecca's day: what she walks behind</title>
<script src="/research/rebecca-day/nav.js" defer></script>
<style>body{background:#121110;color:#ddd6c8;font:15px/1.5 system-ui,sans-serif;max-width:1400px;margin:2em auto;padding:0 1em}
h2{margin:1.6em 0 .4em;font-size:1.15em}p{max-width:52em}.grid{display:flex;flex-wrap:wrap;gap:12px}
figure{margin:0;width:320px}img{width:320px;image-rendering:pixelated}figcaption{color:#8b8478;font-size:.85em}.bad{color:#e66}</style>
<h1>What she walks behind</h1>
<p>Every camera of her day, with what the game will draw over Rebecca tinted red. Nobody marks these by hand any more: the build takes every surface the room's render saw (cam&lt;N&gt;.zall.png) and keeps the parts that are nearer the camera than somewhere she can stand on that camera's floor, and higher than 25 cm (occluders.ts). A post, a truck, a doorframe or a hut's corner is red where she can walk behind it and nowhere else. Red where she should not be hidden, or a thing she walks behind with no red on it, is what to point out.</p>
${rooms.map((r) => `<h2 id="${r.slug}">${r.slug}${r.missing ? ' <span class="bad">(not all cameras rendered yet)</span>' : ''}</h2><div class="grid">${r.shots.map(card).join('')}</div>`).join('\n')}
`,
);
console.log(`${path.join(out, 'index.html')}: ${rooms.length} rooms`);
