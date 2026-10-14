// workshop (415), written by day/scripts.ts from day/workshop/scene.py: edit the scene, not this file.
// init procedure 0
// To camp-yard.
door_aot_set(0, 3740, 1700, 2040, 850, 0, 0, 0, 4, 0, ROOM_31E, 25840, 0, 20740, 1024, UNLOCKED, 193);
aot_set(1, 8755, 7905, 2380, 1105, SCE_MESSAGE, 129, 129, 0, 255, 0, 0, 0);
aot_set(2, 3060, 8670, 3060, 1020, SCE_MESSAGE, 129, 130, 0, 255, 0, 0, 0);
aot_set(3, 6460, 3230, 1700, 1360, SCE_MESSAGE, 129, 131, 0, 255, 0, 0, 0);
aot_set(4, 2975, 3910, 935, 1530, SCE_MESSAGE, 129, 132, 0, 255, 0, 0, 0);
aot_set(5, 3910, 7225, 2040, 935, SCE_MESSAGE, 129, 133, 0, 255, 0, 0, 0);
aot_set(6, 3230, 2040, 2890, 1870, SCE_MESSAGE, 129, 134, 0, 255, 0, 0, 0);
return;

// main procedure 0
if (ck(FG_COMMON, 218, 1)) {
    set(FG_COMMON, 218, 0);
    message(128, 255, 0);
}
return;
