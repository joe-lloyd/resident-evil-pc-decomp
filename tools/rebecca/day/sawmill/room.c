// sawmill (416), written by day/scripts.ts from day/sawmill/scene.py: edit the scene, not this file.
// init procedure 0
// To camp-yard.
door_aot_set(0, 1190, 9690, 2210, 6120, 1, 0, 7, 1, 0, ROOM_31E, 28730, 0, 12750, 2048, UNLOCKED, 193);
// To pond.
door_aot_set(1, 31280, 14960, 1530, 3060, 1, 0, 7, 1, 0, ROOM_417, 4420, 0, 17170, 0, UNLOCKED, 193);
if (ck(FG_ITEM, 189, 0)) {  // clip
    item_aot_set(2, 17630, 4710, 1200, 1200, 11, 15, 0, 255, 54, 71, 0, 0, 190, 20, 0, 0, 189, 129, 0, 0);
}
aot_set(3, 12920, 11900, 4420, 1360, SCE_MESSAGE, 129, 129, 0, 255, 0, 0, 0);
aot_set(4, 13940, 12070, 7310, 1700, SCE_MESSAGE, 129, 130, 0, 255, 0, 0, 0);
aot_set(5, 11390, 10710, 2210, 1530, SCE_MESSAGE, 129, 131, 0, 255, 0, 0, 0);
aot_set(6, 19210, 8330, 4420, 2720, SCE_MESSAGE, 129, 132, 0, 255, 0, 0, 0);
aot_set(7, 21590, 14960, 2677, 1870, SCE_MESSAGE, 129, 133, 0, 255, 0, 0, 0);
aot_set(8, 10370, 19210, 3060, 2040, SCE_MESSAGE, 129, 134, 0, 255, 0, 0, 0);
aot_set(9, 28390, 14110, 3230, 1530, SCE_MESSAGE, 129, 135, 0, 255, 0, 0, 0);
aot_set(10, 24268, 15130, 3442, 2040, SCE_MESSAGE, 129, 136, 0, 255, 0, 0, 0);
aot_set(11, 29750, 17340, 1530, 1530, SCE_MESSAGE, 129, 137, 0, 255, 0, 0, 0);
enemy(17, 0, 205, 1, 2, 0, 0, 2362, 0, 0, 18040, 0, 5460, 0, 0, 0, 0);  // a zombie
enemy(17, 0, 206, 1, 2, 0, 0, 1702, 0, 0, 16000, 0, 19740, 1, 0, 0, 0);  // a zombie
if (ck(FG_COMMON, 137, 0)) {
    enemy(17, 0, 207, 1, 2, 0, 0, 2673, 0, 0, 9200, 0, 5460, 2, 0, 0, 0);  // a zombie
}
return;

// main procedure 0
return;
