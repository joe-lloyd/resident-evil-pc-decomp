// cellar (11D), written by day/scripts.ts from day/cellar/scene.py: edit the scene, not this file.
// init procedure 0
// To back-garden.
// Shut from this side until she opens it from the other (FG_LOCK 49).
if (ck(FG_LOCK, 49, 1)) {
    aot_set(0, 12495, 1700, 1105, 1530, SCE_MESSAGE, 129, 129, 0, 255, 0, 0, 0);
} else {
    door_aot_set(0, 12495, 1700, 1105, 1530, 1, 0, 7, 1, 0, ROOM_110, 16065, 0, 21335, 1024, UNLOCKED, 193);
}
// To kennels.
// Shut from this side until she opens it from the other (FG_LOCK 50).
if (ck(FG_LOCK, 50, 1)) {
    aot_set(1, 5270, 1190, 2720, 2040, SCE_MESSAGE, 129, 130, 0, 255, 0, 0, 0);
} else {
    door_aot_set(1, 5270, 1190, 2720, 2040, 0, 14, 20, 64, 0, ROOM_21F, 20400, 0, 20315, 1024, UNLOCKED, 193);
}
// To wine.
door_aot_set(2, 14280, 3400, 1530, 2040, 1, 0, 33, 1, 0, ROOM_11E, 3230, 0, 4420, 0, UNLOCKED, 193);
// To crawl.
if (ck(FG_COMMON, 142, 1)) {
    aot_set(3, 1190, 8500, 2720, 1870, SCE_MESSAGE, 129, 131, 0, 255, 0, 0, 0);
} else {
    door_aot_set(3, 1190, 8500, 2720, 1870, 1, 0, 7, 1, 0, ROOM_11F, 3740, 0, 8840, 0, UNLOCKED, 193);
}
if (ck(FG_ITEM, 205, 0)) {  // rounds
    item_aot_set(4, 11850, 8790, 1200, 1200, 11, 5, 0, 255, 162, 48, 0, 0, 174, 36, 0, 0, 205, 129, 0, 0);
}
aot_set(5, 7197, 4891, 3541, 3230, SCE_MESSAGE, 129, 132, 0, 255, 0, 0, 0);
aot_set(6, 4590, 7140, 2550, 1700, SCE_MESSAGE, 129, 133, 0, 255, 0, 0, 0);
aot_set(7, 10739, 3740, 3541, 2380, SCE_MESSAGE, 129, 134, 0, 255, 0, 0, 0);
aot_set(8, 12920, 1700, 2380, 2040, SCE_MESSAGE, 129, 135, 0, 255, 0, 0, 0);
aot_set(9, 10710, 1190, 1785, 1530, SCE_MESSAGE, 129, 136, 0, 255, 0, 0, 0);
aot_set(10, 4760, 8330, 7140, 2380, SCE_MESSAGE, 129, 137, 0, 255, 0, 0, 0);
enemy(17, 0, 248, 1, 2, 0, 0, 3185, 0, 0, 2740, 0, 4440, 0, 0, 0, 0);  // a zombie
// push-rack (day/events.ts), FG_COMMON 142 once it has happened.
if (ck(FG_COMMON, 142, 1)) {
    aot_set(11, 2720, 5440, 1530, 3060, SCE_USEITEM, 129, 4, 0, 12, 0, 1, 0);   // the action button here raises FG_ROOM 12
} else {
    aot_set(12, 2720, 5440, 1530, 3060, SCE_MESSAGE, 129, 139, 0, 255, 0, 0, 0);
}
return;

// main procedure 0
if (ck(FG_COMMON, 142, 1) && ck(FG_ROOM, 12, 0)) {
    set(FG_ROOM, 12, 1);
    set(FG_COMMON, 142, 0);
    door_aot_set(3, 1190, 8500, 2720, 1870, 1, 0, 7, 1, 0, ROOM_11F, 3740, 0, 8840, 0, UNLOCKED, 193);
    aot_set(12, 2720, 5440, 1530, 3060, SCE_MESSAGE, 129, 139, 0, 255, 0, 0, 0);
    message(140, 255, 0);
}
return;
