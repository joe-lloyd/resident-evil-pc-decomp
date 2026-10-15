// Model her key items (models.py) in Blender on the GPU machine, in one of
// the shared render slots: their inventory icons into items/icons/, and the
// meshes and baked textures tmd.ts makes the game's models of into
// items/models/.
//
//   node tools/rebecca/items/render-items.ts [<step> ...]   (default: every item models.py has)
//
// RE1_BLENDER_HOST, RE1_BLENDER_EXE and RE1_BLENDER_DIR as for day/render.ts.
import { execFileSync } from 'node:child_process';
import { mkdirSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { withSlot } from '../day/slots.ts';

const here = path.dirname(fileURLToPath(import.meta.url));
const host = process.env.RE1_BLENDER_HOST ?? 'jellybingus';
const exe = process.env.RE1_BLENDER_EXE ?? 'C:\\Program Files\\Blender Foundation\\Blender 5.1\\blender.exe';
const work = `${process.env.RE1_BLENDER_DIR ?? 'C:\\Users\\joell\\Documents\\Blender\\re1-rebecca\\day'}\\items`;
const out = `${work}\\out`;
const only = process.argv.slice(2).join(',');
const remote = (p: string) => p.replace(/\\/g, '/');
const ssh = (cmd: string) => execFileSync('ssh', ['-o', 'BatchMode=yes', host, cmd], { stdio: ['ignore', 'pipe', 'inherit'] });

ssh(`powershell -NoProfile -Command "if (Test-Path '${out}') { Remove-Item -Recurse -Force '${out}' }; New-Item -ItemType Directory -Force '${out}' | Out-Null"`);
execFileSync('scp', ['-q', '-o', 'BatchMode=yes', path.join(here, 'models.py'), path.join(here, '..', 'blender', 'reb.py'), `${host}:${remote(work)}/`]);
try {
  withSlot('items', () =>
    ssh(`cmd /c "set RE1_OUT=${out}&& set RE1_ITEMS=${only}&& "${exe}" -b --factory-startup --python-exit-code 1 --python "${work}\\models.py" > "${work}\\render.log" 2>&1"`),
  );
} catch (err) {
  execFileSync('ssh', ['-o', 'BatchMode=yes', host, `powershell -NoProfile -Command "Get-Content -Tail 40 '${work}\\render.log'"`], { stdio: 'inherit' });
  throw err;
}
for (const dir of ['icons', 'models']) {
  mkdirSync(path.join(here, dir), { recursive: true });
  execFileSync('scp', ['-q', '-o', 'BatchMode=yes', `${host}:${remote(out)}/${dir}/*`, `${path.join(here, dir)}/`]);
}
console.log(`items modelled into ${here}/icons and ${here}/models`);
