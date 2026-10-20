// mast (215), written by day/scripts.ts from day/mast/scene.py: edit the scene, not this file.
// init procedure 0
// To summit-trail.
door_aot_set(0, 12240, 31280, 4080, 1020, 0, 15, 48, 4, 0, ROOM_213, 17000, 0, 4760, 3072, UNLOCKED, 1);
aot_set(1, 5780, 10540, 4420, 3060, SCE_MESSAGE, 129, 129, 0, 255, 0, 0, 0);
aot_set(2, 6800, 13600, 3060, 2040, SCE_MESSAGE, 129, 130, 0, 255, 0, 0, 0);
aot_set(3, 27030, 11220, 1445, 3060, SCE_MESSAGE, 129, 131, 0, 255, 0, 0, 0);
aot_set(4, 4080, 10880, 3060, 2720, SCE_MESSAGE, 129, 132, 0, 255, 0, 0, 0);
aot_set(5, 15980, 12410, 2040, 1190, SCE_MESSAGE, 129, 133, 0, 255, 0, 0, 0);
aot_set(6, 3570, 7140, 4420, 1020, SCE_MESSAGE, 129, 134, 0, 255, 0, 0, 0);
aot_set(7, 14110, 26010, 1020, 1360, SCE_MESSAGE, 129, 135, 0, 255, 0, 0, 0);
aot_set(8, 15300, 29240, 1020, 1700, SCE_MESSAGE, 129, 136, 0, 255, 0, 0, 0);
if (ck(FG_ITEM, 193, 0)) {  // greenHerb
    item_aot_set(9, 26960, 1800, 1200, 1200, 68, 1, 0, 255, 168, 107, 0, 0, 96, 9, 0, 0, 193, 129, 1, 0);
}
if (ck(FG_ITEM, 194, 0)) {  // clip
    item_aot_set(10, 25260, 1800, 1200, 1200, 11, 15, 1, 255, 4, 101, 0, 0, 96, 9, 0, 0, 194, 129, 0, 0);
}
if (ck(FG_ITEM, 195, 0)) {  // spray
    item_aot_set(11, 23560, 1800, 1200, 1200, 65, 1, 2, 255, 96, 94, 0, 0, 96, 9, 0, 0, 195, 129, 0, 0);
}
return;

// main procedure 0
return;
