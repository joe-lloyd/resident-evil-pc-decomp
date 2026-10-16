// Draw every animation of a model as a moving skeleton, from the front and the
// side, on one HTML page: the cheap way to see which is an idle, a walk or a
// death before anything is rendered.
//
//   node tools/rebecca/npc/anims.ts <out.html> <name>=<model.emd> [...]
//
// The joints are posed from each frame's keyframe with pose() in emd.ts, the
// way the game poses them. Animation numbers are the model's own (animationId).
import { readFileSync, writeFileSync } from 'node:fs';
import { pose, readAnimations, readEmd, readKeyframe, readSkeleton, section } from './emd.ts';

export function animationFrames(file: Uint8Array) {
  const emd = readEmd(file);
  const emr = section(emd, 'emr');
  const skeleton = readSkeleton(emr);
  return {
    parents: skeleton.parents,
    // One entry per tick: Joint_move holds a frame for its flags' low byte in
    // ticks (at least one), so a delay-2 idle plays at half the frame rate.
    animations: readAnimations(section(emd, 'edd')).map((frames) =>
      frames.flatMap((f) => {
        const joints = pose(skeleton, readKeyframe(emr, skeleton, f.keyframe)).flatMap((j) => j.t.map(Math.round));
        return Array.from({ length: Math.max(1, f.flags & 0xff) }, () => joints);
      }),
    ),
  };
}

function page(models: { name: string; parents: readonly number[]; animations: number[][][] }[]): string {
  return `<!doctype html><html lang="en"><head><meta charset="utf-8"><title>Character animations</title>
<style>body{background:#121110;color:#ddd6c8;font:14px/1.4 system-ui,sans-serif;margin:1.5em}
.grid{display:flex;flex-wrap:wrap;gap:6px}figure{margin:0;background:#1a1816;border:1px solid #2a2724}
figcaption{padding:2px 6px;color:#8b8478}canvas{display:block}</style></head><body>
<p>Each animation's skeleton, front view on the left and side view on the right, at the game's 30 ticks a second, each frame held as long as the game holds it. The number is the animation's index in the model.</p>
${models.map((m, i) => `<h2>${m.name}</h2><div class="grid" id="m${i}"></div>`).join('\n')}
<script>
const models = ${JSON.stringify(models)};
const W = 90, H = 130, S = 0.042;
const draws = [];
models.forEach((m, i) => {
  const grid = document.getElementById('m' + i);
  m.animations.forEach((frames, a) => {
    const fig = document.createElement('figure');
    const c = document.createElement('canvas');
    c.width = W * 2; c.height = H;
    const cap = document.createElement('figcaption');
    cap.textContent = a + ' (' + frames.length + ' frames)';
    fig.append(c, cap); grid.append(fig);
    draws.push((t) => {
      const g = c.getContext('2d');
      g.clearRect(0, 0, c.width, c.height);
      const f = frames[t % frames.length];
      if (!f) return;
      // Front: the model faces +x, so z runs across. Side: x runs across. Y points down.
      for (const [view, ox] of [[2, W / 2], [0, W + W / 2]]) {
        g.strokeStyle = '#c8963c'; g.lineWidth = 2;
        m.parents.forEach((p, j) => {
          if (p < 0) return;
          g.beginPath();
          g.moveTo(ox + f[p * 3 + view] * S, H - 8 + f[p * 3 + 1] * S);
          g.lineTo(ox + f[j * 3 + view] * S, H - 8 + f[j * 3 + 1] * S);
          g.stroke();
        });
        g.fillStyle = '#ddd6c8';
        g.beginPath(); g.arc(ox + f[1 * 3 + view] * S, H - 8 + f[1 * 3 + 1] * S, 4, 0, 7); g.fill();
      }
    });
  });
});
let t = 0;
setInterval(() => { t++; draws.forEach((d) => d(t)); }, 1000 / 30);
</script></body></html>`;
}

if (import.meta.url === `file://${process.argv[1]}`) {
  const [out, ...specs] = process.argv.slice(2);
  if (!out || !specs.length) throw new Error('usage: anims.ts <out.html> <name>=<model.emd> [...]');
  const models = specs.map((s) => {
    const [name, file] = s.split('=');
    return { name: name!, ...animationFrames(new Uint8Array(readFileSync(file!))) };
  });
  writeFileSync(out, page(models));
  console.log(`${out}: ${models.map((m) => `${m.name} ${m.animations.length} animations`).join(', ')}`);
}
