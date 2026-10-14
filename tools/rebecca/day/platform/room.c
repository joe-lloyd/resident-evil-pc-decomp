// platform (318), written by day/scripts.ts from day/platform/scene.py: edit the scene, not this file.
// init procedure 0
// To bridge.
door_aot_set(0, 5100, 3400, 5100, 1020, 0, 15, 48, 4, 0, ROOM_317, 10200, 0, 27710, 1024, UNLOCKED, 1);
// To booth.
door_aot_set(1, 23970, 8670, 1530, 850, 0, 0, 0, 4, 0, ROOM_319, 5185, 0, 4930, 1024, UNLOCKED, 193);
// To east-path.
door_aot_set(2, 27880, 13600, 1020, 3400, 0, 15, 48, 4, 0, ROOM_517, 4420, 0, 12750, 0, UNLOCKED, 1);
// To line-track.
door_aot_set(3, 3400, 10200, 1020, 3400, 0, 15, 48, 4, 0, ROOM_516, 29410, 0, 11900, 2048, UNLOCKED, 1);
// To car.
door_aot_set(4, 12920, 17680, 1700, 1020, 0, 0, 0, 4, 0, ROOM_216, 3485, 0, 2975, 3072, UNLOCKED, 193);
aot_set(5, 26860, 18020, 2040, 2380, SCE_MESSAGE, 129, 129, 0, 255, 0, 0, 0);
aot_set(6, 11900, 17510, 4420, 1190, SCE_MESSAGE, 129, 130, 0, 255, 0, 0, 0);
aot_set(7, 5270, 15980, 4250, 3400, SCE_MESSAGE, 129, 131, 0, 255, 0, 0, 0);
aot_set(8, 18020, 11390, 3060, 2040, SCE_MESSAGE, 129, 132, 0, 255, 0, 0, 0);
aot_set(9, 14450, 3400, 5100, 2040, SCE_MESSAGE, 129, 133, 0, 255, 0, 0, 0);
aot_set(10, 12240, 9860, 3740, 1700, SCE_MESSAGE, 129, 134, 0, 255, 0, 0, 0);
return;

// main procedure 0
if (ck(FG_COMMON, 207, 1)) {
    set(FG_COMMON, 207, 0);
    message(128, 255, 0);
}
return;
