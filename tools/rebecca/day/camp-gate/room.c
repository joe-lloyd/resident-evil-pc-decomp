// camp-gate (31D), written by day/scripts.ts from day/camp-gate/scene.py: edit the scene, not this file.
// init procedure 0
// To logging-road.
door_aot_set(0, 1700, 14280, 1020, 5100, 0, 15, 48, 4, 0, ROOM_31C, 29410, 0, 18020, 2048, UNLOCKED, 1);
// To camp-yard.
door_aot_set(1, 15300, 3400, 3740, 1020, 0, 15, 48, 4, 0, ROOM_31E, 17170, 0, 28730, 1024, UNLOCKED, 1);
if (ck(FG_ITEM, 249, 0)) {  // the camp plan (maps/pickups.ts)
    item_aot_set(2, 27870, 13930, 1800, 1800, 79, 1, 0, 255, 98, 112, 0, 0, 238, 57, 0, 0, 249, 129, 0, 0);
}
aot_set(3, 6460, 2890, 4080, 2380, SCE_MESSAGE, 129, 129, 0, 255, 0, 0, 0);
aot_set(4, 14790, 4420, 4250, 1785, SCE_MESSAGE, 129, 130, 0, 255, 0, 0, 0);
aot_set(5, 18360, 4080, 2550, 2550, SCE_MESSAGE, 129, 131, 0, 255, 0, 0, 0);
aot_set(6, 8160, 7310, 5270, 4080, SCE_MESSAGE, 129, 132, 0, 255, 0, 0, 0);
aot_set(7, 21930, 10710, 4080, 3060, SCE_MESSAGE, 129, 133, 0, 255, 0, 0, 0);
aot_set(8, 13770, 6205, 2720, 2125, SCE_MESSAGE, 129, 134, 0, 255, 0, 0, 0);
aot_set(9, 1190, 6970, 6970, 2380, SCE_MESSAGE, 129, 135, 0, 255, 0, 0, 0);
if (ck(FG_ITEM, 249, 0)) {
    set(FG_ROOM, 12, 0);
}
return;

// main procedure 0
if (ck(FG_ROOM, 12, 0) && ck(FG_ITEM, 249, 1)) {
    set(FG_ROOM, 12, 1);
    message(136, 255, 0);
}
return;
