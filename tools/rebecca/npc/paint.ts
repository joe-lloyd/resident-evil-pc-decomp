// Paint a skin in a model's own texture layout from what each texel covers on
// the body: for every texel a triangle samples, the body part (TMD object) it
// is on, the point it covers with the model standing at rest, and the
// surface's facing there. A skin is a function of those, so it is drawn from
// the model's shape and none of the game's pixels.
import type { Image } from '../../harness/image.ts';
import { apply, pose, readEmd, readMesh, readSkeleton, restKeyframe, section, type Vec3 } from './emd.ts';

const SIDE = 256;

export interface Texel {
  /** The TMD object, which for a person is the joint: 0 chest, 1 head, 2 hips, 3-5 left leg, 6-8 right leg, 9-11 left arm, 12-14 right arm. */
  readonly part: number;
  /** The point it covers with the model standing at rest, in body axes (`toBody`), game units. */
  readonly at: Vec3;
  /** The point in the part's own space (game axes). */
  readonly local: Vec3;
  /** Unit surface normal at rest, in body axes like `at`. */
  readonly normal: Vec3;
}

/**
 * Body axes for painting, from the game's (x forward, y down, z to the
 * character's left): x to the character's right, y up from the floor, z
 * forward.
 */
const toBody = ([x, y, z]: Vec3): Vec3 => [-z, -y, x];

/** What every sampled texel of the model covers; null where no triangle samples. */
export function surfaceMap(file: Uint8Array): (Texel | null)[] {
  const emd = readEmd(file);
  const skeleton = readSkeleton(section(emd, 'emr'));
  const joints = pose(skeleton, restKeyframe(skeleton));
  const mesh = readMesh(section(emd, 'tmd'));
  const out: (Texel | null)[] = new Array(SIDE * SIDE).fill(null);
  mesh.forEach((o, part) => {
    const joint = joints[part];
    if (!joint) return;
    const world = (v: Vec3): Vec3 => {
      const r = apply(joint.m, v);
      return [r[0] + joint.t[0], r[1] + joint.t[1], r[2] + joint.t[2]];
    };
    for (const t of o.triangles) {
      const p = t.vertices.map((i) => o.vertices[i]!);
      const n = t.normals.map((i) => o.normals[i]!);
      const uv = t.uv;
      const [a, b, c] = uv;
      const area = (b![0] - a![0]) * (c![1] - a![1]) - (c![0] - a![0]) * (b![1] - a![1]);
      if (Math.abs(area) < 1e-6) continue;
      const lo = [Math.floor(Math.min(a![0], b![0], c![0])), Math.floor(Math.min(a![1], b![1], c![1]))];
      const hi = [Math.ceil(Math.max(a![0], b![0], c![0])), Math.ceil(Math.max(a![1], b![1], c![1]))];
      for (let y = lo[1]!; y <= Math.min(hi[1]!, SIDE - 1); y++)
        for (let x = lo[0]!; x <= Math.min(hi[0]!, SIDE - 1); x++) {
          // Barycentric weights of the texel's centre, clamped so the texels a
          // triangle's edges touch take the edge's value.
          const px = x + 0.5;
          const py = y + 0.5;
          const e1 = ((px - a![0]) * (c![1] - a![1]) - (c![0] - a![0]) * (py - a![1])) / area;
          const e2 = ((b![0] - a![0]) * (py - a![1]) - (px - a![0]) * (b![1] - a![1])) / area;
          const e0 = 1 - e1 - e2;
          const inside = Math.min(e0, e1, e2) >= -0.5 / Math.sqrt(Math.abs(area));
          if (!inside) continue;
          const [w0, w1, w2] = [Math.max(0, e0), Math.max(0, e1), Math.max(0, e2)];
          const sum = w0 + w1 + w2;
          const axis = (q: readonly Vec3[], k: number) => (w0 * q[0]![k]! + w1 * q[1]![k]! + w2 * q[2]![k]!) / sum;
          const mix = (q: readonly Vec3[]): Vec3 => [axis(q, 0), axis(q, 1), axis(q, 2)];
          const local = mix(p);
          const nl = mix(n);
          const nw = apply(joint.m, nl);
          const len = Math.hypot(...nw) || 1;
          const strict = Math.min(e0, e1, e2) >= 0;
          const i = y * SIDE + x;
          // A texel inside a triangle beats one only near an edge.
          if (out[i] && !strict) continue;
          out[i] = { part, local, at: toBody(world(local)), normal: toBody([nw[0] / len, nw[1] / len, nw[2] / len]) };
        }
    }
  });
  return out;
}

export type Rgb = readonly [number, number, number];

/** A skin from a function of what each texel covers. Texels no triangle samples are grown out from their neighbours. */
export function paint(map: readonly (Texel | null)[], colour: (t: Texel) => Rgb): Image {
  const rgb = new Uint8Array(SIDE * SIDE * 3);
  const done = new Uint8Array(SIDE * SIDE);
  map.forEach((t, i) => {
    if (!t) return;
    rgb.set(colour(t).map((v) => Math.max(0, Math.min(255, Math.round(v)))), i * 3);
    done[i] = 1;
  });
  // Grow painted texels into the empty space a few times so filtering and
  // rounding at island edges never reach an unpainted texel.
  for (let pass = 0; pass < 4; pass++) {
    const next = done.slice();
    for (let y = 0; y < SIDE; y++)
      for (let x = 0; x < SIDE; x++) {
        const i = y * SIDE + x;
        if (done[i]) continue;
        const from = [i - 1, i + 1, i - SIDE, i + SIDE].find((j, k) => j >= 0 && j < SIDE * SIDE && done[j] && (k > 1 || Math.floor(j / SIDE) === y));
        if (from === undefined) continue;
        rgb.copyWithin(i * 3, from * 3, from * 3 + 3);
        next[i] = 1;
      }
    done.set(next);
  }
  return { width: SIDE, height: SIDE, rgb };
}

/** The placeholder: one flat colour per body part, lit from above, with a fine check so the texel grid shows. */
export function placeholder(t: Texel): Rgb {
  const colours: Rgb[] = [
    [70, 110, 170], [220, 180, 150], [60, 130, 90], [170, 90, 60], [190, 120, 70], [120, 80, 50],
    [90, 60, 140], [130, 90, 170], [80, 50, 110], [200, 160, 60], [220, 200, 90], [240, 220, 160],
    [60, 150, 150], [90, 190, 190], [160, 230, 230],
  ];
  const base = colours[t.part % colours.length]!;
  const light = 0.75 + 0.25 * t.normal[1];
  const check = (Math.floor(t.at[0] / 60) + Math.floor(t.at[1] / 60) + Math.floor(t.at[2] / 60)) % 2 ? 1 : 0.88;
  return [base[0] * light * check, base[1] * light * check, base[2] * light * check];
}
