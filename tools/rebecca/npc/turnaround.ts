// Turnaround renders of her day's people, as the game will have them: each
// model built from the player's own file with our skin (people.ts), exported,
// and rendered in Blender on jellybingus (view.py) inside a render slot, then
// fetched back.
//
//   node tools/rebecca/npc/turnaround.ts <out dir> [slug ...] [--poses rest,4:29] [--size 512] [--head]
//
// Reads the player's models from RE1_BASE (default /tmp/re1-pc)/enemy. Writes
// <out dir>/<slug>/<pose>-front.png, -side.png and -back.png, and the model's
// texture as texture.png. Blender's work folder is RE1_NPC_REMOTE (default
// C:\Users\joell\Documents\Blender\re1-npc).
import { execFileSync } from 'node:child_process';
import { mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { withSlot } from '../day/slots.ts';
import { exportModel } from './export.ts';
import { people, personModel } from './people.ts';

const here = path.dirname(fileURLToPath(import.meta.url));
const host = process.env.RE1_LAB_HOST ?? 'jellybingus';
const remote = process.env.RE1_NPC_REMOTE ?? 'C:\\Users\\joell\\Documents\\Blender\\re1-npc';
const blender = 'C:\\Program Files\\Blender Foundation\\Blender 5.1\\blender.exe';
const fwd = (p: string) => p.replace(/\\/g, '/');

const args = process.argv.slice(2);
const option = (name: string) => {
  const at = args.indexOf(name);
  return at < 0 ? undefined : args.splice(at, 2)[1];
};
const head = args.includes('--head');
const poses = (option('--poses') ?? 'rest').split(',');
const size = option('--size') ?? '512';
const [outDir, ...slugs] = args.filter((a) => a !== '--head');
if (!outDir) throw new Error('usage: turnaround.ts <out dir> [slug ...] [--poses rest,4:29] [--size 512] [--head]');
const enemy = path.join(process.env.RE1_BASE ?? '/tmp/re1-pc', 'enemy');

for (const person of people.filter((p) => !slugs.length || slugs.includes(p.slug))) {
  const local = path.join(outDir, person.slug);
  mkdirSync(local, { recursive: true });
  const model = personModel(new Uint8Array(readFileSync(path.join(enemy, person.model))), person);
  const { model: json, png } = exportModel(model, poses.filter((p) => p !== 'rest'));
  writeFileSync(path.join(local, 'model.json'), JSON.stringify(json));
  writeFileSync(path.join(local, 'texture.png'), png);

  const work = `${remote}\\${person.slug}`;
  // A fresh out folder, so no render from an earlier run comes back.
  execFileSync('ssh', ['-o', 'BatchMode=yes', host, `cmd /c (if exist "${work}\\out" rmdir /s /q "${work}\\out") & mkdir "${work}\\out"`]);
  execFileSync('scp', ['-q', path.join(local, 'model.json'), path.join(local, 'texture.png'), path.join(here, 'view.py'), `${host}:${fwd(work)}/`]);
  for (const pose of poses) {
    const flags = `${head ? '--head ' : ''}--size ${size}`;
    withSlot('npc', () =>
      execFileSync('ssh', ['-o', 'BatchMode=yes', host, `cmd /c ""${blender}" -b --factory-startup --python "${work}\\view.py" -- "${work}" "${work}\\out" ${pose} ${flags} > "${work}\\blender.log" 2>&1"`]),
    );
  }
  execFileSync('scp', ['-q', `${host}:${fwd(work)}/out/*.png`, `${local}/`]);
  console.log(`${local}: ${poses.join(', ')}`);
}
