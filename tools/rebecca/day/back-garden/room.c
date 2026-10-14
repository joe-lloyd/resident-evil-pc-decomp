// back-garden (110), written by day/scripts.ts from day/back-garden/scene.py: edit the scene, not this file.
// init procedure 0
// To kennels.
door_aot_set(0, 15300, 3400, 3400, 1020, 0, 15, 48, 4, 0, ROOM_21F, 17000, 0, 21420, 1024, UNLOCKED, 1);
// To garden-shed.
door_aot_set(1, 24820, 7820, 1020, 1360, 0, 0, 0, 4, 0, ROOM_119, 2975, 0, 4250, 0, UNLOCKED, 129);
// To cellar.
door_aot_set(2, 20400, 20400, 2720, 1020, 0, 0, 0, 4, 0, ROOM_11D, 12410, 0, 3230, 3072, UNLOCKED, 129);
aot_set(3, 20400, 20230, 2720, 1190, SCE_MESSAGE, 129, 129, 0, 255, 0, 0, 0);
aot_set(4, 10540, 22100, 2040, 1360, SCE_MESSAGE, 129, 130, 0, 255, 0, 0, 0);
aot_set(5, 5270, 15980, 4250, 2550, SCE_MESSAGE, 129, 131, 0, 255, 0, 0, 0);
aot_set(6, 19040, 20060, 1360, 1360, SCE_MESSAGE, 129, 132, 0, 255, 0, 0, 0);
aot_set(7, 13430, 10030, 7140, 7140, SCE_MESSAGE, 129, 133, 0, 255, 0, 0, 0);
aot_set(8, 20400, 11900, 3740, 3910, SCE_MESSAGE, 129, 134, 0, 255, 0, 0, 0);
aot_set(9, 18360, 21420, 2040, 2040, SCE_MESSAGE, 129, 135, 0, 255, 0, 0, 0);
return;

// main procedure 0
if (ck(FG_COMMON, 253, 1)) {
    set(FG_COMMON, 253, 0);
    message(128, 255, 0);
}
return;
