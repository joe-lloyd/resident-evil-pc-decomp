// Render the save room's trapdoor (hatch.py) through the room's six cameras on
// the Blender machine, inside a render slot, into saveroom/renders/.
//
//   node tools/rebecca/saveroom/render.ts
//
// RE1_BLENDER_HOST, RE1_BLENDER_EXE and RE1_WEAR as for day/render.ts.
import { execFileSync } from 'node:child_process';
import { mkdirSync, rmSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { withSlot } from '../day/slots.ts';

const here = path.dirname(fileURLToPath(import.meta.url));
const host = process.env.RE1_BLENDER_HOST ?? 'jellybingus';
const exe = process.env.RE1_BLENDER_EXE ?? 'C:\\Program Files\\Blender Foundation\\Blender 5.1\\blender.exe';
const work = 'C:\\Users\\joell\\Documents\\Blender\\re1-rebecca\\saveroom';
const out = `${work}\\renders`;
const fwd = (p: string) => p.replace(/\\/g, '/');
const ssh = (cmd: string) => execFileSync('ssh', ['-o', 'BatchMode=yes', host, cmd], { stdio: 'ignore' });

ssh(`powershell -NoProfile -Command "if (Test-Path '${out}') { Remove-Item -Recurse -Force '${out}' }; New-Item -ItemType Directory -Force '${out}' | Out-Null"`);
execFileSync('scp', ['-q', '-o', 'BatchMode=yes', path.join(here, 'hatch.py'), path.join(here, '..', 'blender', 'reb.py'), path.join(here, '..', 'blender', 'kit.py'), `${host}:${fwd(work)}/`]);
withSlot('saveroom', () =>
  ssh(`cmd /c "set OUT=${out}&& set RE1_WEAR=${process.env.RE1_WEAR ?? '1.3'}&& "${exe}" -b --factory-startup --python-exit-code 1 --python "${work}\\hatch.py" > "${work}\\render.log" 2>&1"`),
);
const local = path.join(here, 'renders');
rmSync(local, { recursive: true, force: true });
mkdirSync(local, { recursive: true });
execFileSync('scp', ['-q', '-o', 'BatchMode=yes', `${host}:${fwd(out)}/*.png`, `${local}/`]);
console.log(`${local}: the trapdoor through six cameras`);
