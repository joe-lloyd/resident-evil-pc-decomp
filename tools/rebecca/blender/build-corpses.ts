// Build the dead (corpses.py) in Blender on the GPU machine, in one of the
// shared render slots: corpses.blend goes next to the rooms' work folders,
// where kit.body reads it, and the sheet of every corpse comes back to
// /tmp/reb-corpses.png for checking.
//
//   node tools/rebecca/blender/build-corpses.ts
//
// RE1_BLENDER_HOST, RE1_BLENDER_EXE and RE1_BLENDER_DIR as for day/render.ts.
import { execFileSync } from 'node:child_process';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { withSlot } from '../day/slots.ts';

const here = path.dirname(fileURLToPath(import.meta.url));
const host = process.env.RE1_BLENDER_HOST ?? 'jellybingus';
const exe = process.env.RE1_BLENDER_EXE ?? 'C:\\Program Files\\Blender Foundation\\Blender 5.1\\blender.exe';
const root = process.env.RE1_BLENDER_DIR ?? 'C:\\Users\\joell\\Documents\\Blender\\re1-rebecca\\day';
const work = `${root}\\corpses`;
const remote = (p: string) => p.replace(/\\/g, '/');
const ssh = (cmd: string) => execFileSync('ssh', ['-o', 'BatchMode=yes', host, cmd], { stdio: ['ignore', 'pipe', 'inherit'] });

ssh(`powershell -NoProfile -Command "New-Item -ItemType Directory -Force '${work}' | Out-Null"`);
execFileSync('scp', ['-q', '-o', 'BatchMode=yes', ...['corpses.py', 'kit.py', 'reb.py'].map((f) => path.join(here, f)), `${host}:${remote(work)}/`]);
try {
  // MPFB is one of the owner's add-ons, so no --factory-startup here.
  withSlot('corpses', () => ssh(`cmd /c "set RE1_OUT=${root}&& "${exe}" -b --python-exit-code 1 --python "${work}\\corpses.py" > "${work}\\build.log" 2>&1"`));
} catch (err) {
  execFileSync('ssh', ['-o', 'BatchMode=yes', host, `powershell -NoProfile -Command "Get-Content -Tail 40 '${work}\\build.log'"`], { stdio: 'inherit' });
  throw err;
}
execFileSync('scp', ['-q', '-o', 'BatchMode=yes', `${host}:${remote(root)}/corpses.png`, '/tmp/reb-corpses.png']);
console.log(`corpses.blend built in ${root}; the sheet is /tmp/reb-corpses.png`);
