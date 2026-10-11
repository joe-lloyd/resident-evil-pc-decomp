// Boot a REB game straight into a room, optionally stand Rebecca somewhere,
// and take a few screenshots a moment apart. Development aid for looking at
// new rooms, not a test.
//
//   node tools/harness/look.ts <stage>:<room> <name> [x,z[,angle]] [shots] [gap frames]
import { open } from './lab.ts';
import { settle } from './flows.ts';
import { snapshot } from './snapshot.ts';

const [where, name, at, shots = '3', gap = '7'] = process.argv.slice(2);
if (!where || !name) throw new Error('usage: look.ts <stage>:<room> <name> [x,z[,angle]] [shots] [gap frames]');
const [stage, room] = where.split(':').map(Number) as [number, number];
const session = await open(Number(process.env.PORT ?? 7802), `--mode REB --boot rebecca:${stage}:${room}`);
try {
  let s = await settle(session.link);
  if (at) {
    const [x, z, angle] = at.split(',').map(Number) as [number, number, number | undefined];
    await session.link.place(x, z, angle);
    s = await settle(session.link);
  }
  console.log(`room ${s.stage}:${s.room} camera ${s.camera} at (${s.player.x}, ${s.player.z})`);
  for (let i = 0; i < Number(shots); i++) {
    if (i) await session.link.frames(Number(gap));
    console.log(await snapshot(session.link, process.env.OUT ?? '/tmp/rae-look', `${name}-${i}`));
  }
} finally {
  session.end();
}
