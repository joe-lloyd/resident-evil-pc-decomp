// mine-office (51D), written by day/scripts.ts from day/mine-office/scene.py: edit the scene, not this file.
// init procedure 0
// To tunnel.
door_aot_set(0, 4080, 5610, 1530, 850, 1, 0, 7, 1, 0, ROOM_51C, 21335, 0, 15980, 3072, UNLOCKED, 193);
// The typewriter and the item box, its lid on the body the scene paints.
aot_set(1, 3485, 1700, 1190, 2210, SCE_TYPEWRITER, 129, 0, 0, 0, 0, 0, 0);
aot_set(2, 5780, 3400, 2040, 2159, SCE_ITEMBOX, 129, 0, 0, 0, 0, 0, 0);
obj(0, 17, 255, 7809, -1440, 4480, 2048, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0);
if (ck(FG_ITEM, 251, 0)) {  // the mine survey (maps/pickups.ts)
    item_aot_set(3, 3160, 3840, 1200, 1200, 81, 1, 1, 255, 176, 14, 0, 0, 88, 17, 0, 0, 251, 129, 0, 0);
}
// Mine map, a file.
if (ck(FG_ITEM, 237, 0)) {
    item_aot_set(4, 4335, 1700, 765, 1445, 98, 1, 2, 255, 0, 0, 0, 0, 0, 0, 0, 0, 237, 129, 0, 0);
}
aot_set(5, 5100, 1700, 1020, 1445, SCE_MESSAGE, 129, 129, 0, 255, 0, 0, 0);
aot_set(6, 3740, 3145, 1530, 1275, SCE_MESSAGE, 129, 130, 0, 255, 0, 0, 0);
aot_set(7, 1700, 2890, 1700, 3230, SCE_MESSAGE, 129, 131, 0, 255, 0, 0, 0);
aot_set(8, 6460, 2040, 1360, 1275, SCE_MESSAGE, 129, 132, 0, 255, 0, 0, 0);
aot_set(9, 5270, 3910, 850, 850, SCE_MESSAGE, 129, 133, 0, 255, 0, 0, 0);
if (ck(FG_ITEM, 191, 0)) {  // ribbons
    item_aot_set(10, 4560, 2860, 1800, 1800, 47, 3, 0, 255, 84, 21, 0, 0, 176, 14, 0, 0, 191, 129, 0, 0);
}
if (ck(FG_ITEM, 251, 0)) {
    set(FG_ROOM, 12, 0);
}
return;

// main procedure 0
if (ck(FG_COMMON, 236, 1)) {
    set(FG_COMMON, 236, 0);
    message(128, 255, 0);
}
if (ck(FG_ROOM, 12, 0) && ck(FG_ITEM, 251, 1)) {
    set(FG_ROOM, 12, 1);
    message(134, 255, 0);
}
return;
