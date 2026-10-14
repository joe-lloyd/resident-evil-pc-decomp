// depot (414), written by day/scripts.ts from day/depot/scene.py: edit the scene, not this file.
// init procedure 0
// To camp-yard.
door_aot_set(0, 9520, 1700, 3060, 1020, 0, 15, 48, 4, 0, ROOM_31E, 5950, 0, 23290, 1024, UNLOCKED, 1);
aot_set(1, 12920, 6460, 1700, 1020, SCE_MESSAGE, 129, 129, 0, 255, 0, 0, 0);
aot_set(2, 10710, 6630, 1700, 935, SCE_MESSAGE, 129, 130, 0, 255, 0, 0, 0);
aot_set(3, 13770, 4420, 680, 2380, SCE_MESSAGE, 129, 131, 0, 255, 0, 0, 0);
aot_set(4, 6630, 3400, 1530, 1360, SCE_MESSAGE, 129, 132, 0, 255, 0, 0, 0);
aot_set(5, 2040, 7820, 2380, 680, SCE_MESSAGE, 129, 133, 0, 255, 0, 0, 0);
return;

// main procedure 0
if (ck(FG_COMMON, 217, 1)) {
    set(FG_COMMON, 217, 0);
    message(128, 255, 0);
}
return;
