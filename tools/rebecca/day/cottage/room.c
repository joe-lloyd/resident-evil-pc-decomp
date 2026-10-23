// cottage (518), written by day/scripts.ts from day/cottage/scene.py: edit the scene, not this file.
// init procedure 0
// To east-path.
door_aot_set(0, 4420, 6630, 1530, 1360, 1, 0, 33, 1, 0, ROOM_517, 15385, 0, 9690, 3072, UNLOCKED, 193);
if (ck(FG_ITEM, 165, 0)) {  // quarry key (quarry-key)
    item_aot_set(1, 2905, 6594, 1500, 1500, 60, 1, 1, 255, 71, 14, 180, 246, 176, 28, 0, 0, 165, 129, 0, 0);
}
if (ck(FG_ITEM, 190, 0)) {  // greenHerb
    item_aot_set(2, 7770, 3010, 1200, 1200, 68, 1, 0, 255, 178, 32, 0, 0, 26, 14, 0, 0, 190, 129, 1, 0);
}
// Hal's diary, a file.
if (ck(FG_ITEM, 235, 0)) {
    item_aot_set(3, 4038, 3570, 1572, 1827, 103, 1, 2, 255, 0, 0, 0, 0, 0, 0, 0, 0, 235, 129, 0, 0);
}
aot_set(4, 5610, 3485, 722, 2040, SCE_MESSAGE, 129, 129, 0, 255, 0, 0, 0);
aot_set(5, 3145, 6630, 1275, 1360, SCE_MESSAGE, 129, 130, 0, 255, 0, 0, 0);
aot_set(6, 6333, 1190, 2507, 2295, SCE_MESSAGE, 129, 131, 0, 255, 0, 0, 0);
aot_set(7, 3995, 1190, 1700, 2040, SCE_MESSAGE, 129, 132, 0, 255, 0, 0, 0);
aot_set(8, 3400, 1190, 595, 2040, SCE_MESSAGE, 129, 133, 0, 255, 0, 0, 0);
aot_set(9, 1870, 5525, 2210, 1955, SCE_MESSAGE, 129, 134, 0, 255, 0, 0, 0);
aot_set(10, 1190, 1700, 2550, 3570, SCE_MESSAGE, 129, 135, 0, 255, 0, 0, 0);
aot_set(11, 5950, 5950, 3740, 1530, SCE_MESSAGE, 129, 136, 0, 255, 0, 0, 0);
return;

// main procedure 0
return;
