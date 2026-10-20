// kennels (21F), written by day/scripts.ts from day/kennels/scene.py: edit the scene, not this file.
// init procedure 0
// To estate-wall.
door_aot_set(0, 15810, 3400, 2380, 1020, 0, 16, 48, 4, 0, ROOM_21E, 17000, 0, 29750, 1024, UNLOCKED, 1);
// To back-garden.
door_aot_set(1, 15300, 22780, 3400, 1020, 0, 15, 48, 4, 0, ROOM_110, 17000, 0, 5780, 3072, UNLOCKED, 1);
aot_set(2, 11050, 14450, 1360, 3400, SCE_MESSAGE, 129, 129, 0, 255, 0, 0, 0);
aot_set(3, 5100, 14450, 5100, 3400, SCE_MESSAGE, 129, 130, 0, 255, 0, 0, 0);
aot_set(4, 9010, 6290, 2040, 3400, SCE_MESSAGE, 129, 131, 0, 255, 0, 0, 0);
aot_set(5, 11050, 5950, 1020, 16320, SCE_MESSAGE, 129, 132, 0, 255, 0, 0, 0);
aot_set(6, 20740, 8330, 1360, 2550, SCE_MESSAGE, 129, 133, 0, 255, 0, 0, 0);
aot_set(7, 19210, 18020, 3060, 1360, SCE_MESSAGE, 129, 134, 0, 255, 0, 0, 0);
aot_set(8, 12750, 9350, 3400, 5100, SCE_MESSAGE, 129, 135, 0, 255, 0, 0, 0);
enemy(2, 1, 232, 1, 2, 0, 0, 2453, 0, 0, 27900, 0, 13620, 0, 0, 0, 0);  // a cerberus
enemy(2, 1, 233, 1, 2, 0, 0, 394, 0, 0, 6140, 0, 13280, 1, 0, 0, 0);  // a cerberus
enemy(2, 1, 234, 1, 2, 0, 0, 2162, 0, 0, 26540, 0, 4100, 2, 0, 0, 0);  // a cerberus
if (ck(FG_ITEM, 203, 0)) {  // greenHerb
    item_aot_set(9, 27300, 13020, 1200, 1200, 68, 1, 0, 255, 252, 108, 0, 0, 52, 53, 0, 0, 203, 129, 1, 0);
}
return;

// main procedure 0
return;
