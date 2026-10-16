// Render a day room's Blender scene on the Blender machine and bring the
// renders back into day/<slug>/renders/.
//
//   node tools/rebecca/day/render.ts [--preview | --records] [--states] <slug> [<slug> ...]
//
// --preview renders the backgrounds alone at low quality into
// /tmp/reb-preview/<slug>/, to judge a scene without replacing its renders.
// --records renders nothing: it writes the scene's room.json alone (doors,
// checks, items) into day/<slug>/renders/, for a change to what the scene
// records rather than to its pictures.
// --states renders the scene's changes of state alone (kit.Room.state), over
// the backgrounds already in day/<slug>/renders/: the scene must otherwise be
// as it was when they were rendered. With --preview they go to the preview
// folder instead, at low quality.
//
// RE1_BLENDER_HOST  ssh host with Blender and an NVIDIA GPU (default: jellybingus)
// RE1_BLENDER_EXE   Blender on that host (default: Blender 5.1's install path)
// RE1_BLENDER_DIR   working folder there (default: Documents\Blender\re1-rebecca\day)
// RE1_WEAR          strength of kit.wear's texture on every surface, 0 for none (default: 1.3)
// RE1_FILL          an indoor room's fill light, watts per square metre of floor, 0 for none (default: kit's)
// RE1_BLENDER_SLOTS renders at once across every caller on this machine (default: 3)
//
// One GPU serves every caller, so each render takes one of the shared slots
// (slots.ts) and waits while they are all taken. A render that runs past its
// time limit is stopped on the Blender machine.
import { execFileSync } from 'node:child_process';
import { mkdirSync, readdirSync, rmSync } from 'node:fs';
import { takeSlot } from './slots.ts';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
const host = process.env.RE1_BLENDER_HOST ?? 'jellybingus';
const exe = process.env.RE1_BLENDER_EXE ?? 'C:\\Program Files\\Blender Foundation\\Blender 5.1\\blender.exe';
const root = process.env.RE1_BLENDER_DIR ?? 'C:\\Users\\joell\\Documents\\Blender\\re1-rebecca\\day';

const ssh = (cmd: string) =>
  execFileSync('ssh', ['-o', 'BatchMode=yes', host, cmd], { encoding: 'utf8', maxBuffer: 64 << 20, stdio: ['ignore', 'pipe', 'pipe'] });
const remote = (p: string) => p.replace(/\\/g, '/');

/** Stop the Blender rendering this scene on the Blender machine. */
function stopRemote(scene: string) {
  const ps = `Get-CimInstance Win32_Process | Where-Object { $_.Name -eq 'blender.exe' -and $_.CommandLine -like '*${scene}*' } | ForEach-Object { Stop-Process -Force -Id $_.ProcessId }`;
  ssh(`powershell -NoProfile -EncodedCommand ${Buffer.from(ps, 'utf16le').toString('base64')}`);
}

const args = process.argv.slice(2);
const preview = args.includes('--preview');
const records = args.includes('--records');
const states = args.includes('--states');
const slugs = args.filter((a) => !['--preview', '--records', '--states'].includes(a));
if (!slugs.length) throw new Error('usage: render.ts [--preview | --records] [--states] <slug> [<slug> ...]');
for (const slug of slugs) {
  const dir = path.join(here, slug);
  const work = `${root}\\${slug}`;
  const out = `${work}\\renders`;
  ssh(`powershell -NoProfile -Command "if (Test-Path '${out}') { Remove-Item -Recurse -Force '${out}' }; New-Item -ItemType Directory -Force '${out}' | Out-Null"`);
  execFileSync('scp', ['-q', '-o', 'BatchMode=yes', path.join(dir, 'scene.py'), path.join(here, '..', 'blender', 'reb.py'), path.join(here, '..', 'blender', 'kit.py'), `${host}:${remote(work)}/`]);
  const slot = takeSlot(slug);
  const started = Date.now();
  const limit = (records || (preview && !states) ? 5 : 30) * 60_000;
  try {
    execFileSync('ssh', ['-o', 'BatchMode=yes', host, `cmd /c "set RE1_OUT=${out}&& set RE1_PREVIEW=${preview ? '1' : ''}&& set RE1_RECORDS=${records ? '1' : ''}&& set RE1_STATES=${states ? '1' : ''}&& set RE1_WEAR=${process.env.RE1_WEAR ?? '1.3'}&& set RE1_FILL=${process.env.RE1_FILL ?? ''}&& "${exe}" -b --factory-startup --python-exit-code 1 --python "${work}\\scene.py" > "${work}\\render.log" 2>&1"`], { stdio: 'ignore', timeout: limit });
  } catch (err) {
    const late = Date.now() - started >= limit;
    if (late) stopRemote(`${work}\\scene.py`);
    const log = ssh(`powershell -NoProfile -Command "Get-Content -Tail 40 '${work}\\render.log'"`);
    throw new Error(`${slug}: Blender ${late ? `ran past ${limit / 60_000} minutes and was stopped` : 'failed'}\n${log}`, { cause: err });
  } finally {
    rmSync(slot, { recursive: true, force: true });
  }
  if (records) {
    execFileSync('scp', ['-q', '-o', 'BatchMode=yes', `${host}:${remote(out)}/room.json`, path.join(dir, 'renders', 'room.json')]);
    console.log(`${slug}: records written`);
    continue;
  }
  const local = preview ? path.join('/tmp/reb-preview', slug) : path.join(dir, 'renders');
  if (states && !preview) {
    // Keep the backgrounds; replace every state's pictures.
    for (const f of readdirSync(local)) if (/^cam\d+\.[sm]-/.test(f)) rmSync(path.join(local, f));
  } else {
    rmSync(local, { recursive: true, force: true });
    mkdirSync(local, { recursive: true });
  }
  execFileSync('scp', ['-q', '-r', '-o', 'BatchMode=yes', `${host}:${remote(out)}/*`, `${local}/`]);
  console.log(`${slug}: rendered in ${Math.round((Date.now() - started) / 1000)} s`);
}
