// office (412), written by day/scripts.ts from day/office/scene.py: edit the scene, not this file.
// init procedure 0
// To camp-yard.
door_aot_set(0, 4250, 5950, 1530, 850, 1, 0, 33, 1, 0, ROOM_31E, 5015, 0, 7990, 3072, UNLOCKED, 193);
// The typewriter and the item box, its lid on the body the scene paints.
aot_set(1, 3400, 5355, 765, 1445, SCE_TYPEWRITER, 129, 0, 0, 0, 0, 0, 0);
aot_set(2, 6120, 5440, 1700, 1360, SCE_ITEMBOX, 129, 0, 0, 0, 0, 0, 0);
obj(0, 17, 255, 7801, -1152, 5720, 2048, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0);
if (ck(FG_ITEM, 161, 0)) {  // workshop key (safe)
    item_aot_set(3, 1780, 4500, 1200, 1200, 59, 1, 2, 255, 76, 9, 0, 0, 236, 19, 0, 0, 161, 129, 0, 0);
}
aot_set(4, 3400, 2040, 935, 2040, SCE_MESSAGE, 129, 129, 0, 255, 0, 0, 0);
// Foreman's letters, a file.
if (ck(FG_ITEM, 233, 0)) {
    item_aot_set(5, 5610, 4607, 1190, 748, 97, 1, 3, 255, 0, 0, 0, 0, 0, 0, 0, 0, 233, 129, 0, 0);
}
aot_set(6, 4250, 4607, 1360, 748, SCE_MESSAGE, 129, 130, 0, 255, 0, 0, 0);
aot_set(7, 1870, 4930, 1530, 595, SCE_MESSAGE, 129, 131, 0, 255, 0, 0, 0);
aot_set(8, 1700, 4080, 1020, 1530, SCE_MESSAGE, 129, 132, 0, 255, 0, 0, 0);
aot_set(9, 6120, 2635, 1700, 1105, SCE_MESSAGE, 129, 133, 0, 255, 0, 0, 0);
if (ck(FG_ITEM, 183, 0)) {  // spray
    item_aot_set(10, 3160, 1800, 1200, 1200, 65, 1, 0, 255, 176, 14, 0, 0, 96, 9, 0, 0, 183, 129, 0, 0);
}
if (ck(FG_ITEM, 184, 0)) {  // ribbons
    item_aot_set(11, 1800, 3500, 1200, 1200, 47, 3, 1, 255, 96, 9, 0, 0, 4, 16, 0, 0, 184, 129, 0, 0);
}
return;

// main procedure 0
if (ck(FG_COMMON, 215, 1)) {
    set(FG_COMMON, 215, 0);
    message(128, 255, 0);
}
return;
