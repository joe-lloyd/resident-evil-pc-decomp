// ROOM4080, the guardhouse passage, in Rebecca's scenario (Chapter 4: the
// guardhouse). She arrives from the bar by a chapter break. Plant 42's roots
// run under the door to its room (ROOM40C0); V-JOLT from the drug storehouse
// (ROOM4090) kills them, and with them the plant (its kill flag, FG_ENEMY 96).
// Chris's wasps and his events are left out.
//
// FG_COMMON 220: the roots are dead. 221: the chapter title has shown.
// (ck(bank, n, 1) holds while flag n is clear; set(bank, n, 0) sets it.)
// A message zone records the zone she checked: cmpb(16, 0, zone + 1).
// aot_delete(n, type, flags) re-arms zone n; SCE_NONE with flags 0 kills it.
// Room messages are 0x80 + index: 144 is message 16.
// init procedure 0
door_aot_set(0, 0, 2200, 3000, 2100, 0, 0, 0, 4, 0, ROOM_S05, 23200, 0, 8800, 2048, UNLOCKED, 129);
door_aot_set(1, 5500, 9400, 3000, 1800, 1, 0, 7, 1, 0, ROOM_S09, 9000, 0, 3000, 2048, UNLOCKED, 129);
door_aot_set(2, 18200, 6500, 3000, 2000, 1, 0, 6, 1, 170, ROOM_S0A, 2900, 0, 2800, 0, 58 /* Dorm Key (003) */, 129);
// In Chris's game this door is blocked from the other side until he has been
// in ROOM40C0 another way; for her it is the way in.
door_aot_set(3, 27800, 2100, 3000, 4000, 12, 0, 0, 1, 64, ROOM_S0C, 3000, 0, 10200, 0, UNLOCKED, 129);
item_aot_set(5, 15000, 21700, 2000, 1000, 57 /* Dorm Key (002) */, 1, 0, 255, 0, 0, 0, 0, 0, 0, 0, 4, 72, 129, 0, 0);
// The roots, in front of door 3.
if (ck(FG_COMMON, 220, 1)) {
    aot_set(4, 24200, 2400, 2600, 3400, SCE_MESSAGE, 129, 145, 0, 255, 0, 0, 0);
} else {
    aot_set(4, 24200, 2400, 2600, 3400, SCE_MESSAGE, 129, 147, 0, 255, 0, 0, 0);
}
return;

// main procedure 0
if (ck(FG_COMMON, 221, 1)) {
    set(FG_COMMON, 221, 0);
    message(144, 0, 0);
}
// She checked the roots with V-JOLT in her bag: they die, and the plant.
if (ck(FG_COMMON, 220, 1) && cmpb(16, 0, 5)) {
    if (item_ck(27 /* V-JOLT */)) {
        set(FG_COMMON, 220, 0);
        set(FG_ENEMY, 96, 0);
        remove_item(27 /* V-JOLT */);
        message(146, 0, 0);
        aot_reset(4, SCE_MESSAGE, 129, 147, 255, 0);
    }
}
return;
