// booth (319), written by day/scripts.ts from day/booth/scene.py: edit the scene, not this file.
// init procedure 0
// To platform.
door_aot_set(0, 4420, 5440, 1530, 680, 0, 0, 0, 4, 0, ROOM_318, 24735, 0, 10710, 3072, UNLOCKED, 193);
aot_set(1, 5100, 1700, 1870, 1190, SCE_MESSAGE, 129, 129, 0, 255, 0, 0, 0);
aot_set(2, 1700, 1870, 1530, 850, SCE_MESSAGE, 129, 130, 0, 255, 0, 0, 0);
aot_set(3, 1700, 4080, 1530, 850, SCE_MESSAGE, 129, 131, 0, 255, 0, 0, 0);
aot_set(4, 3230, 4080, 1360, 1020, SCE_MESSAGE, 129, 132, 0, 255, 0, 0, 0);
aot_set(5, 5950, 2210, 1190, 1105, SCE_MESSAGE, 129, 133, 0, 255, 0, 0, 0);
aot_set(6, 5950, 4165, 1190, 850, SCE_MESSAGE, 129, 134, 0, 255, 0, 0, 0);
aot_set(7, 5950, 5015, 1190, 850, SCE_MESSAGE, 129, 135, 0, 255, 0, 0, 0);
aot_set(8, 3570, 5100, 850, 1020, SCE_MESSAGE, 129, 136, 0, 255, 0, 0, 0);
return;

// main procedure 0
if (ck(FG_COMMON, 208, 1)) {
    set(FG_COMMON, 208, 0);
    message(128, 255, 0);
}
return;
