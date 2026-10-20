// cottage (518), written by day/scripts.ts from day/cottage/scene.py: edit the scene, not this file.
// init procedure 0
// To east-path.
door_aot_set(0, 4420, 6630, 1530, 850, 1, 0, 33, 1, 0, ROOM_517, 15385, 0, 9690, 3072, UNLOCKED, 193);
if (ck(FG_ITEM, 165, 0)) {  // quarry key (quarry-key)
    item_aot_set(1, 3055, 6744, 1200, 1200, 60, 1, 0, 255, 71, 14, 180, 246, 176, 28, 0, 0, 165, 129, 0, 0);
}
// Hal's diary, a file.
if (ck(FG_ITEM, 235, 0)) {
    item_aot_set(2, 4080, 3570, 1530, 1445, 103, 1, 1, 255, 0, 0, 0, 0, 0, 0, 0, 0, 235, 129, 0, 0);
}
aot_set(3, 5610, 3570, 510, 1445, SCE_MESSAGE, 129, 129, 0, 255, 0, 0, 0);
aot_set(4, 3145, 6630, 1275, 850, SCE_MESSAGE, 129, 130, 0, 255, 0, 0, 0);
aot_set(5, 6545, 1700, 1785, 1700, SCE_MESSAGE, 129, 131, 0, 255, 0, 0, 0);
aot_set(6, 3995, 1700, 1700, 1530, SCE_MESSAGE, 129, 132, 0, 255, 0, 0, 0);
aot_set(7, 3400, 1700, 595, 1530, SCE_MESSAGE, 129, 133, 0, 255, 0, 0, 0);
aot_set(8, 2380, 5780, 1700, 1700, SCE_MESSAGE, 129, 134, 0, 255, 0, 0, 0);
aot_set(9, 1700, 1700, 2040, 3570, SCE_MESSAGE, 129, 135, 0, 255, 0, 0, 0);
aot_set(10, 5950, 6460, 3230, 1020, SCE_MESSAGE, 129, 136, 0, 255, 0, 0, 0);
return;

// main procedure 0
return;
