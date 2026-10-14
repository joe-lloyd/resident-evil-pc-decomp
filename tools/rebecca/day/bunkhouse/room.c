// bunkhouse (31F), written by day/scripts.ts from day/bunkhouse/scene.py: edit the scene, not this file.
// init procedure 0
// To camp-yard.
door_aot_set(0, 10200, 9350, 1530, 850, 0, 0, 0, 4, 0, ROOM_31E, 19465, 0, 5780, 3072, UNLOCKED, 129);
aot_set(1, 11475, 1700, 1360, 2210, SCE_MESSAGE, 129, 129, 0, 255, 0, 0, 0);
aot_set(2, 12920, 3910, 3230, 850, SCE_MESSAGE, 129, 130, 0, 255, 0, 0, 0);
aot_set(3, 15640, 6970, 3060, 935, SCE_MESSAGE, 129, 131, 0, 255, 0, 0, 0);
aot_set(4, 12920, 7565, 1700, 1105, SCE_MESSAGE, 129, 132, 0, 255, 0, 0, 0);
aot_set(5, 7480, 5100, 2380, 1870, SCE_MESSAGE, 129, 133, 0, 255, 0, 0, 0);
aot_set(6, 11730, 6290, 2210, 1870, SCE_MESSAGE, 129, 134, 0, 255, 0, 0, 0);
aot_set(7, 9860, 3145, 2040, 935, SCE_MESSAGE, 129, 135, 0, 255, 0, 0, 0);
aot_set(8, 2210, 3910, 2550, 850, SCE_MESSAGE, 129, 136, 0, 255, 0, 0, 0);
return;

// main procedure 0
if (ck(FG_COMMON, 214, 1)) {
    set(FG_COMMON, 214, 0);
    message(128, 255, 0);
}
return;
