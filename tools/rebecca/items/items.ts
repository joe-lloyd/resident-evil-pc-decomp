// Her key items. Each takes the place of an item of RE1's that her day never
// sees, and in her mode only it has her name and her description (RebItems.cpp,
// written by engine.ts). An item models.py makes has its own icon, its own
// model to examine and its own model lying in the room (tmd.ts); the rest,
// the keys, keep their donors': the pickup model is copied from a room of the
// player's game that holds the donor. The operator's key borrows a dormitory
// key's, since RE1 hands its Special Key over in a cutscene.
//
// Donors are chosen to have no behaviour of their own outside the mansion's
// room scripts: no combining (the herbs, the chemicals), no reading (the
// books), no pose when used (the cranks, but the winch crank wants it), and
// not the Sword Key, which her save room still holds. An item she uses at a
// spot (an item-use zone, flag bank 9, bit id - 27) must be 27 (0x1B) or
// more: the jerrycan and the diesel take the two emblems for that.

export interface KeyItem {
  /** The plan's step that gives it (plan/day.ts). */
  readonly step: string;
  /** RE1's item id it takes the place of. */
  readonly id: number;
  /** In capitals, as RE1's names are; the pickup message and the inventory show it. */
  readonly name: string;
  /** What she sees examining it: short lines, '\n' between them. */
  readonly description: string;
  /** Its pickup model. */
  readonly model: PickupModel;
}

/** A pickup model: the donor's, from a room of the player's game that holds it (and its slot there), or the item's own (models.py, tmd.ts). */
export type PickupModel = { readonly from: string; readonly index: number } | { readonly own: string };

export const sameModel = (a: PickupModel, b: PickupModel): boolean =>
  'own' in a ? 'own' in b && a.own === b.own : !('own' in b) && a.from === b.from && a.index === b.index;

export const KEY_ITEMS: readonly KeyItem[] = [
  { step: 'shed-key', id: 0x3d, name: 'SHED KEY', description: 'The key to the tool shed,\noff the ranger\'s board.' , model: { from: 'Stage1/ROOM1130.RDT', index: 0 } },
  { step: 'crank', id: 0x1e, name: 'WINCH CRANK', description: 'A crank handle for the\ntruck\'s winch.' , model: { from: 'Stage3/ROOM30A0.RDT', index: 1 } },
  { step: 'truck-keys', id: 0x39, name: 'RANGER KEYS', description: 'The ranger\'s key ring.\nHis truck, and the tower.' , model: { from: 'Stage4/ROOM4080.RDT', index: 0 } },
  { step: 'cutters', id: 0x1c, name: 'BOLT CUTTERS', description: 'Heavy bolt cutters from\nthe truck\'s toolbox.' , model: { own: 'cutters' } },
  { step: 'office-key', id: 0x3a, name: 'OFFICE KEY', description: 'A key on a tag marked\n"FOREMAN".' , model: { from: 'Stage4/ROOM4100.RDT', index: 4 } },
  { step: 'safe', id: 0x3b, name: 'WORKSHOP KEY', description: 'A brass key from the\nforeman\'s safe.' , model: { from: 'Stage4/ROOM4020.RDT', index: 0 } },
  { step: 'cog', id: 0x29, name: 'DRIVE COG', description: 'A spare drive cog for the\ngondola\'s bullwheel.' , model: { own: 'cog' } },
  { step: 'jerrycan', id: 0x1f, name: 'JERRYCAN', description: 'An empty jerrycan.' , model: { own: 'jerrycan' } },
  { step: 'fuel', id: 0x20, name: 'DIESEL', description: 'A jerrycan full of diesel.' , model: { own: 'fuel' } },
  { step: 'switch-key', id: 0x37, name: 'SWITCH KEY', description: 'A key tagged "SWITCH\nHOUSE".' , model: { from: 'Stage5/ROOM5130.RDT', index: 0 } },
  { step: 'quarry-key', id: 0x3c, name: 'QUARRY KEY', description: 'A key tagged "QUARRY\nOFFICE".' , model: { from: 'Stage5/ROOM5040.RDT', index: 0 } },
  { step: 'dynamite', id: 0x2a, name: 'DYNAMITE', description: 'Sticks of dynamite with a\nshort fuse.' , model: { own: 'dynamite' } },
  { step: 'op-key', id: 0x38, name: 'OPERATOR KEY', description: 'Hal\'s key to the gondola\'s\ncontrols.' , model: { from: 'Stage4/ROOM4080.RDT', index: 0 } },
  { step: 'fuses', id: 0x27, name: 'FUSES', description: 'Spare fuses for the\ngondola\'s board.' , model: { own: 'fuses' } },
  { step: 'crowbar', id: 0x2b, name: 'CROWBAR', description: 'A crowbar from Bravo\'s\nhelicopter.' , model: { own: 'crowbar' } },
  { step: 'gate-key', id: 0x34, name: 'GATE KEY', description: 'An old iron key to the\nestate\'s back gate.' , model: { from: 'Stage1/ROOM10C0.RDT', index: 0 } },
  { step: 'cellar-key', id: 0x35, name: 'CELLAR KEY', description: 'A key to the cellar doors.' , model: { from: 'Stage1/ROOM1050.RDT', index: 0 } },
];

/** Room-item flags (FG_ITEM) for the key items she picks up in the kit rooms: 160-179. */
export const KEY_ITEM_FLAGS = Array.from({ length: 20 }, (_, i) => 160 + i);

/** Where a kit room's scene says a key item lies (kit.Room.item): game units, y up negative. */
export interface ItemSpot {
  readonly step: string;
  readonly x: number;
  readonly y: number;
  readonly z: number;
}

const byStep = (step: string) => {
  const k = KEY_ITEMS.find((i) => i.step === step);
  if (!k) throw new Error(`no key item for step ${step}`);
  return k;
};

/** The pickup models a room's key items need, in the order its pickups name them. */
export function keyItemModels(spots: readonly ItemSpot[]): PickupModel[] {
  const out: PickupModel[] = [];
  for (const s of spots) {
    const m = byStep(s.step).model;
    if (!out.some((o) => sameModel(o, m))) out.push(m);
  }
  return out;
}

const word = (n: number) => `${n & 0xff}, ${(n >> 8) & 0xff}`;
/** A key item's zone, square on it: her reach (600 ahead) lands in it from a step away, on a table she stands her radius off, and it leaves the room's checks beside it theirs. */
const ZONE = 1500;

/**
 * A room's key item pickups: each where its scene put it, kept once taken by
 * its own flag (`flags` is consumed), its model in slot `first` onwards.
 * aot ids count up from `id`.
 */
export function keyItemLines(spots: readonly ItemSpot[], flags: number[], id: number, first: number): string[] {
  const models = keyItemModels(spots);
  return spots.flatMap((s) => {
    const k = byStep(s.step);
    const flag = flags.shift();
    if (flag === undefined) throw new Error(`${s.step}: no item flag left`);
    const slot = first + models.findIndex((m) => sameModel(m, k.model));
    const zone = `${s.x - ZONE / 2}, ${s.z - ZONE / 2}, ${ZONE}, ${ZONE}`;
    return [
      `if (ck(FG_ITEM, ${flag}, 0)) {  // ${k.name.toLowerCase()} (${s.step})`,
      `    item_aot_set(${id++}, ${zone}, ${k.id}, 1, ${slot}, 255, ${word(s.x)}, ${word(s.y & 0xffff)}, ${word(s.z)}, 0, 0, ${flag}, 129, 0, 0);`,
      '}',
    ];
  });
}
