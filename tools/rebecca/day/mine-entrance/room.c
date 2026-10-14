// mine-entrance (51B), written by day/scripts.ts from day/mine-entrance/scene.py: edit the scene, not this file.
// init procedure 0
// To quarry.
door_aot_set(0, 1700, 10200, 1020, 4080, 0, 15, 48, 4, 0, ROOM_519, 29580, 0, 12580, 2048, UNLOCKED, 1);
// To tunnel.
door_aot_set(1, 13430, 4250, 1700, 1360, 0, 0, 0, 4, 0, ROOM_51C, 8500, 0, 29920, 1024, UNLOCKED, 193);
aot_set(2, 11900, 4250, 1360, 1530, SCE_MESSAGE, 129, 129, 0, 255, 0, 0, 0);
aot_set(3, 15045, 4250, 3655, 3570, SCE_MESSAGE, 129, 130, 0, 255, 0, 0, 0);
aot_set(4, 19550, 14790, 2550, 3910, SCE_MESSAGE, 129, 131, 0, 255, 0, 0, 0);
aot_set(5, 18700, 4250, 2040, 1360, SCE_MESSAGE, 129, 132, 0, 255, 0, 0, 0);
aot_set(6, 18700, 9520, 3060, 3400, SCE_MESSAGE, 129, 133, 0, 255, 0, 0, 0);
return;

// main procedure 0
if (ck(FG_COMMON, 234, 1)) {
    set(FG_COMMON, 234, 0);
    message(128, 255, 0);
}
return;
