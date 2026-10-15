// lodge (21D), written by day/scripts.ts from day/lodge/scene.py: edit the scene, not this file.
// init procedure 0
// To creek.
door_aot_set(0, 8330, 2890, 850, 1530, 1, 0, 33, 1, 0, ROOM_21C, 12750, 0, 20485, 0, UNLOCKED, 193);
// The typewriter and the item box, its lid on the body the scene paints.
aot_set(1, 5525, 1700, 1275, 1275, SCE_TYPEWRITER, 129, 0, 0, 0, 0, 0, 0);
aot_set(2, 3315, 5865, 2074, 1955, SCE_ITEMBOX, 129, 0, 0, 0, 0, 0, 0);
obj(0, 17, 255, 4310, -1440, 7809, 1024, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0);
// Gardener's diary, a file.
if (ck(FG_ITEM, 239, 0)) {
    item_aot_set(3, 3400, 3400, 1190, 1360, 100, 1, 4, 255, 0, 0, 0, 0, 0, 0, 0, 0, 239, 129, 0, 0);
}
aot_set(4, 4590, 3400, 1020, 1360, SCE_MESSAGE, 129, 129, 0, 255, 0, 0, 0);
aot_set(5, 5440, 5355, 3485, 850, SCE_MESSAGE, 129, 130, 0, 255, 0, 0, 0);
aot_set(6, 7480, 1700, 1700, 1190, SCE_MESSAGE, 129, 131, 0, 255, 0, 0, 0);
aot_set(7, 8160, 4930, 1020, 850, SCE_MESSAGE, 129, 132, 0, 255, 0, 0, 0);
aot_set(8, 1700, 2380, 1020, 2720, SCE_MESSAGE, 129, 133, 0, 255, 0, 0, 0);
aot_set(9, 1870, 1700, 2550, 1190, SCE_MESSAGE, 129, 134, 0, 255, 0, 0, 0);
aot_set(10, 6630, 3060, 1700, 1360, SCE_MESSAGE, 129, 135, 0, 255, 0, 0, 0);
if (ck(FG_ITEM, 197, 0)) {  // spray
    item_aot_set(11, 1500, 3880, 1800, 1800, 65, 1, 0, 255, 96, 9, 0, 0, 172, 18, 0, 0, 197, 129, 0, 0);
}
if (ck(FG_ITEM, 198, 0)) {  // redHerb
    item_aot_set(12, 3200, 4560, 1800, 1800, 67, 1, 1, 255, 4, 16, 0, 0, 84, 21, 0, 0, 198, 129, 1, 0);
}
if (ck(FG_ITEM, 199, 0)) {  // ribbons
    item_aot_set(13, 4900, 4560, 1800, 1800, 47, 3, 2, 255, 168, 22, 0, 0, 84, 21, 0, 0, 199, 129, 0, 0);
}
if (ck(FG_ITEM, 169, 0)) {  // gate key (gate-key)
    item_aot_set(14, 8144, 4455, 1800, 1800, 52, 1, 3, 255, 84, 35, 180, 246, 235, 20, 0, 0, 169, 129, 0, 0);
}
return;

// main procedure 0
if (ck(FG_COMMON, 250, 1)) {
    set(FG_COMMON, 250, 0);
    message(128, 255, 0);
}
return;
