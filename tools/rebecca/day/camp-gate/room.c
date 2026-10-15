// camp-gate (31D), written by day/scripts.ts from day/camp-gate/scene.py: edit the scene, not this file.
// init procedure 0
// To logging-road.
door_aot_set(0, 1700, 14280, 1020, 5100, 0, 15, 48, 4, 0, ROOM_31C, 29410, 0, 18020, 2048, UNLOCKED, 1);
// To camp-yard.
door_aot_set(1, 15300, 3400, 3740, 1020, 0, 15, 48, 4, 0, ROOM_31E, 17170, 0, 28730, 1024, UNLOCKED, 1);
aot_set(2, 6970, 3400, 3060, 1360, SCE_MESSAGE, 129, 129, 0, 255, 0, 0, 0);
aot_set(3, 15300, 4420, 3740, 1360, SCE_MESSAGE, 129, 130, 0, 255, 0, 0, 0);
aot_set(4, 18360, 4080, 2040, 2040, SCE_MESSAGE, 129, 131, 0, 255, 0, 0, 0);
aot_set(5, 11560, 6800, 3740, 1700, SCE_MESSAGE, 129, 132, 0, 255, 0, 0, 0);
aot_set(6, 22440, 11220, 3060, 2040, SCE_MESSAGE, 129, 133, 0, 255, 0, 0, 0);
aot_set(7, 8840, 7820, 5780, 4080, SCE_MESSAGE, 129, 134, 0, 255, 0, 0, 0);
if (ck(FG_ITEM, 249, 0)) {  // the camp plan (maps/pickups.ts)
    item_aot_set(8, 28700, 16460, 1800, 1800, 79, 1, 0, 255, 160, 115, 0, 0, 208, 67, 0, 0, 249, 129, 0, 0);
}
return;

// main procedure 0
if (ck(FG_COMMON, 212, 1)) {
    set(FG_COMMON, 212, 0);
    message(128, 255, 0);
}
return;
