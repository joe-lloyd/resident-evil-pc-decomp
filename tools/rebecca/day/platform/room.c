// platform (318), written by day/scripts.ts from day/platform/scene.py: edit the scene, not this file.
// init procedure 0
// To bridge.
door_aot_set(0, 2720, 3400, 5100, 1020, 0, 15, 48, 4, 0, ROOM_317, 10200, 0, 27710, 1024, UNLOCKED, 1);
// To booth.
door_aot_set(1, 21590, 8670, 1530, 850, 0, 0, 0, 4, 0, ROOM_319, 5185, 0, 4930, 1024, UNLOCKED, 193);
// To east-path.
door_aot_set(2, 31280, 14620, 1020, 3740, 0, 15, 48, 4, 0, ROOM_517, 4420, 0, 12750, 0, UNLOCKED, 1);
// To line-track.
door_aot_set(3, 1020, 10200, 1020, 3400, 0, 15, 48, 4, 0, ROOM_516, 29410, 0, 11900, 2048, UNLOCKED, 1);
// To car.
door_aot_set(4, 10540, 17680, 1700, 1020, 0, 0, 0, 4, 0, ROOM_216, 3485, 0, 2975, 3072, UNLOCKED, 193);
aot_set(5, 24480, 18020, 2040, 2380, SCE_MESSAGE, 129, 129, 0, 255, 0, 0, 0);
aot_set(6, 9520, 17510, 4420, 1190, SCE_MESSAGE, 129, 130, 0, 255, 0, 0, 0);
aot_set(7, 2890, 15980, 4250, 3400, SCE_MESSAGE, 129, 131, 0, 255, 0, 0, 0);
aot_set(8, 15640, 11390, 3060, 2040, SCE_MESSAGE, 129, 132, 0, 255, 0, 0, 0);
aot_set(9, 12070, 3400, 5100, 2040, SCE_MESSAGE, 129, 133, 0, 255, 0, 0, 0);
aot_set(10, 9860, 9860, 3740, 1700, SCE_MESSAGE, 129, 134, 0, 255, 0, 0, 0);
aot_set(11, 30600, 17340, 680, 1020, SCE_MESSAGE, 129, 135, 0, 255, 0, 0, 0);
return;

// main procedure 0
if (ck(FG_COMMON, 207, 1)) {
    set(FG_COMMON, 207, 0);
    message(128, 255, 0);
}
return;
