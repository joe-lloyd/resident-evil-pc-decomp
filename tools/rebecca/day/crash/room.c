// crash (21B), written by day/scripts.ts from day/crash/scene.py: edit the scene, not this file.
// init procedure 0
// To valley-path.
door_aot_set(0, 31280, 12920, 1020, 3740, 0, 15, 48, 4, 0, ROOM_218, 4420, 0, 15470, 0, UNLOCKED, 1);
aot_set(1, 10540, 14280, 2380, 1700, SCE_MESSAGE, 129, 129, 0, 255, 0, 0, 0);
aot_set(2, 14280, 14280, 2720, 1360, SCE_MESSAGE, 129, 130, 0, 255, 0, 0, 0);
aot_set(3, 11560, 16830, 2720, 1700, SCE_MESSAGE, 129, 131, 0, 255, 0, 0, 0);
aot_set(4, 14790, 15640, 4760, 2890, SCE_MESSAGE, 129, 132, 0, 255, 0, 0, 0);
aot_set(5, 9520, 15300, 2040, 1530, SCE_MESSAGE, 129, 133, 0, 255, 0, 0, 0);
aot_set(6, 20570, 6800, 5100, 4420, SCE_MESSAGE, 129, 134, 0, 255, 0, 0, 0);
aot_set(7, 18700, 18870, 1700, 1700, SCE_MESSAGE, 129, 135, 0, 255, 0, 0, 0);
aot_set(8, 22270, 12410, 3230, 3400, SCE_MESSAGE, 129, 136, 0, 255, 0, 0, 0);
aot_set(9, 29750, 12920, 1870, 1020, SCE_MESSAGE, 129, 137, 0, 255, 0, 0, 0);
aot_set(10, 26860, 14280, 2380, 1020, SCE_MESSAGE, 129, 138, 0, 255, 0, 0, 0);
return;

// main procedure 0
if (ck(FG_COMMON, 248, 1)) {
    set(FG_COMMON, 248, 0);
    message(128, 255, 0);
}
return;
