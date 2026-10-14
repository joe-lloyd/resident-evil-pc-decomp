// lower-station (21A), written by day/scripts.ts from day/lower-station/scene.py: edit the scene, not this file.
// init procedure 0
// To lower-yard.
door_aot_set(0, 1700, 4420, 765, 1700, 0, 0, 0, 4, 0, ROOM_219, 20230, 0, 9350, 2048, UNLOCKED, 193);
aot_set(1, 6800, 5865, 1190, 1020, SCE_MESSAGE, 129, 129, 0, 255, 0, 0, 0);
aot_set(2, 8755, 5865, 765, 1020, SCE_MESSAGE, 129, 130, 0, 255, 0, 0, 0);
aot_set(3, 3060, 3400, 3740, 1020, SCE_MESSAGE, 129, 131, 0, 255, 0, 0, 0);
aot_set(4, 1700, 2210, 1190, 1700, SCE_MESSAGE, 129, 132, 0, 255, 0, 0, 0);
aot_set(5, 8500, 2550, 1020, 2040, SCE_MESSAGE, 129, 133, 0, 255, 0, 0, 0);
aot_set(6, 1700, 1700, 1360, 850, SCE_MESSAGE, 129, 134, 0, 255, 0, 0, 0);
aot_set(7, 8670, 5440, 850, 1190, SCE_MESSAGE, 129, 135, 0, 255, 0, 0, 0);
aot_set(8, 5440, 7650, 1360, 850, SCE_MESSAGE, 129, 136, 0, 255, 0, 0, 0);
aot_set(9, 7990, 5865, 765, 1020, SCE_MESSAGE, 129, 137, 0, 255, 0, 0, 0);
return;

// main procedure 0
if (ck(FG_COMMON, 247, 1)) {
    set(FG_COMMON, 247, 0);
    message(128, 255, 0);
}
return;
