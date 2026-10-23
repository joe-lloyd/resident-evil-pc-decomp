// mine-office (51D), written by day/scripts.ts from day/mine-office/scene.py: edit the scene, not this file.
// init procedure 0
// To tunnel.
door_aot_set(0, 3740, 5185, 2380, 1785, 1, 0, 7, 1, 0, ROOM_51C, 21335, 0, 15980, 3072, UNLOCKED, 193);
// The typewriter and the item box, its lid on the body the scene paints.
aot_set(1, 3485, 1700, 850, 2550, SCE_TYPEWRITER, 129, 0, 0, 0, 0, 0, 0);
aot_set(2, 5780, 3400, 2040, 2159, SCE_ITEMBOX, 129, 0, 0, 0, 0, 0, 0);
obj(0, 17, 255, 7809, -1440, 4480, 2048, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0);
if (ck(FG_ITEM, 251, 0)) {  // the mine survey (maps/pickups.ts)
    item_aot_set(3, 1990, 1650, 1200, 1200, 81, 1, 1, 255, 30, 10, 0, 0, 202, 8, 0, 0, 251, 129, 0, 0);
}
if (ck(FG_ITEM, 192, 0)) {  // ribbons
    item_aot_set(4, 3010, 3010, 1200, 1200, 47, 3, 0, 255, 26, 14, 0, 0, 26, 14, 0, 0, 192, 129, 0, 0);
}
// Mine map, a file.
if (ck(FG_ITEM, 237, 0)) {
    item_aot_set(5, 4335, 1190, 765, 1955, 98, 1, 2, 255, 0, 0, 0, 0, 0, 0, 0, 0, 237, 129, 0, 0);
}
aot_set(6, 5100, 1190, 1190, 1955, SCE_MESSAGE, 129, 129, 0, 255, 0, 0, 0);
aot_set(7, 3570, 3145, 1700, 1275, SCE_MESSAGE, 129, 130, 0, 255, 0, 0, 0);
aot_set(8, 1190, 2890, 2380, 3740, SCE_MESSAGE, 129, 131, 0, 255, 0, 0, 0);
aot_set(9, 6290, 2040, 2040, 1572, SCE_MESSAGE, 129, 132, 0, 255, 0, 0, 0);
aot_set(10, 5270, 3910, 1360, 1275, SCE_MESSAGE, 129, 133, 0, 255, 0, 0, 0);
if (ck(FG_ITEM, 251, 0)) {
    set(FG_ROOM, 12, 0);
}
return;

// main procedure 0
if (ck(FG_ROOM, 12, 0) && ck(FG_ITEM, 251, 1)) {
    set(FG_ROOM, 12, 1);
    message(134, 255, 0);
}
return;
