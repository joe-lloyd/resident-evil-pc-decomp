// crash (21B), written by day/scripts.ts from day/crash/scene.py: edit the scene, not this file.
// init procedure 0
// To valley-path.
door_aot_set(0, 27880, 11900, 1020, 3400, 0, 15, 48, 4, 0, ROOM_218, 4420, 0, 15470, 0, UNLOCKED, 1);
aot_set(1, 12920, 14280, 2380, 1700, SCE_MESSAGE, 129, 129, 0, 255, 0, 0, 0);
aot_set(2, 16660, 14280, 2720, 1360, SCE_MESSAGE, 129, 130, 0, 255, 0, 0, 0);
aot_set(3, 13940, 16830, 2720, 1700, SCE_MESSAGE, 129, 131, 0, 255, 0, 0, 0);
aot_set(4, 17170, 15640, 4760, 2890, SCE_MESSAGE, 129, 132, 0, 255, 0, 0, 0);
aot_set(5, 11900, 15300, 2040, 1530, SCE_MESSAGE, 129, 133, 0, 255, 0, 0, 0);
aot_set(6, 22950, 6800, 5100, 4420, SCE_MESSAGE, 129, 134, 0, 255, 0, 0, 0);
aot_set(7, 21080, 18870, 1700, 1700, SCE_MESSAGE, 129, 135, 0, 255, 0, 0, 0);
aot_set(8, 24650, 12410, 3230, 3400, SCE_MESSAGE, 129, 136, 0, 255, 0, 0, 0);
return;

// main procedure 0
if (ck(FG_COMMON, 248, 1)) {
    set(FG_COMMON, 248, 0);
    message(128, 255, 0);
}
return;
