// office (412), written by day/scripts.ts from day/office/scene.py: edit the scene, not this file.
// init procedure 0
// To camp-yard.
door_aot_set(0, 3825, 5653, 2465, 1657, 1, 0, 33, 1, 0, ROOM_31E, 5015, 0, 7990, 3072, UNLOCKED, 193);
// The typewriter and the item box, its lid on the body the scene paints.
aot_set(1, 3400, 5355, 765, 1445, SCE_TYPEWRITER, 129, 0, 0, 0, 0, 0, 0);
aot_set(2, 5950, 5389, 1292, 1411, SCE_ITEMBOX, 129, 0, 0, 0, 0, 0, 0);
obj(0, 17, 255, 6596, -864, 6798, 1024, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0);
if (ck(FG_ITEM, 161, 0)) {  // workshop key (safe)
    item_aot_set(3, 1630, 4350, 1500, 1500, 59, 1, 2, 255, 76, 9, 0, 0, 236, 19, 0, 0, 161, 129, 0, 0);
}
if (ck(FG_ITEM, 183, 0)) {  // spray
    item_aot_set(4, 6410, 4710, 1200, 1200, 65, 1, 0, 255, 98, 27, 0, 0, 190, 20, 0, 0, 183, 129, 0, 0);
}
if (ck(FG_ITEM, 184, 0)) {  // ribbons
    item_aot_set(5, 3350, 1990, 1200, 1200, 47, 3, 1, 255, 110, 15, 0, 0, 30, 10, 0, 0, 184, 129, 0, 0);
}
aot_set(6, 3060, 1530, 1785, 2813, SCE_MESSAGE, 129, 129, 0, 255, 0, 0, 0);
// Foreman's letters, a file.
if (ck(FG_ITEM, 233, 0)) {
    item_aot_set(7, 5610, 4174, 1700, 1478, 97, 1, 3, 255, 0, 0, 0, 0, 0, 0, 0, 0, 233, 129, 0, 0);
}
aot_set(8, 3825, 4344, 1785, 1308, SCE_MESSAGE, 129, 130, 0, 255, 0, 0, 0);
aot_set(9, 1870, 4930, 1955, 1105, SCE_MESSAGE, 129, 131, 0, 255, 0, 0, 0);
aot_set(10, 1190, 3570, 1530, 2040, SCE_MESSAGE, 129, 132, 0, 255, 0, 0, 0);
aot_set(11, 5610, 2125, 2720, 2048, SCE_MESSAGE, 129, 133, 0, 255, 0, 0, 0);
return;

// main procedure 0
return;
