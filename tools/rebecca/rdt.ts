// Compose a room file (RDT) for a room the game never had: a donor room's
// sound bank, effects and models, with our own cameras, masks, collision,
// zones, scripts and messages.
//
// The donor is cut into sections at every offset anything points at: the 19
// header pointers, the camera mask pointers, the {TMD, TIM} model pairs and the
// two effect tables. The sections the new room needs are copied in their
// order, ours are added, snd.vb goes last (the engine loads models over it,
// docs/RDT_FILE_FORMAT.md), and every pointer is rewritten through the map
// from old offsets to new. Pointers are plain file offsets; 0 is null.
//
// What points where is in docs/RDT_FILE_FORMAT.md ("Pointer relocation
// passes"): the header slots, the camera records, the model pairs and the
// effect tables (8 dwords each, the slot pointing at the last one). The event
// table's offsets are relative to itself, so it moves as one piece.

export const HEADER_SIZE = 0x94;
export const CAMERA_SIZE = 0x2c;
const SLOTS_AT = 0x48;

/** The 19 header pointer slots, in order (RDT+0x48 + 4 * slot). */
export const SLOT = {
  switchZones: 0,
  collision: 1,
  objectModels: 2,
  itemModels: 3,
  walkZones: 4,
  footsteps: 5,
  init: 6,
  main: 7,
  events: 8,
  playerAnimHeader: 9,
  playerAnimBase: 10,
  messages: 11,
  itemIcons: 12,
  effectIds: 13,
  effectTable: 14,
  effectSpriteTable: 15,
  soundAttributes: 16,
  soundHeader: 17,
  soundBody: 18,
} as const;
export type Slot = (typeof SLOT)[keyof typeof SLOT];

/** Header bytes the composer sets. */
const HDR_SPRITES = 0x00;
const HDR_CAMERAS = 0x01;
const HDR_OMODELS = 0x02;
const HDR_ITEMS = 0x03;
const HDR_AMBIENT = 0x06;
const HDR_LIGHTS = 0x0c;
const LIGHT_SIZE = 0x14;

/** The effect tables: 8 dwords, the slot pointing at the last one, 0xFFFFFFFF for none. */
const EFFECT_TABLE_DWORDS = 8;
const NO_EFFECT = 0xffffffff;

export interface Vec3 {
  readonly x: number;
  readonly y: number;
  readonly z: number;
}

export interface CameraRecord {
  readonly from: Vec3;
  readonly to: Vec3;
  readonly fov: number;
  /** The camera's mask/sprite block; undefined for none (a 4-byte zero block). */
  readonly maskBlock?: Uint8Array;
}

export interface PointLight {
  readonly x: number;
  readonly y: number;
  readonly z: number;
  readonly rgb: readonly [number, number, number];
  readonly radius: number;
}

export interface RoomPlan {
  readonly cameras: readonly CameraRecord[];
  /** Twelve-bit PS1 channels, fed to setBackColor. */
  readonly ambient: readonly [number, number, number];
  readonly lights: readonly [PointLight, PointLight, PointLight];
  /** New contents for these slots. Slots not given keep the donor's section. */
  readonly sections: Partial<Record<Slot, Uint8Array>>;
  /** Keep the donor's object and item models (and icons); otherwise the room has none. */
  readonly keepModels?: boolean;
  /**
   * The room's item models, in slot order (item_aot_set's model index), from
   * other rooms (model()). Replaces the donor's models.
   */
  readonly itemModels?: readonly Model[];
  /** The room's object models, in slot order (obj's model index), from other rooms (model()). */
  readonly objectModels?: readonly Model[];
}

/** One model: the TMD (mesh) and TIM (texture) a room's model pair points at. */
export interface Model {
  readonly tmd?: Uint8Array;
  readonly tim?: Uint8Array;
}

