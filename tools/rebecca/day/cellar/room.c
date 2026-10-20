// cellar (11D), written by day/scripts.ts from day/cellar/scene.py: edit the scene, not this file.
// init procedure 0
// To back-garden.
door_aot_set(0, 11220, 1700, 2380, 1020, 1, 0, 7, 1, 0, ROOM_110, 21760, 0, 19550, 1024, UNLOCKED, 193);
// To wine.
door_aot_set(1, 14280, 3400, 1020, 2040, 1, 0, 33, 1, 0, ROOM_11E, 3230, 0, 4420, 0, UNLOCKED, 193);
// To crawl.
if (ck(FG_COMMON, 142, 1)) {
    aot_set(2, 1700, 8500, 2210, 1360, SCE_MESSAGE, 129, 129, 0, 255, 0, 0, 0);
} else {
    door_aot_set(2, 1700, 8500, 2210, 1360, 1, 0, 7, 1, 0, ROOM_11F, 3740, 0, 8840, 0, UNLOCKED, 193);
}
aot_set(3, 7197, 5401, 3060, 2720, SCE_MESSAGE, 129, 130, 0, 255, 0, 0, 0);
aot_set(4, 5100, 7140, 2040, 1700, SCE_MESSAGE, 129, 131, 0, 255, 0, 0, 0);
aot_set(5, 11220, 3740, 3060, 1870, SCE_MESSAGE, 129, 132, 0, 255, 0, 0, 0);
aot_set(6, 12920, 1700, 2380, 2040, SCE_MESSAGE, 129, 133, 0, 255, 0, 0, 0);
aot_set(7, 4760, 8330, 7140, 1870, SCE_MESSAGE, 129, 134, 0, 255, 0, 0, 0);
enemy(17, 0, 236, 1, 2, 0, 0, 4019, 0, 0, 5460, 0, 2400, 0, 0, 0, 0);  // a zombie
if (ck(FG_ITEM, 204, 0)) {  // rounds
    item_aot_set(8, 4860, 1800, 1200, 1200, 11, 5, 0, 255, 84, 21, 0, 0, 96, 9, 0, 0, 204, 129, 0, 0);
}
// push-rack (day/events.ts), FG_COMMON 142 once it has happened.
if (ck(FG_COMMON, 142, 1)) {
    aot_set(9, 2720, 5950, 1020, 2550, SCE_USEITEM, 129, 4, 0, 12, 0, 1, 0);   // the action button here raises FG_ROOM 12
} else {
    aot_set(10, 2720, 5950, 1020, 2550, SCE_MESSAGE, 129, 136, 0, 255, 0, 0, 0);
}
return;

// main procedure 0
if (ck(FG_COMMON, 142, 1) && ck(FG_ROOM, 12, 0)) {
    set(FG_ROOM, 12, 1);
    set(FG_COMMON, 142, 0);
    door_aot_set(2, 1700, 8500, 2210, 1360, 1, 0, 7, 1, 0, ROOM_11F, 3740, 0, 8840, 0, UNLOCKED, 193);
    aot_set(10, 2720, 5950, 1020, 2550, SCE_MESSAGE, 129, 136, 0, 255, 0, 0, 0);
    message(137, 255, 0);
}
return;
