// Write a model out for tools/rebecca/npc/view.py: its skeleton, its mesh with
// the texture's coordinates, the joints' places for a few keyframes, and the
// texture sheet as a PNG.
//
//   node tools/rebecca/npc/export.ts <model.emd> <out dir> [anim:frame ...] [--skin skin.png]
//
// Writes <out dir>/model.json and texture.png. Each anim:frame names a pose
// from the model's animation list (rest is always there). With --skin the
// texture is our skin, fitted to the model's palettes first, so the render
// shows what the game will.
import { mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import path from 'node:path';
import { encodePng, readPng, type Image } from '../../harness/image.ts';
import { pose, readAnimations, readEmd, readKeyframe, readMesh, readSkeleton, readTexture, restKeyframe, section, textureImage, type Keyframe } from './emd.ts';
import { fitSkin } from './skin.ts';

export function exportModel(file: Uint8Array, poses: readonly string[], skin?: Image) {
  const emd = readEmd(file);
  const emr = section(emd, 'emr');
  const skeleton = readSkeleton(emr);
  const animations = readAnimations(section(emd, 'edd'));
  const mesh = readMesh(section(emd, 'tmd'));
  const keyframes: [string, Keyframe][] = [['rest', restKeyframe(skeleton)]];
  for (const name of poses) {
    const [a, f] = name.split(':').map(Number);
    const frame = animations[a!]?.[f!];
    if (!frame) throw new Error(`no frame ${name}: the model has ${animations.length} animations`);
    keyframes.push([name, readKeyframe(emr, skeleton, frame.keyframe)]);
  }
  const texture = readTexture(section(emd, 'tim'));
  const sheet = textureImage(skin ? fitSkin(texture, skin) : texture);
  const model = {
    joints: skeleton.offsets.map((offset, j) => ({ parent: skeleton.parents[j], offset })),
    // A model can carry more objects than joints (the women's models have a
    // 16th); only objects with a joint are drawn on the skeleton.
    objects: mesh.map((o, j) => ({
      joint: j < skeleton.offsets.length ? j : null,
      vertices: o.vertices,
      normals: o.normals,
      triangles: o.triangles.map((t) => ({ v: t.vertices, n: t.normals, uv: t.uv, row: t.row })),
    })),
    poses: Object.fromEntries(keyframes.map(([name, key]) => [name, pose(skeleton, key)])),
  };
  return { model, png: encodePng(sheet) };
}

if (import.meta.url === `file://${process.argv[1]}`) {
  const args = process.argv.slice(2);
  const skinAt = args.indexOf('--skin');
  const skin = skinAt >= 0 ? readPng(args.splice(skinAt, 2)[1]!) : undefined;
  const [file, out, ...poses] = args;
  if (!file || !out) throw new Error('usage: export.ts <model.emd> <out dir> [anim:frame ...] [--skin skin.png]');
  const { model, png } = exportModel(new Uint8Array(readFileSync(file)), poses, skin);
  mkdirSync(out, { recursive: true });
  writeFileSync(path.join(out, 'model.json'), JSON.stringify(model));
  writeFileSync(path.join(out, 'texture.png'), png);
  console.log(`${out}: ${model.joints.length} joints, ${model.objects.length} objects, poses ${Object.keys(model.poses).join(' ')}`);
}
