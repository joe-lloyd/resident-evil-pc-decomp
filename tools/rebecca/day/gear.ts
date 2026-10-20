// Her weapons through the day: she starts with her knife, Beretta and a
// spare clip. The gallery scare keeps them. At the crawl's narrow turn,
// before the mansion hatch, she leaves her pack and long weapons behind.
// Only the Beretta, item 0x02, and its loaded rounds stay, with her key items.
// The scene unequips her current weapon before removing inventory entries.

/** Six case slots. remove_item removes the first match, so try every slot. */
export const BAG_SLOTS = 6;

const range = (a: number, b: number) => Array.from({ length: b - a + 1 }, (_, i) => a + i);

/**
 * Gear left under the floor: every weapon and spare round in 0x01-0x12
 * except the Beretta at 0x02, sprays at 0x41, and herbs and mixes at
 * 0x43-0x4B. The Beretta entry and its loaded count are never touched.
 * Key items use other ids and stay with her.
 */
export const GEAR: readonly number[] = [...range(0x01, 0x12).filter((id) => id !== 0x02), 0x41, ...range(0x43, 0x4b)];

/**
 * Event-script SCD blocks. Each item gets its own block, so no conditional
 * or SCD length byte overflows. Run inside cut-leave-gear, once, with her
 * controls off. No room-main loop can remove supplies on a later visit.
 */
export const LEAVE_GEAR = [
  'scd {', '    sys_multi(0);', '    return;', '}',
  ...GEAR.flatMap((id) => [
    'scd {',
    ...Array.from({ length: BAG_SLOTS }, () => [`    if (item_ck(${id})) {`, `        remove_item(${id});`, '    }']).flat(),
    '    return;', '}',
  ]),
];
