// ROOM4090, the drug storehouse, in Rebecca's scenario (Chapter 4). In Chris's
// game she mixes V-JOLT here for him. Here she works it out at the mixing
// table herself, and the V-JOLT stands on the table to take.
//
// FG_COMMON 222: she has mixed the V-JOLT. FG_ITEM 240: she has taken it.
// The V-JOLT uses the room's item model 4 (the water bottle) at (6640, -3010,
// 6220), where Chris's game puts its third empty bottle.
// Room messages are 0x80 + index: 155 is message 27.
// init procedure 0
door_aot_set(0, 9600, 2300, 1800, 1700, 2, 0, 7, 1, 0, ROOM_S08, 8500, 0, 10200, 0, UNLOCKED, 129);
aot_set(8, 5900, 1400, 1100, 1500, SCE_MESSAGE, 129, 132, 0, 77, 0, 0, 0);
aot_set(9, 3000, 1500, 1200, 600, SCE_MESSAGE, 129, 128, 0, 77, 0, 0, 0);
aot_set(10, 9800, 4400, 700, 1700, SCE_MESSAGE, 129, 129, 0, 77, 0, 0, 0);
aot_set(12, 1900, 3500, 1200, 1900, SCE_MESSAGE, 129, 137, 0, 77, 0, 0, 0);
// The mixing table.
if (ck(FG_COMMON, 222, 1)) {
    aot_set(11, 5100, 6000, 4400, 1100, SCE_MESSAGE, 129, 155, 0, 255, 0, 0, 0);
} else {
    if (ck(FG_ITEM, 240, 0)) {
        item_aot_set(1, 5100, 6000, 4400, 1100, 27 /* V-JOLT */, 1, 4, 255, 240, 25, 62, 244, 76, 24, 132, 3, 240, 129, 0, 0);
    }
}
return;

// main procedure 0
if (ck(FG_COMMON, 222, 1) && cmpb(16, 0, 12)) {
    set(FG_COMMON, 222, 0);
    aot_delete(11, SCE_NONE, 0);
    item_aot_set(1, 5100, 6000, 4400, 1100, 27 /* V-JOLT */, 1, 4, 255, 240, 25, 62, 244, 76, 24, 132, 3, 240, 129, 0, 0);
}
return;
