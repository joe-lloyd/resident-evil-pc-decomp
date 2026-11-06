// garden-shed (119), written by day/scripts.ts from day/garden-shed/scene.py: edit the scene, not this file.
// init procedure 0
// To back-garden.
door_aot_set(0, 1190, 3145, 1615, 2040, 1, 0, 7, 1, 0, ROOM_110, 23800, 0, 8500, 2048, UNLOCKED, 193);
if (ck(FG_ITEM, 171, 0)) {  // cellar key (cellar-key)
    item_aot_set(1, 2225, 1086, 1500, 2067, 53, 1, 0, 255, 159, 11, 180, 246, 44, 7, 0, 0, 171, 129, 0, 0);
}
if (ck(FG_ITEM, 172, 0)) {  // dog meat (dog-meat)
    item_aot_set(2, 1494, 4605, 1915, 1500, 36, 1, 1, 255, 196, 8, 174, 252, 235, 20, 0, 0, 172, 129, 0, 0);
}
aot_set(3, 1700, 1190, 2295, 1955, SCE_MESSAGE, 129, 129, 0, 255, 0, 0, 0);
aot_set(4, 3995, 1190, 1190, 1530, SCE_MESSAGE, 129, 130, 0, 255, 0, 0, 0);
aot_set(5, 5185, 2380, 1785, 1870, SCE_MESSAGE, 129, 131, 0, 255, 0, 0, 0);
aot_set(6, 3060, 4080, 1360, 1530, SCE_MESSAGE, 129, 132, 0, 255, 0, 0, 0);
aot_set(7, 4420, 4930, 2550, 1530, SCE_MESSAGE, 129, 133, 0, 255, 0, 0, 0);
aot_set(8, 1700, 5440, 3230, 1530, SCE_MESSAGE, 129, 134, 0, 255, 0, 0, 0);
return;

// main procedure 0
return;
