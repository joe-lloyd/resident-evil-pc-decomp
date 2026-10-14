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
// RE1_WEAR          strength of kit.wear's texture on every surface, 0 for none (default: 1.3)
// RE1_BLENDER_SLOTS renders at once across every caller on this machine (default: 3)
//
// One GPU serves every caller. Seventeen renders at once filled its 24 GB and
// froze them all, so each render takes one of a few slots (a folder under
// /tmp/reb-render-slots holding its pid) and waits while they are all taken.
// A render that runs past its time limit is stopped on the Blender machine.
import { execFileSync } from 'node:child_process';
import { mkdirSync, readFileSync, rmSync, statSync, writeFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
const host = process.env.RE1_BLENDER_HOST ?? 'jellybingus';
const exe = process.env.RE1_BLENDER_EXE ?? 'C:\\Program Files\\Blender Foundation\\Blender 5.1\\blender.exe';
const root = process.env.RE1_BLENDER_DIR ?? 'C:\\Users\\joell\\Documents\\Blender\\re1-rebecca\\day';

const ssh = (cmd: string) =>
  execFileSync('ssh', ['-o', 'BatchMode=yes', host, cmd], { encoding: 'utf8', maxBuffer: 64 << 20, stdio: ['ignore', 'pipe', 'pipe'] });
const remote = (p: string) => p.replace(/\\/g, '/');

const slotsDir = '/tmp/reb-render-slots';
const slots = Number(process.env.RE1_BLENDER_SLOTS ?? 3);
const alive = (pid: number) => {
  try {
    process.kill(pid, 0);
    return true;
  } catch {
    return false;
  }
};
const sleep = (ms: number) => Atomics.wait(new Int32Array(new SharedArrayBuffer(4)), 0, 0, ms);

/** Wait for a free render slot and take it; returns the slot's folder. */
function takeSlot(slug: string): string {
  mkdirSync(slotsDir, { recursive: true });
  for (let waited = false; ; waited = true) {
    for (let i = 0; i < slots; i++) {
      const slot = path.join(slotsDir, String(i));
      try {
        mkdirSync(slot);
      } catch {
        // Taken: free it if whoever holds it has gone. A slot just taken may
        // not have its pid written yet; give it a minute.
        let pid = 0;
        try {
          pid = Number(readFileSync(path.join(slot, 'pid'), 'utf8').split('\n')[0]);
        } catch {
          if (Date.now() - statSync(slot).mtimeMs < 60_000) continue;
        }
        if (pid && alive(pid)) continue;
        rmSync(slot, { recursive: true, force: true });
        continue;
      }
      writeFileSync(path.join(slot, 'pid'), `${process.pid}\n${slug}\n`);
      return slot;
    }
    if (!waited) console.log(`${slug}: waiting for a render slot`);
    sleep(5000);
  }
}

/** Stop the Blender rendering this scene on the Blender machine. */
function stopRemote(scene: string) {
  const ps = `Get-CimInstance Win32_Process | Where-Object { $_.Name -eq 'blender.exe' -and $_.CommandLine -like '*${scene}*' } | ForEach-Object { Stop-Process -Force -Id $_.ProcessId }`;
  ssh(`powershell -NoProfile -EncodedCommand ${Buffer.from(ps, 'utf16le').toString('base64')}`);
}

const args = process.argv.slice(2);
const preview = args.includes('--preview');
const slugs = args.filter((a) => a !== '--preview');
if (!slugs.length) throw new Error('usage: render.ts [--preview] <slug> [<slug> ...]');
for (const slug of slugs) {
  const dir = path.join(here, slug);
  const work = `${root}\\${slug}`;
  const out = `${work}\\renders`;
  ssh(`powershell -NoProfile -Command "if (Test-Path '${out}') { Remove-Item -Recurse -Force '${out}' }; New-Item -ItemType Directory -Force '${out}' | Out-Null"`);
  execFileSync('scp', ['-q', '-o', 'BatchMode=yes', path.join(dir, 'scene.py'), path.join(here, '..', 'blender', 'reb.py'), path.join(here, '..', 'blender', 'kit.py'), `${host}:${remote(work)}/`]);
  const slot = takeSlot(slug);
  const started = Date.now();
  const limit = (preview ? 5 : 30) * 60_000;
  try {
    execFileSync('ssh', ['-o', 'BatchMode=yes', host, `cmd /c "set RE1_OUT=${out}&& set RE1_PREVIEW=${preview ? '1' : ''}&& set RE1_WEAR=${process.env.RE1_WEAR ?? '1.3'}&& "${exe}" -b --factory-startup --python-exit-code 1 --python "${work}\\scene.py" > "${work}\\render.log" 2>&1"`], { stdio: 'ignore', timeout: limit });
  } catch (err) {
    const late = Date.now() - started >= limit;
    if (late) stopRemote(`${work}\\scene.py`);
    const log = ssh(`powershell -NoProfile -Command "Get-Content -Tail 40 '${work}\\render.log'"`);
    throw new Error(`${slug}: Blender ${late ? `ran past ${limit / 60_000} minutes and was stopped` : 'failed'}\n${log}`, { cause: err });
  } finally {
    rmSync(slot, { recursive: true, force: true });
  }
  const local = preview ? path.join('/tmp/reb-preview', slug) : path.join(dir, 'renders');
  rmSync(local, { recursive: true, force: true });
  mkdirSync(local, { recursive: true });
  execFileSync('scp', ['-q', '-r', '-o', 'BatchMode=yes', `${host}:${remote(out)}/*`, `${local}/`]);
  console.log(`${slug}: rendered in ${Math.round((Date.now() - started) / 1000)} s`);
}
