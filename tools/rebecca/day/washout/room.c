// washout (41A), written by day/scripts.ts from day/washout/scene.py: edit the scene, not this file.
// init procedure 0
// To road.
door_aot_set(0, 31280, 7650, 1020, 6800, 0, 15, 48, 4, 0, ROOM_419, 4420, 0, 11900, 0, UNLOCKED, 1);
// To tower-foot.
door_aot_set(1, 1700, 7820, 1020, 5100, 0, 15, 48, 4, 0, ROOM_41C, 29410, 0, 11900, 2048, UNLOCKED, 1);
// To generator.
door_aot_set(2, 5440, 19890, 2040, 1360, 0, 0, 0, 4, 0, ROOM_41B, 5270, 0, 3400, 3072, UNLOCKED, 193);
aot_set(3, 17680, 9690, 3740, 1020, SCE_MESSAGE, 129, 129, 0, 255, 0, 0, 0);
aot_set(4, 12920, 9690, 4760, 1020, SCE_MESSAGE, 129, 130, 0, 255, 0, 0, 0);
aot_set(5, 14960, 5100, 4080, 1700, SCE_MESSAGE, 129, 131, 0, 255, 0, 0, 0);
aot_set(6, 22440, 8500, 5440, 5100, SCE_MESSAGE, 129, 132, 0, 255, 0, 0, 0);
aot_set(7, 7140, 19040, 3740, 850, SCE_MESSAGE, 129, 133, 0, 255, 0, 0, 0);
aot_set(8, 3060, 15470, 2720, 1700, SCE_MESSAGE, 129, 134, 0, 255, 0, 0, 0);
aot_set(9, 1700, 13090, 2040, 1700, SCE_MESSAGE, 129, 135, 0, 255, 0, 0, 0);
return;

// main procedure 0
if (ck(FG_COMMON, 223, 1)) {
    set(FG_COMMON, 223, 0);
    message(128, 255, 0);
}
return;
