// office (412), written by day/scripts.ts from day/office/scene.py: edit the scene, not this file.
// init procedure 0
// To camp-yard.
door_aot_set(0, 4250, 5950, 1530, 850, 0, 0, 0, 4, 0, ROOM_31E, 5015, 0, 7990, 3072, UNLOCKED, 193);
// The typewriter and the item box, its lid on the body the scene paints.
aot_set(1, 3060, 5355, 1105, 1445, SCE_TYPEWRITER, 129, 0, 0, 0, 0, 0, 0);
aot_set(2, 5865, 4675, 1955, 2125, SCE_ITEMBOX, 129, 0, 0, 0, 0, 0, 0);
obj(0, 17, 255, 7809, -1440, 5720, 2048, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0);
aot_set(3, 3400, 2040, 935, 2040, SCE_MESSAGE, 129, 129, 0, 255, 0, 0, 0);
aot_set(4, 5610, 4607, 1190, 748, SCE_MESSAGE, 129, 130, 0, 255, 0, 0, 0);
aot_set(5, 4250, 4607, 1360, 748, SCE_MESSAGE, 129, 131, 0, 255, 0, 0, 0);
aot_set(6, 1870, 4930, 1530, 595, SCE_MESSAGE, 129, 132, 0, 255, 0, 0, 0);
aot_set(7, 1700, 4080, 1020, 1530, SCE_MESSAGE, 129, 133, 0, 255, 0, 0, 0);
aot_set(8, 6120, 2635, 1700, 1105, SCE_MESSAGE, 129, 134, 0, 255, 0, 0, 0);
return;

// main procedure 0
if (ck(FG_COMMON, 215, 1)) {
    set(FG_COMMON, 215, 0);
    message(128, 255, 0);
}
return;
