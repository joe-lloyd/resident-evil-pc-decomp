// lower-station (21A), written by day/scripts.ts from day/lower-station/scene.py: edit the scene, not this file.
// init procedure 0
// To lower-yard.
door_aot_set(0, 1700, 4420, 765, 1700, 0, 1, 10, 8, 0, ROOM_219, 29580, 0, 9350, 2048, UNLOCKED, 193);
if (ck(FG_ITEM, 252, 0)) {  // the skyway map (maps/pickups.ts)
    item_aot_set(1, 6600, 1500, 1800, 1800, 82, 1, 1, 255, 76, 29, 0, 0, 96, 9, 0, 0, 252, 129, 0, 0);
}
// Lower station log, a file.
if (ck(FG_ITEM, 238, 0)) {
    item_aot_set(2, 6800, 5865, 1190, 1020, 100, 1, 2, 255, 0, 0, 0, 0, 0, 0, 0, 0, 238, 129, 0, 0);
}
aot_set(3, 8755, 5865, 765, 1020, SCE_MESSAGE, 129, 129, 0, 255, 0, 0, 0);
aot_set(4, 3060, 3400, 3740, 1020, SCE_MESSAGE, 129, 130, 0, 255, 0, 0, 0);
aot_set(5, 1700, 2210, 1190, 1700, SCE_MESSAGE, 129, 131, 0, 255, 0, 0, 0);
aot_set(6, 8500, 2550, 1020, 2040, SCE_MESSAGE, 129, 132, 0, 255, 0, 0, 0);
aot_set(7, 1700, 1700, 1360, 850, SCE_MESSAGE, 129, 133, 0, 255, 0, 0, 0);
aot_set(8, 8670, 5440, 850, 1190, SCE_MESSAGE, 129, 134, 0, 255, 0, 0, 0);
aot_set(9, 5440, 7650, 1360, 850, SCE_MESSAGE, 129, 135, 0, 255, 0, 0, 0);
aot_set(10, 7990, 5865, 765, 1020, SCE_MESSAGE, 129, 136, 0, 255, 0, 0, 0);
if (ck(FG_ITEM, 196, 0)) {  // clip
    item_aot_set(11, 7920, 3500, 1200, 1200, 11, 15, 0, 255, 72, 33, 0, 0, 4, 16, 0, 0, 196, 129, 0, 0);
}
if (ck(FG_ITEM, 252, 0)) {
    set(FG_ROOM, 12, 0);
}
return;

// main procedure 0
if (ck(FG_ROOM, 12, 0) && ck(FG_ITEM, 252, 1)) {
    set(FG_ROOM, 12, 1);
    message(137, 255, 0);
}
return;
