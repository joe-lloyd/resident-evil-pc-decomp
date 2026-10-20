// quarry-office (51A), written by day/scripts.ts from day/quarry-office/scene.py: edit the scene, not this file.
// init procedure 0
// To quarry.
door_aot_set(0, 3910, 1700, 1530, 850, 0, 1, 8, 0, 0, ROOM_519, 6375, 0, 19040, 1024, UNLOCKED, 193);
if (ck(FG_ITEM, 166, 0)) {  // dynamite (dynamite)
    item_aot_set(1, 2341, 4500, 1200, 1200, 42, 1, 1, 255, 125, 11, 0, 0, 236, 19, 0, 0, 166, 129, 0, 0);
}
aot_set(2, 1700, 4250, 1360, 1700, SCE_MESSAGE, 129, 129, 0, 255, 0, 0, 0);
aot_set(3, 1700, 2550, 1360, 1530, SCE_MESSAGE, 129, 130, 0, 255, 0, 0, 0);
aot_set(4, 2040, 1700, 1785, 1020, SCE_MESSAGE, 129, 131, 0, 255, 0, 0, 0);
aot_set(5, 5270, 3060, 1054, 1190, SCE_MESSAGE, 129, 132, 0, 255, 0, 0, 0);
// Quarry rosters, a file.
if (ck(FG_ITEM, 236, 0)) {
    item_aot_set(6, 5270, 4250, 1054, 1190, 104, 1, 2, 255, 0, 0, 0, 0, 0, 0, 0, 0, 236, 129, 0, 0);
}
aot_set(7, 6120, 5270, 1360, 1190, SCE_MESSAGE, 129, 133, 0, 255, 0, 0, 0);
aot_set(8, 3570, 5610, 1700, 850, SCE_MESSAGE, 129, 134, 0, 255, 0, 0, 0);
if (ck(FG_ITEM, 190, 0)) {  // greenHerb
    item_aot_set(9, 2820, 4860, 1200, 1200, 68, 1, 0, 255, 92, 13, 0, 0, 84, 21, 0, 0, 190, 129, 1, 0);
}
return;

// main procedure 0
return;
