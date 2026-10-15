// The animation page plays each frame for as many ticks as the game holds it.
import assert from 'node:assert/strict';
import { existsSync, readFileSync } from 'node:fs';
import path from 'node:path';
import { test } from 'node:test';
import { animationFrames } from './anims.ts';
import { readAnimations, readEmd, section } from './emd.ts';

const file = path.join(process.env.RE1_BASE ?? '/tmp/re1-pc', 'enemy', 'EM1022.EMD');
const skip = existsSync(file) ? false : `needs the player's enemy/EM1022.EMD in ${path.dirname(file)}`;

test("Barry's idle, a delay-2 loop, plays each frame for two ticks", { skip }, () => {
  const emd = new Uint8Array(readFileSync(file));
  const idle = readAnimations(section(readEmd(emd), 'edd'))[42]!;
  assert.ok(idle.every((f) => (f.flags & 0xff) === 2), 'every idle frame has delay 2');
  const shown = animationFrames(emd).animations[42]!;
  assert.equal(shown.length, idle.length * 2);
  assert.deepEqual(shown[0], shown[1]);
  assert.notDeepEqual(shown[1], shown[2]);
});