/** Item or object model `index` of room `rdt`, copied out of it. */
export function model(rdt: Uint8Array, kind: 'item' | 'object', index: number): Model {
  const v = new DataView(rdt.buffer, rdt.byteOffset, rdt.byteLength);
  const count = rdt[kind === 'item' ? HDR_ITEMS : HDR_OMODELS]!;
  if (index >= count) throw new Error(`the room has ${count} ${kind} models, not ${index + 1}`);
  const table = u32(v, SLOTS_AT + 4 * (kind === 'item' ? SLOT.itemModels : SLOT.objectModels));
  const sections = cut(rdt);
  const grab = (p: number) => {
    if (!p) return undefined;
    const s = holder(sections, p)!;
    return rdt.slice(p, s.end);
  };
  return { tmd: grab(u32(v, table + 8 * index)), tim: grab(u32(v, table + 8 * index + 4)) };
}

/**
 * A copy of a model's mesh scaled by `s` about its own origin, as when RE1's
 * item box lid goes on a smaller box: every vertex of every object in the TMD.
 */
export function scaleModel(m: Model, s: number): Model {
  if (!m.tmd || s === 1) return m;
  // A copy with its own buffer: a Node Buffer's slice is a view into a shared pool.
  const tmd = new Uint8Array(m.tmd);
  const v = new DataView(tmd.buffer);
  // Header: id, flags (0: offsets relative to the object table), object count; then 28-byte objects.
  if (v.getUint32(4, true) !== 0) throw new Error('the TMD has absolute offsets');
  const objects = 12;
  for (let o = 0; o < v.getUint32(8, true); o++) {
    const top = v.getUint32(objects + 28 * o, true);
    const count = v.getUint32(objects + 28 * o + 4, true);
    for (let i = 0; i < count * 4; i++) {
      // SVECTOR: x, y, z and a pad word, which stays.
      if (i % 4 === 3) continue;
      const at = objects + top + 2 * i;
      v.setInt16(at, Math.round(v.getInt16(at, true) * s), true);
    }
  }
  return { tmd, tim: m.tim };
}

const u32 = (v: DataView, at: number) => v.getUint32(at, true);
const align4 = (n: number) => (n + 3) & ~3;

interface Section {
  readonly start: number;
  readonly end: number;
}

/** Every offset the donor's pointers name, and the sections they cut it into. */
function cut(donor: Uint8Array): Section[] {
  const v = new DataView(donor.buffer, donor.byteOffset, donor.byteLength);
  const starts = new Set<number>([0, HEADER_SIZE]);
  const add = (p: number) => {
    if (p !== 0 && p !== NO_EFFECT && p < donor.length) starts.add(p);
  };
  // The effect table slots point at a table's last dword; the table is cut at its first.
  for (let s = 0; s < 19; s++) if (s !== SLOT.effectTable && s !== SLOT.effectSpriteTable) add(u32(v, SLOTS_AT + 4 * s));
  const cameras = donor[HDR_CAMERAS]!;
  for (let i = 0; i < cameras; i++) {
    add(u32(v, HEADER_SIZE + i * CAMERA_SIZE));
    add(u32(v, HEADER_SIZE + i * CAMERA_SIZE + 4));
  }
  starts.add(HEADER_SIZE + cameras * CAMERA_SIZE);
  for (const [slot, count] of [[SLOT.objectModels, donor[HDR_OMODELS]!], [SLOT.itemModels, donor[HDR_ITEMS]!]] as const) {
    const table = u32(v, SLOTS_AT + 4 * slot);
    if (table) for (let i = 0; i < count * 2; i++) add(u32(v, table + 4 * i));
  }
  for (const slot of [SLOT.effectTable, SLOT.effectSpriteTable]) {
    const last = u32(v, SLOTS_AT + 4 * slot);
    if (!last) continue;
    // The table itself starts 7 dwords before the slot's target.
    add(last - 4 * (EFFECT_TABLE_DWORDS - 1));
    for (let i = 0; i < EFFECT_TABLE_DWORDS; i++) add(u32(v, last - 4 * i));
  }
  const sorted = [...starts].sort((a, b) => a - b);
  return sorted.map((start, i) => ({ start, end: sorted[i + 1] ?? donor.length }));
}

