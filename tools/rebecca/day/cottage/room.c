// cottage (518), written by day/scripts.ts from day/cottage/scene.py: edit the scene, not this file.
// init procedure 0
// To east-path.
door_aot_set(0, 4420, 6630, 1530, 850, 1, 0, 33, 1, 0, ROOM_517, 15385, 0, 9690, 3072, UNLOCKED, 193);
// Hal's diary, a file.
if (ck(FG_ITEM, 235, 0)) {
    item_aot_set(1, 4080, 3570, 1530, 1445, 96, 1, 1, 255, 0, 0, 0, 0, 0, 0, 0, 0, 235, 129, 0, 0);
}
aot_set(2, 5610, 3570, 510, 1445, SCE_MESSAGE, 129, 129, 0, 255, 0, 0, 0);
aot_set(3, 3145, 6630, 1275, 850, SCE_MESSAGE, 129, 130, 0, 255, 0, 0, 0);
aot_set(4, 6545, 1700, 1785, 1700, SCE_MESSAGE, 129, 131, 0, 255, 0, 0, 0);
aot_set(5, 3995, 1700, 1700, 1530, SCE_MESSAGE, 129, 132, 0, 255, 0, 0, 0);
aot_set(6, 3400, 1700, 595, 1530, SCE_MESSAGE, 129, 133, 0, 255, 0, 0, 0);
aot_set(7, 2380, 5780, 1700, 1700, SCE_MESSAGE, 129, 134, 0, 255, 0, 0, 0);
aot_set(8, 1700, 1700, 2040, 3570, SCE_MESSAGE, 129, 135, 0, 255, 0, 0, 0);
aot_set(9, 5950, 6460, 3230, 1020, SCE_MESSAGE, 129, 136, 0, 255, 0, 0, 0);
if (ck(FG_ITEM, 165, 0)) {  // quarry key (quarry-key)
    item_aot_set(10, 2755, 6444, 1800, 1800, 60, 1, 0, 255, 71, 14, 180, 246, 176, 28, 0, 0, 165, 129, 0, 0);
}
return;

// main procedure 0
if (ck(FG_COMMON, 231, 1)) {
    set(FG_COMMON, 231, 0);
    message(128, 255, 0);
}
return;
