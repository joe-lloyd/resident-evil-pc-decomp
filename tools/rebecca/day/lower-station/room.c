// lower-station (21A), written by day/scripts.ts from day/lower-station/scene.py: edit the scene, not this file.
// init procedure 0
// To lower-yard.
door_aot_set(0, 1190, 4165, 1572, 2465, 0, 1, 10, 8, 0, ROOM_219, 29580, 0, 9350, 2048, UNLOCKED, 193);
if (ck(FG_ITEM, 252, 0)) {  // the skyway map (maps/pickups.ts)
    item_aot_set(1, 6790, 1690, 1800, 1800, 82, 1, 1, 255, 10, 30, 0, 0, 30, 10, 0, 0, 252, 129, 0, 0);
}
if (ck(FG_ITEM, 196, 0)) {  // clip
    item_aot_set(2, 8110, 3350, 1200, 1200, 11, 15, 0, 255, 6, 34, 0, 0, 110, 15, 0, 0, 196, 129, 0, 0);
}
// Lower station log, a file.
if (ck(FG_ITEM, 238, 0)) {
    item_aot_set(3, 6290, 5355, 1700, 1912, 100, 1, 2, 255, 0, 0, 0, 0, 0, 0, 0, 0, 238, 129, 0, 0);
}
aot_set(4, 8755, 5865, 1275, 1530, SCE_MESSAGE, 129, 129, 0, 255, 0, 0, 0);
aot_set(5, 2975, 3400, 4335, 1530, SCE_MESSAGE, 129, 130, 0, 255, 0, 0, 0);
aot_set(6, 1190, 2210, 1700, 1700, SCE_MESSAGE, 129, 131, 0, 255, 0, 0, 0);
aot_set(7, 7990, 2040, 2040, 2975, SCE_MESSAGE, 129, 132, 0, 255, 0, 0, 0);
aot_set(8, 1700, 1190, 1870, 1360, SCE_MESSAGE, 129, 133, 0, 255, 0, 0, 0);
aot_set(9, 8670, 5015, 850, 1615, SCE_MESSAGE, 129, 134, 0, 255, 0, 0, 0);
aot_set(10, 4930, 7268, 2380, 1742, SCE_MESSAGE, 129, 135, 0, 255, 0, 0, 0);
aot_set(11, 7990, 5865, 765, 1530, SCE_MESSAGE, 129, 136, 0, 255, 0, 0, 0);
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
