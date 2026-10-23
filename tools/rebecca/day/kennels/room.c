// kennels (21F), written by day/scripts.ts from day/kennels/scene.py: edit the scene, not this file.
// init procedure 0
// To estate-wall.
door_aot_set(0, 15810, 3400, 2380, 1020, 0, 16, 48, 4, 0, ROOM_21E, 17000, 0, 29750, 1024, UNLOCKED, 1);
// To back-garden.
door_aot_set(1, 15300, 22780, 3400, 1020, 0, 15, 48, 4, 0, ROOM_110, 17000, 0, 5780, 3072, UNLOCKED, 1);
if (ck(FG_ITEM, 203, 0)) {  // greenHerb
    item_aot_set(2, 27490, 12870, 1200, 1200, 68, 1, 0, 255, 186, 109, 0, 0, 158, 52, 0, 0, 203, 129, 1, 0);
}
aot_set(3, 11050, 14450, 1530, 3910, SCE_MESSAGE, 129, 129, 0, 255, 0, 0, 0);
aot_set(4, 4590, 13940, 6035, 4420, SCE_MESSAGE, 129, 130, 0, 255, 0, 0, 0);
aot_set(5, 8500, 5780, 2550, 3910, SCE_MESSAGE, 129, 131, 0, 255, 0, 0, 0);
aot_set(6, 11050, 5950, 1020, 16320, SCE_MESSAGE, 129, 132, 0, 255, 0, 0, 0);
aot_set(7, 20230, 7820, 2380, 3570, SCE_MESSAGE, 129, 133, 0, 255, 0, 0, 0);
aot_set(8, 18700, 17510, 4080, 2380, SCE_MESSAGE, 129, 134, 0, 255, 0, 0, 0);
aot_set(9, 12580, 8840, 4080, 5610, SCE_MESSAGE, 129, 135, 0, 255, 0, 0, 0);
enemy(2, 1, 232, 1, 2, 0, 0, 2453, 0, 0, 27900, 0, 13620, 0, 0, 0, 0);  // a cerberus
enemy(2, 1, 233, 1, 2, 0, 0, 4012, 0, 0, 4100, 0, 4100, 1, 0, 0, 0);  // a cerberus
enemy(2, 1, 234, 1, 2, 0, 0, 3786, 0, 0, 6480, 0, 16000, 2, 0, 0, 0);  // a cerberus
return;

// main procedure 0
return;
