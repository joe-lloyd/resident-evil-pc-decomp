// booth (319), written by day/scripts.ts from day/booth/scene.py: edit the scene, not this file.
// init procedure 0
// To platform.
door_aot_set(0, 4420, 5440, 1530, 680, 0, 0, 0, 4, 0, ROOM_318, 22355, 0, 10710, 3072, UNLOCKED, 193);
// The typewriter and the item box, its lid on the body the scene paints.
aot_set(1, 3315, 1700, 1020, 1360, SCE_TYPEWRITER, 129, 0, 0, 0, 0, 0, 0);
aot_set(2, 5440, 3349, 1700, 782, SCE_ITEMBOX, 129, 0, 0, 0, 0, 0, 0);
obj(0, 17, 255, 7129, -1440, 3485, 2048, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0);
aot_set(3, 5100, 1700, 1870, 1190, SCE_MESSAGE, 129, 129, 0, 255, 0, 0, 0);
aot_set(4, 1700, 1870, 1530, 850, SCE_MESSAGE, 129, 130, 0, 255, 0, 0, 0);
aot_set(5, 1700, 4080, 1530, 850, SCE_MESSAGE, 129, 131, 0, 255, 0, 0, 0);
aot_set(6, 3230, 4080, 1360, 1020, SCE_MESSAGE, 129, 132, 0, 255, 0, 0, 0);
aot_set(7, 5440, 2210, 1700, 1105, SCE_MESSAGE, 129, 133, 0, 255, 0, 0, 0);
aot_set(8, 5440, 4165, 1700, 850, SCE_MESSAGE, 129, 134, 0, 255, 0, 0, 0);
aot_set(9, 5950, 5015, 1190, 850, SCE_MESSAGE, 129, 135, 0, 255, 0, 0, 0);
aot_set(10, 3570, 5100, 850, 1020, SCE_MESSAGE, 129, 136, 0, 255, 0, 0, 0);
return;

// main procedure 0
if (ck(FG_COMMON, 208, 1)) {
    set(FG_COMMON, 208, 0);
    message(128, 255, 0);
}
return;
