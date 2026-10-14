// Read and write RE1's .EMD character models, the files LoadEntityEMD
// (0x00462370, src/game/EntityModelLoader.cpp) loads for every enemy and
// cutscene character.
//
// A model is a run of sections and a directory of five 32-bit offsets in its
// last 20 bytes. LoadEntityEMD reads the directory at (size & ~3) - 0x14:
//   [0] a second skeleton, used by the monsters (0 for the people, whose
//       models start with the EMR; a monster's starts with a section no
//       entry names)
//   [1] skeleton and keyframes (EMR); 0, it starts the file (animHeader)
//   [2] animation list (EDD) (animBase)
//   [3] mesh, a PlayStation TMD (modelLoadBuffer, ProcessTmdTextures)
//   [4] texture, an 8 bpp 256x256 TIM with one 256-colour palette row per
//       128-pixel half of the sheet
// This module keeps every section as bytes, so a model written back unchanged
// is the same file, and parses the parts it needs to draw and repaint one.
//
// EMR (read by Entity_SetJoints and UpdateEntityAnimation, PlayerAnimations.cpp):
//   u16 armature offset, u16 keyframe offset, u16 joint count, u16 keyframe size
//   joint count x (s16 x, y, z): each joint's offset from its parent
//   at the armature offset, per joint: u8 child count, pad, u16 offset of its
//   list of u8 child indices (offsets from the armature)
//   keyframes: s16 root x, y, z, three s16 the engine moves the entity by, then
//   s16 x, y, z rotation per joint, in 4096ths of a turn
// EDD: per animation, u16 frame count and u16 offset of its frames; a frame is
//   a u32 whose low 16 bits index a keyframe.
// TMD: the standard PlayStation layout, one object per joint. Every polygon in
//   the people's models is mode 0x34, a lit, textured, smooth-shaded triangle:
//   u0 v0 CBA, u1 v1 TSB, u2 v2, then normal and vertex index pairs.

import type { Image } from '../../harness/image.ts';

const DIRECTORY = 5;
const SIDE = 256;
/** A TSB page is 64 VRAM halfwords: 128 texels at 8 bpp. */
const PAGE_TEXELS = 128;

export const SECTION = { second: 0, emr: 1, edd: 2, tmd: 3, tim: 4 } as const;
export type SectionName = keyof typeof SECTION;

export interface Part {
  /** The directory entries that point at this part; none for a monster's first section. */
  readonly names: readonly SectionName[];
  readonly bytes: Uint8Array;
}

export interface Emd {
  /** The file's sections in file order, from offset 0 to the directory. */
  readonly parts: readonly Part[];
  /** Directory words that are not offsets (a model with no second skeleton can hold anything there), by index. */
  readonly other: ReadonlyMap<number, number>;
}

const view = (b: Uint8Array) => new DataView(b.buffer, b.byteOffset, b.byteLength);
const names = Object.keys(SECTION).filter((k): k is SectionName => k in SECTION);

/** Split a model into its sections. */
export function readEmd(file: Uint8Array): Emd {
  if (file.length % 4 !== 0) throw new Error(`an EMD is whole words, got ${file.length} bytes`);
  const dirAt = file.length - DIRECTORY * 4;
  const v = view(file);
  const words = Array.from({ length: DIRECTORY }, (_, i) => v.getUint32(dirAt + i * 4, true));
  const other = new Map<number, number>();
  const starts = new Map<number, SectionName[]>();
  names.forEach((name) => {
    const at = words[SECTION[name]]!;
    if (at % 4 !== 0 || at >= dirAt || (name === 'second' && at === 0)) {
      if (name !== 'second') throw new Error(`the ${name} offset 0x${at.toString(16)} is not in the file`);
      other.set(SECTION[name], at);
      return;
    }
    starts.set(at, [...(starts.get(at) ?? []), name]);
  });
  // The monsters' first section is named by no entry: LoadEntityEMD keeps the
  // file's start for it (emdScratchPtr1) and the directory points past it.
  if (!starts.has(0)) starts.set(0, []);
  const order = [...starts.keys()].sort((a, b) => a - b);
  const parts = order.map((at, i) => ({ names: starts.get(at)!, bytes: file.slice(at, order[i + 1] ?? dirAt) }));
  return { parts, other };
}

