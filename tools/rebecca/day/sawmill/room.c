// sawmill (416), written by day/scripts.ts from day/sawmill/scene.py: edit the scene, not this file.
// init procedure 0
// To camp-yard.
door_aot_set(0, 1700, 10200, 1190, 5100, 0, 0, 0, 4, 0, ROOM_31E, 28730, 0, 12750, 2048, UNLOCKED, 129);
// To pond.
door_aot_set(1, 22780, 16320, 1020, 1700, 0, 0, 0, 4, 0, ROOM_417, 4420, 0, 17170, 0, UNLOCKED, 129);
aot_set(2, 12920, 11900, 4420, 1360, SCE_MESSAGE, 129, 129, 0, 255, 0, 0, 0);
aot_set(3, 13940, 12070, 6800, 1190, SCE_MESSAGE, 129, 130, 0, 255, 0, 0, 0);
aot_set(4, 11900, 11220, 1700, 1020, SCE_MESSAGE, 129, 131, 0, 255, 0, 0, 0);
aot_set(5, 19720, 8840, 3400, 1700, SCE_MESSAGE, 129, 132, 0, 255, 0, 0, 0);
aot_set(6, 7650, 8670, 3060, 1360, SCE_MESSAGE, 129, 133, 0, 255, 0, 0, 0);
aot_set(7, 22100, 15470, 1700, 850, SCE_MESSAGE, 129, 134, 0, 255, 0, 0, 0);
aot_set(8, 10880, 19720, 2040, 1020, SCE_MESSAGE, 129, 135, 0, 255, 0, 0, 0);
return;

// main procedure 0
if (ck(FG_COMMON, 219, 1)) {
    set(FG_COMMON, 219, 0);
    message(128, 255, 0);
}
return;
