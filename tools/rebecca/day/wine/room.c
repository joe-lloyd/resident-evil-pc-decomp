// wine (11E), written by day/scripts.ts from day/wine/scene.py: edit the scene, not this file.
// init procedure 0
// To cellar.
door_aot_set(0, 1700, 3400, 1020, 2040, 1, 0, 33, 1, 0, ROOM_11D, 13770, 0, 4420, 2048, UNLOCKED, 193);
aot_set(1, 3570, 2312, 1530, 918, SCE_MESSAGE, 129, 129, 0, 255, 0, 0, 0);
aot_set(2, 2813, 2312, 2721, 1853, SCE_MESSAGE, 129, 130, 0, 255, 0, 0, 0);
aot_set(3, 5695, 4590, 1530, 1360, SCE_MESSAGE, 129, 131, 0, 255, 0, 0, 0);
aot_set(4, 3400, 5100, 2210, 1088, SCE_MESSAGE, 129, 132, 0, 255, 0, 0, 0);
aot_set(5, 6460, 2380, 748, 1360, SCE_MESSAGE, 129, 133, 0, 255, 0, 0, 0);
if (ck(FG_ITEM, 204, 0)) {  // spray
    item_aot_set(6, 5880, 2480, 1200, 1200, 65, 1, 0, 255, 80, 25, 0, 0, 8, 12, 0, 0, 204, 129, 0, 0);
}
return;

// main procedure 0
return;