/** Lay the sections out again and write the directory. */
export function writeEmd(emd: Emd): Uint8Array {
  const size = emd.parts.reduce((n, p) => n + p.bytes.length, 0);
  if (emd.parts.some((p) => p.bytes.length % 4 !== 0)) throw new Error('every section must be whole words');
  const out = new Uint8Array(size + DIRECTORY * 4);
  const v = view(out);
  let at = 0;
  for (const p of emd.parts) {
    out.set(p.bytes, at);
    for (const name of p.names) v.setUint32(size + SECTION[name] * 4, at, true);
    at += p.bytes.length;
  }
  for (const [i, word] of emd.other) v.setUint32(size + i * 4, word, true);
  return out;
}

export function section(emd: Emd, name: SectionName): Uint8Array {
  const part = emd.parts.find((p) => p.names.includes(name));
  if (!part) throw new Error(`the model has no ${name} section`);
  return part.bytes;
}

/** The same model with one section's bytes replaced. */
export function withSection(emd: Emd, name: SectionName, bytes: Uint8Array): Emd {
  if (!emd.parts.some((p) => p.names.includes(name))) throw new Error(`the model has no ${name} section`);
  return { ...emd, parts: emd.parts.map((p) => (p.names.includes(name) ? { ...p, bytes } : p)) };
}

// ---------------------------------------------------------------------------
// Skeleton and animations

export type Vec3 = readonly [number, number, number];

export interface Skeleton {
  /** Each joint's offset from its parent, in game units (Y points down). */
  readonly offsets: readonly Vec3[];
  readonly children: readonly (readonly number[])[];
  /** Each joint's parent; -1 for the root. */
  readonly parents: readonly number[];
  readonly keyframeAt: number;
  readonly keyframeSize: number;
  readonly keyframes: number;
}

export function readSkeleton(emr: Uint8Array): Skeleton {
  const v = view(emr);
  const armature = v.getUint16(0, true);
  const keyframeAt = v.getUint16(2, true);
  const joints = v.getUint16(4, true);
  const keyframeSize = v.getUint16(6, true);
  const offsets = Array.from({ length: joints }, (_, j): Vec3 => {
    const at = 8 + j * 6;
    return [v.getInt16(at, true), v.getInt16(at + 2, true), v.getInt16(at + 4, true)];
  });
  const children = Array.from({ length: joints }, (_, j) => {
    const count = emr[armature + j * 4]!;
    const list = armature + v.getUint16(armature + j * 4 + 2, true);
    return Array.from(emr.subarray(list, list + count));
  });
  const parents = Array.from({ length: joints }, (_, j) => children.findIndex((c) => c.includes(j)));
  return { offsets, children, parents, keyframeAt, keyframeSize, keyframes: Math.floor((emr.length - keyframeAt) / keyframeSize) };
}

export interface Frame {
  /** The keyframe this frame shows. */
  readonly keyframe: number;
  /** The frame word's high 16 bits, which the animation code reads as flags. */
  readonly flags: number;
}

/** Every animation in the list, as its frames. */
export function readAnimations(edd: Uint8Array): Frame[][] {
  const v = view(edd);
  const count = v.getUint16(2, true) / 4;
  return Array.from({ length: count }, (_, a) => {
    const frames = v.getUint16(a * 4, true);
    const at = v.getUint16(a * 4 + 2, true);
    return Array.from({ length: frames }, (_, f) => ({ keyframe: v.getUint16(at + f * 4, true), flags: v.getUint16(at + f * 4 + 2, true) }));
  });
}

export interface Keyframe {
  /** Where the root joint sits, in game units. */
  readonly root: Vec3;
  /** Each joint's rotation in 4096ths of a turn. */
  readonly rotations: readonly Vec3[];
}

export function readKeyframe(emr: Uint8Array, skeleton: Skeleton, index: number): Keyframe {
  const v = view(emr);
  const at = skeleton.keyframeAt + index * skeleton.keyframeSize;
  const s = (k: number) => v.getInt16(at + k * 2, true);
  return {
    root: [s(0), s(1), s(2)],
    rotations: skeleton.offsets.map((_, j): Vec3 => [s(6 + j * 3), s(7 + j * 3), s(8 + j * 3)]),
  };
}

