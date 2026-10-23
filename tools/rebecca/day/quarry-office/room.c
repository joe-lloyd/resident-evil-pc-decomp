// quarry-office (51A), written by day/scripts.ts from day/quarry-office/scene.py: edit the scene, not this file.
// init procedure 0
// To quarry.
door_aot_set(0, 3868, 1190, 2082, 1360, 0, 1, 8, 0, 0, ROOM_519, 6375, 0, 19040, 1024, UNLOCKED, 193);
if (ck(FG_ITEM, 166, 0)) {  // dynamite (dynamite)
    item_aot_set(1, 2191, 4350, 1500, 1500, 42, 1, 1, 255, 125, 11, 0, 0, 236, 19, 0, 0, 166, 129, 0, 0);
}
if (ck(FG_ITEM, 191, 0)) {  // greenHerb
    item_aot_set(2, 2670, 5050, 1200, 1200, 68, 1, 0, 255, 198, 12, 0, 0, 18, 22, 0, 0, 191, 129, 1, 0);
}
aot_set(3, 1190, 4165, 2125, 2295, SCE_MESSAGE, 129, 129, 0, 255, 0, 0, 0);
aot_set(4, 1190, 2550, 1870, 1615, SCE_MESSAGE, 129, 130, 0, 255, 0, 0, 0);
aot_set(5, 2040, 1700, 1827, 1020, SCE_MESSAGE, 129, 131, 0, 255, 0, 0, 0);
aot_set(6, 4760, 2805, 2074, 1445, SCE_MESSAGE, 129, 132, 0, 255, 0, 0, 0);
// Quarry rosters, a file.
if (ck(FG_ITEM, 236, 0)) {
    item_aot_set(7, 5270, 4250, 1054, 1190, 104, 1, 2, 255, 0, 0, 0, 0, 0, 0, 0, 0, 236, 129, 0, 0);
}
aot_set(8, 6120, 5270, 1870, 1700, SCE_MESSAGE, 129, 133, 0, 255, 0, 0, 0);
aot_set(9, 3315, 5525, 1955, 1445, SCE_MESSAGE, 129, 134, 0, 255, 0, 0, 0);
return;

// main procedure 0
return;
