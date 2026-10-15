// Her weapons through the day (the plan's row weapons-plan): she starts with
// her knife and her Beretta with a spare clip (src/game/GameStart.cpp); the
// mine takes everything she fights and heals with; a gun again from Kevin at
// the crash (supplies.ts, the crash's Beretta).
//
// The loss happens the first time she wades into the flooded gallery: the
// floor gives way under the black water. scripts.ts makes her first thought
// there the loss: the weapon in her hands drops (sys_multi 0, RE1's own
// "clear the equipped weapon"), then each gear item she carries goes. Her key
// items stay, or the gondola could not be finished.

/**
 * Slots in her case (BioCardLayout.itemsSlots). remove_item takes the first
 * slot holding an item, and a script has no loop, so the loss tries each item
 * this many times: two sprays, or a clip in two slots, all go.
 */
export const BAG_SLOTS = 6;

/**
 * The FG_ROOM bit up while the loss happens, in word 0 below the events'
 * bits (scripts.ts counts those from 12; the engine uses 0 and 29-31).
 */
export const LOSS_BIT = 11;

/** The room where the mine takes her gear. */
export const LOSS_ROOM = 'gallery';

/** What she says when it happens, after the room's own first thought. */
export const LOSS_LINE = "The floor's gone under me! My bag, the gun... gone, down there in the dark.";

const range = (a: number, b: number) => Array.from({ length: b - a + 1 }, (_, i) => a + i);

/**
 * What the mine takes: the weapons and their rounds (RE1's items 0x01-0x12),
 * the first aid spray (0x41) and the herbs and their mixes (0x43-0x4B). Not
 * the ids her key items borrow (items.ts), which fall outside these.
 */
export const GEAR: readonly number[] = [...range(0x01, 0x12), 0x41, ...range(0x43, 0x4b)];

/** What starts the loss: the bit up (the room's main takes each item while it is), and the weapon out of her hands. */
export const LOSS_START = [`set(FG_ROOM, ${LOSS_BIT}, 0);`, 'sys_multi(0);'] as const;