/** The skeleton standing as modelled: no joint turned, the root at its own offset. */
export function restKeyframe(skeleton: Skeleton): Keyframe {
  return { root: skeleton.offsets[0]!, rotations: skeleton.offsets.map((): Vec3 => [0, 0, 0]) };
}

/** A rotation and a translation: world = rotation * local + translation. */
export interface Transform {
  /** Row-major 3x3. */
  readonly m: readonly number[];
  readonly t: Vec3;
}

/**
 * RotMatrix (src/game/GteMatrix.cpp) as floats: it hands GteRotationMatrixCalc
 * (-x, y, -z) and that builds Rx * Ry * Rz.
 */
export function rotMatrix([x, y, z]: Vec3): number[] {
  const a = (n: number) => (n * Math.PI * 2) / 4096;
  const [sx, cx] = [Math.sin(a(-x)), Math.cos(a(-x))];
  const [sy, cy] = [Math.sin(a(y)), Math.cos(a(y))];
  const [sz, cz] = [Math.sin(a(-z)), Math.cos(a(-z))];
  return [
    cz * cy, -cy * sz, sy,
    sx * sy * cz + cx * sz, cx * cz - sx * sz * sy, -sx * cy,
    sx * sz - cx * sy * cz, sz * sy * cx + sx * cz, cx * cy,
  ];
}

const mul = (a: readonly number[], b: readonly number[]) =>
  Array.from({ length: 9 }, (_, i) => [0, 1, 2].reduce((sum, k) => sum + a[Math.floor(i / 3) * 3 + k]! * b[k * 3 + (i % 3)]!, 0));
export const apply = (m: readonly number[], [x, y, z]: Vec3): Vec3 => [
  m[0]! * x + m[1]! * y + m[2]! * z,
  m[3]! * x + m[4]! * y + m[5]! * z,
  m[6]! * x + m[7]! * y + m[8]! * z,
];
const add = (a: Vec3, b: Vec3): Vec3 => [a[0] + b[0], a[1] + b[1], a[2] + b[2]];

/**
 * Each joint's place in the model's space for one keyframe, the way
 * EntityComputeJointWorldMatrices walks the armature from joint 0.
 */
export function pose(skeleton: Skeleton, key: Keyframe): Transform[] {
  const out: Transform[] = [];
  const walk = (j: number, parent: Transform | null) => {
    const r = rotMatrix(key.rotations[j]!);
    const t = parent ? add(apply(parent.m, skeleton.offsets[j]!), parent.t) : key.root;
    const here = { m: parent ? mul(parent.m, r) : r, t };
    out[j] = here;
    for (const c of skeleton.children[j]!) walk(c, here);
  };
  walk(0, null);
  return out;
}

// ---------------------------------------------------------------------------
// Mesh

export interface Triangle {
  /** Offset of the polygon's header word in the TMD section. */
  readonly at: number;
  readonly vertices: readonly [number, number, number];
  readonly normals: readonly [number, number, number];
  /** Texel coordinates on the whole 256x256 sheet: the TSB's page adds 128 to u. */
  readonly uv: readonly (readonly [number, number])[];
  /** Palette row: 0 or 1, from the CBA. */
  readonly row: number;
}

export interface MeshObject {
  readonly vertices: readonly Vec3[];
  readonly normals: readonly Vec3[];
  readonly triangles: readonly Triangle[];
}

