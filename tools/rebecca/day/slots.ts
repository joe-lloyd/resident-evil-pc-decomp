// One GPU serves every caller on this machine: Blender renders for the
// rooms, the characters, anything. Each Blender run takes one of a few slots
// (a folder under /tmp/reb-render-slots holding its pid) and waits while
// they are all taken. Seventeen renders at once filled the GPU's 24 GB and
// froze them all.
//
//   import { withSlot } from '.../day/slots.ts';
//   withSlot('my-job', () => runBlender());
//
//   node tools/rebecca/day/slots.ts <label> -- <command> [args...]   (from a shell)
//
// RE1_BLENDER_SLOTS sets how many run at once (default: 3).
import { execFileSync } from 'node:child_process';
import { mkdirSync, readFileSync, rmSync, statSync, writeFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

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
export function takeSlot(slug: string): string {
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

/** Run `job` holding a slot, and free it however `job` ends. */
export function withSlot<T>(label: string, job: () => T): T {
  const slot = takeSlot(label);
  try {
    return job();
  } finally {
    rmSync(slot, { recursive: true, force: true });
  }
}

if (process.argv[1] === fileURLToPath(import.meta.url)) {
  const [label, dash, cmd, ...rest] = process.argv.slice(2);
  if (!label || dash !== '--' || !cmd) throw new Error('usage: slots.ts <label> -- <command> [args...]');
  withSlot(label, () => execFileSync(cmd, rest, { stdio: 'inherit' }));
}