/** The section of `sections` that holds offset `p`. */
function holder(sections: readonly Section[], p: number): Section | undefined {
  return sections.find((s) => p >= s.start && p < s.end);
}

/**
 * The room file. `donor` is not modified. The init and main scripts and the
 * messages are usually written afterwards by `rae asm` and `rae msg-set`,
 * which put theirs where snd.vb starts and move snd.vb behind them.
 */
export function composeRoom(donor: Uint8Array, plan: RoomPlan): Uint8Array {
  const dv = new DataView(donor.buffer, donor.byteOffset, donor.byteLength);
  const slot = (s: Slot) => u32(dv, SLOTS_AT + 4 * s);
  const sections = cut(donor);
  const sectionAt = (p: number) => {
    const s = holder(sections, p);
    if (!s) throw new Error(`donor offset 0x${p.toString(16)} is in no section`);
    return s;
  };

  // Donor sections to keep: the ones these slots start (and what they own).
  const keepSlots: Slot[] = [SLOT.events, SLOT.messages, SLOT.playerAnimHeader, SLOT.playerAnimBase, SLOT.effectIds, SLOT.effectTable, SLOT.effectSpriteTable, SLOT.soundAttributes, SLOT.soundHeader];
  if (plan.keepModels) keepSlots.push(SLOT.objectModels, SLOT.itemModels, SLOT.itemIcons);
  const kept = new Set<Section>();
  for (const s of keepSlots) if (!(s in plan.sections) && slot(s)) kept.add(sectionAt(slot(s)));
  // A model table and the TMD and TIM sections its pairs name.
  const keepTable = (s: Slot, pairs: number) => {
    const at = slot(s);
    if (!at) return;
    for (let i = 0; i < pairs * 2; i++) {
      const p = u32(dv, at + 4 * i);
      if (p && p !== NO_EFFECT) kept.add(sectionAt(p));
    }
  };
  if (plan.keepModels) {
    keepTable(SLOT.objectModels, donor[HDR_OMODELS]!);
    keepTable(SLOT.itemModels, donor[HDR_ITEMS]!);
  }
  // The effect tables and the effect data they name.
  for (const s of [SLOT.effectTable, SLOT.effectSpriteTable]) {
    const last = slot(s);
    if (!last) continue;
    for (let i = 0; i < EFFECT_TABLE_DWORDS; i++) {
      const p = u32(dv, last - 4 * i);
      if (p && p !== NO_EFFECT) kept.add(sectionAt(p));
    }
  }
  const vbAt = slot(SLOT.soundBody);
  const vb = vbAt ? sectionAt(vbAt) : undefined;
  if (vb) kept.delete(vb);

  // Layout: header, cameras, kept donor sections in donor order, our sections,
  // the camera mask blocks, then snd.vb.
  const parts: { bytes: Uint8Array; at: number }[] = [];
  let end = HEADER_SIZE + plan.cameras.length * CAMERA_SIZE;
  const place = (bytes: Uint8Array) => {
    end = align4(end);
    const at = end;
    parts.push({ bytes, at });
    end += bytes.length;
    return at;
  };
  const moved = new Map<Section, number>();
  for (const s of [...kept].sort((a, b) => a.start - b.start)) moved.set(s, place(donor.subarray(s.start, s.end)));
  const ours = new Map<Slot, number>();
  for (const [s, bytes] of Object.entries(plan.sections) as [string, Uint8Array][]) ours.set(Number(s) as Slot, place(bytes));
  // Models from other rooms: each TMD and TIM, then the table of pairs.
  const placeModels = (list: readonly Model[] | undefined) => {
    const pairs = (list ?? []).map((m) => ({ tmd: m.tmd ? place(m.tmd) : 0, tim: m.tim ? place(m.tim) : 0 }));
    return { pairs, table: list ? place(new Uint8Array(Math.max(4, pairs.length * 8))) : 0 };
  };
  const items = placeModels(plan.itemModels);
  const objects = placeModels(plan.objectModels);
  const masks = plan.cameras.map((c) => place(c.maskBlock ?? new Uint8Array(4)));
  if (vb) moved.set(vb, place(donor.subarray(vb.start, vb.end)));

  const out = new Uint8Array(end);
  out.set(donor.subarray(0, HEADER_SIZE));
  for (const p of parts) out.set(p.bytes, p.at);
  const ov = new DataView(out.buffer);
  /** Where donor offset `p` went; 0 when its section was dropped. */
  const map = (p: number): number => {
    if (!p || p === NO_EFFECT) return p;
    const s = holder(sections, p);
    const at = s && moved.get(s);
    return at === undefined ? 0 : at + (p - s!.start);
  };

  // Header: counts, lights, then the pointer slots.
  out[HDR_SPRITES] = 0;
  out[HDR_CAMERAS] = plan.cameras.length;
  if (!plan.keepModels) {
    out[HDR_OMODELS] = 0;
    out[HDR_ITEMS] = 0;
  }
  plan.ambient.forEach((c, i) => ov.setInt16(HDR_AMBIENT + 2 * i, c, true));
  plan.lights.forEach((l, i) => {
    const at = HDR_LIGHTS + i * LIGHT_SIZE;
    ov.setInt32(at, l.x, true);
    ov.setInt32(at + 4, l.y, true);
    ov.setInt32(at + 8, l.z, true);
    l.rgb.forEach((c, j) => ov.setUint8(at + 12 + j, c));
    ov.setUint8(at + 15, 0);
    ov.setUint16(at + 16, 0, true); // type 0: a point light
    ov.setInt16(at + 18, l.radius, true);
  });
  for (let s = 0 as Slot; s < 19; s++) {
    const own = ours.get(s);
    ov.setUint32(SLOTS_AT + 4 * s, own ?? map(u32(dv, SLOTS_AT + 4 * s)), true);
  }
  if (plan.itemModels || plan.objectModels) {
    for (const [{ pairs, table }, count, s] of [[items, HDR_ITEMS, SLOT.itemModels], [objects, HDR_OMODELS, SLOT.objectModels]] as const) {
      out[count] = pairs.length;
      pairs.forEach((m, i) => {
        ov.setUint32(table + 8 * i, m.tmd, true);
        ov.setUint32(table + 8 * i + 4, m.tim, true);
      });
      ov.setUint32(SLOTS_AT + 4 * s, table, true);
    }
    // The icon tiles are a PS1 leftover nothing on PC reads (RDT_FILE_FORMAT.md).
    ov.setUint32(SLOTS_AT + 4 * SLOT.itemIcons, 0, true);
  }

  // Cameras.
  plan.cameras.forEach((c, i) => {
    const at = HEADER_SIZE + i * CAMERA_SIZE;
    ov.setUint32(at, masks[i]!, true);
    ov.setUint32(at + 4, 0, true); // no embedded mask TIM: the PC loads masks from objspr paks
    const vals = [c.from.x, c.from.y, c.from.z, c.to.x, c.to.y, c.to.z, 0, 0, c.fov];
    vals.forEach((n, j) => ov.setInt32(at + 8 + 4 * j, n, true));
  });

  // Tables inside kept sections.
  const remapTable = (s: Slot, dwords: number, fromLast: boolean) => {
    const target = u32(ov, SLOTS_AT + 4 * s);
    if (!target) return;
    const first = fromLast ? target - 4 * (dwords - 1) : target;
    for (let i = 0; i < dwords; i++) ov.setUint32(first + 4 * i, map(u32(ov, first + 4 * i)), true);
  };
  if (plan.keepModels) {
    remapTable(SLOT.objectModels, 2 * out[HDR_OMODELS]!, false);
    remapTable(SLOT.itemModels, 2 * out[HDR_ITEMS]!, false);
  }
  remapTable(SLOT.effectTable, EFFECT_TABLE_DWORDS, true);
  remapTable(SLOT.effectSpriteTable, EFFECT_TABLE_DWORDS, true);
  return out;
}