/** The TMD's objects: one per joint, its vertices in that joint's space. */
export function readMesh(tmd: Uint8Array): MeshObject[] {
  const v = view(tmd);
  const objects = v.getUint32(8, true);
  const base = 12;
  const vecs = (at: number, n: number) =>
    Array.from({ length: n }, (_, i): Vec3 => [v.getInt16(at + i * 8, true), v.getInt16(at + i * 8 + 2, true), v.getInt16(at + i * 8 + 4, true)]);
  return Array.from({ length: objects }, (_, o) => {
    const e = base + o * 28;
    const vertices = vecs(base + v.getUint32(e, true), v.getUint32(e + 4, true));
    const normals = vecs(base + v.getUint32(e + 8, true), v.getUint32(e + 12, true));
    let p = base + v.getUint32(e + 16, true);
    const triangles: Triangle[] = [];
    for (let k = v.getUint32(e + 20, true); k > 0; k--) {
      const ilen = tmd[p + 1]!;
      const mode = tmd[p + 3]!;
      if (mode !== 0x34) throw new Error(`object ${o}: polygon mode 0x${mode.toString(16)} at 0x${p.toString(16)}, only 0x34 is read`);
      const tsb = v.getUint16(p + 10, true);
      const page = (tsb & 0xf) * PAGE_TEXELS;
      const uv = [0, 1, 2].map((c) => [tmd[p + 4 + c * 4]! + page, tmd[p + 5 + c * 4]!] as const);
      const idx = (k2: number) => v.getUint16(p + 16 + k2 * 2, true);
      triangles.push({ at: p, uv, row: (v.getUint16(p + 6, true) >> 6) & 1, normals: [idx(0), idx(2), idx(4)], vertices: [idx(1), idx(3), idx(5)] });
      p += 4 + ilen * 4;
    }
    return { vertices, normals, triangles };
  });
}

// ---------------------------------------------------------------------------
// Texture

export interface Texture {
  /** One palette of 256 PlayStation 15-bit colours per row; bit 15 is the semi-transparency bit. */
  readonly palettes: readonly Uint16Array[];
  /** 256x256 palette indices, row-major. */
  readonly pixels: Uint8Array;
}

interface TimLayout {
  readonly clut: number;
  readonly rows: number;
  readonly pixels: number;
}

function timLayout(tim: Uint8Array): TimLayout {
  const v = view(tim);
  if (v.getUint32(0, true) !== 0x10 || v.getUint32(4, true) !== 9) throw new Error('the texture is not an 8 bpp TIM with a palette');
  const clutBytes = v.getUint32(8, true);
  const rows = v.getUint16(18, true);
  const pixels = 8 + clutBytes;
  if (v.getUint16(16, true) !== 256 || v.getUint16(pixels + 8, true) !== SIDE / 2 || v.getUint16(pixels + 10, true) !== SIDE) {
    throw new Error('the texture is not 256x256 with 256-colour palettes');
  }
  return { clut: 20, rows, pixels: pixels + 12 };
}

export function readTexture(tim: Uint8Array): Texture {
  const l = timLayout(tim);
  const v = view(tim);
  const palettes = Array.from({ length: l.rows }, (_, r) => Uint16Array.from({ length: 256 }, (_, i) => v.getUint16(l.clut + (r * 256 + i) * 2, true)));
  return { palettes, pixels: tim.slice(l.pixels, l.pixels + SIDE * SIDE) };
}

/** The TIM with its palettes and pixels replaced; its headers and size stay as they were. */
export function writeTexture(tim: Uint8Array, texture: Texture): Uint8Array {
  const l = timLayout(tim);
  if (texture.palettes.length !== l.rows || texture.pixels.length !== SIDE * SIDE) throw new Error('the texture does not fit the TIM');
  const out = tim.slice();
  const v = view(out);
  texture.palettes.forEach((p, r) => p.forEach((c, i) => v.setUint16(l.clut + (r * 256 + i) * 2, c, true)));
  out.set(texture.pixels, l.pixels);
  return out;
}

/** The palette row the sheet's texel at x uses: each 128-texel half has its own. */
export const rowAt = (x: number) => (x < PAGE_TEXELS ? 0 : 1);

/** 8-bit RGB of a 15-bit colour. Colour 0 is the transparent one; it comes out black. */
export function rgb(c: number): [number, number, number] {
  const e = (n: number) => Math.floor(((n & 31) * 255 + 15) / 31);
  return [e(c), e(c >> 5), e(c >> 10)];
}

/** The sheet as an RGB image, each half through its own palette row. */
export function textureImage(t: Texture): Image {
  const out = new Uint8Array(SIDE * SIDE * 3);
  for (let i = 0; i < SIDE * SIDE; i++) out.set(rgb(t.palettes[Math.min(rowAt(i % SIDE), t.palettes.length - 1)]![t.pixels[i]!]!), i * 3);
  return { width: SIDE, height: SIDE, rgb: out };
}
