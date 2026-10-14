// office (412), written by day/scripts.ts from day/office/scene.py: edit the scene, not this file.
// init procedure 0
// To camp-yard.
door_aot_set(0, 4250, 5950, 1530, 850, 0, 0, 0, 4, 0, ROOM_31E, 5015, 0, 7990, 3072, UNLOCKED, 193);
aot_set(1, 3400, 2040, 935, 2040, SCE_MESSAGE, 129, 129, 0, 255, 0, 0, 0);
aot_set(2, 5610, 4607, 1190, 748, SCE_MESSAGE, 129, 130, 0, 255, 0, 0, 0);
aot_set(3, 4250, 4607, 1360, 748, SCE_MESSAGE, 129, 131, 0, 255, 0, 0, 0);
aot_set(4, 1870, 4930, 1530, 595, SCE_MESSAGE, 129, 132, 0, 255, 0, 0, 0);
aot_set(5, 1700, 4080, 1020, 1530, SCE_MESSAGE, 129, 133, 0, 255, 0, 0, 0);
aot_set(6, 6800, 5100, 1020, 1360, SCE_MESSAGE, 129, 134, 0, 255, 0, 0, 0);
aot_set(7, 6120, 2635, 1700, 1105, SCE_MESSAGE, 129, 135, 0, 255, 0, 0, 0);
return;

// main procedure 0
if (ck(FG_COMMON, 215, 1)) {
    set(FG_COMMON, 215, 0);
    message(128, 255, 0);
}
return;
