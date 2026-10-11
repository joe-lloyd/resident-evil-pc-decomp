// Render a day room's Blender scene on the Blender machine and bring the
// renders back into day/<slug>/renders/.
//
//   node tools/rebecca/day/render.ts [--preview] <slug> [<slug> ...]
//
// --preview renders the backgrounds alone at low quality into
// /tmp/reb-preview/<slug>/, to judge a scene without replacing its renders.
//
// RE1_BLENDER_HOST  ssh host with Blender and an NVIDIA GPU (default: jellybingus)
// RE1_BLENDER_EXE   Blender on that host (default: Blender 5.1's install path)
// RE1_BLENDER_DIR   working folder there (default: Documents\Blender\re1-rebecca\day)
import { execFileSync } from 'node:child_process';
import { mkdirSync, rmSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
const host = process.env.RE1_BLENDER_HOST ?? 'jellybingus';
const exe = process.env.RE1_BLENDER_EXE ?? 'C:\\Program Files\\Blender Foundation\\Blender 5.1\\blender.exe';
const root = process.env.RE1_BLENDER_DIR ?? 'C:\\Users\\joell\\Documents\\Blender\\re1-rebecca\\day';

const ssh = (cmd: string) =>
  execFileSync('ssh', ['-o', 'BatchMode=yes', host, cmd], { encoding: 'utf8', maxBuffer: 64 << 20, stdio: ['ignore', 'pipe', 'pipe'] });
const remote = (p: string) => p.replace(/\\/g, '/');

const args = process.argv.slice(2);
const preview = args.includes('--preview');
const slugs = args.filter((a) => a !== '--preview');
if (!slugs.length) throw new Error('usage: render.ts [--preview] <slug> [<slug> ...]');
for (const slug of slugs) {
  const dir = path.join(here, slug);
  const work = `${root}\\${slug}`;
  const out = `${work}\\renders`;
  ssh(`powershell -NoProfile -Command "if (Test-Path '${out}') { Remove-Item -Recurse -Force '${out}' }; New-Item -ItemType Directory -Force '${out}' | Out-Null"`);
  execFileSync('scp', ['-q', '-o', 'BatchMode=yes', path.join(dir, 'scene.py'), path.join(here, '..', 'blender', 'reb.py'), `${host}:${remote(work)}/`]);
  const started = Date.now();
  try {
    ssh(`cmd /c "set RE1_OUT=${out}&& set RE1_PREVIEW=${preview ? '1' : ''}&& "${exe}" -b --factory-startup --python-exit-code 1 --python "${work}\\scene.py" > "${work}\\render.log" 2>&1"`);
  } catch (err) {
    const log = ssh(`powershell -NoProfile -Command "Get-Content -Tail 40 '${work}\\render.log'"`);
    throw new Error(`${slug}: Blender failed\n${log}`, { cause: err });
  }
  const local = preview ? path.join('/tmp/reb-preview', slug) : path.join(dir, 'renders');
  rmSync(local, { recursive: true, force: true });
  mkdirSync(local, { recursive: true });
  execFileSync('scp', ['-q', '-r', '-o', 'BatchMode=yes', `${host}:${remote(out)}/*`, `${local}/`]);
  console.log(`${slug}: rendered in ${Math.round((Date.now() - started) / 1000)} s`);
}
