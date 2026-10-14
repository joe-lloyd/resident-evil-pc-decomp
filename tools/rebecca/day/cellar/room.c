// cellar (11D), written by day/scripts.ts from day/cellar/scene.py: edit the scene, not this file.
// init procedure 0
// To back-garden.
door_aot_set(0, 11220, 1700, 2380, 1020, 0, 0, 0, 4, 0, ROOM_110, 21760, 0, 19550, 1024, UNLOCKED, 129);
// To wine.
door_aot_set(1, 14280, 3400, 1020, 2040, 0, 0, 0, 4, 0, ROOM_11E, 3230, 0, 4420, 0, UNLOCKED, 129);
// To crawl.
door_aot_set(2, 1700, 8500, 1020, 1360, 0, 0, 0, 4, 0, ROOM_11F, 3740, 0, 8840, 0, UNLOCKED, 129);
aot_set(3, 7197, 5401, 3060, 2720, SCE_MESSAGE, 129, 129, 0, 255, 0, 0, 0);
aot_set(4, 5100, 7140, 2040, 1700, SCE_MESSAGE, 129, 130, 0, 255, 0, 0, 0);
aot_set(5, 11220, 3740, 3060, 1870, SCE_MESSAGE, 129, 131, 0, 255, 0, 0, 0);
aot_set(6, 2720, 4420, 1020, 3910, SCE_MESSAGE, 129, 132, 0, 255, 0, 0, 0);
aot_set(7, 1700, 8500, 1360, 1360, SCE_MESSAGE, 129, 133, 0, 255, 0, 0, 0);
aot_set(8, 12920, 1700, 2380, 2040, SCE_MESSAGE, 129, 134, 0, 255, 0, 0, 0);
aot_set(9, 3400, 8330, 8500, 1870, SCE_MESSAGE, 129, 135, 0, 255, 0, 0, 0);
return;

// main procedure 0
if (ck(FG_COMMON, 255, 1)) {
    set(FG_COMMON, 255, 0);
    message(128, 255, 0);
}
return;
