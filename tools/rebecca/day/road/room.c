// road (419), written by day/scripts.ts from day/road/scene.py: edit the scene, not this file.
// init procedure 0
// To yard.
door_aot_set(0, 31280, 8500, 1020, 6800, 0, 15, 48, 4, 0, ROOM_315, 6120, 0, 18360, 0, UNLOCKED, 1);
// To washout.
door_aot_set(1, 1700, 8500, 1020, 6800, 0, 15, 48, 4, 171, ROOM_41A, 29580, 0, 11050, 2048, 28, 193);
aot_set(2, 13260, 7310, 1870, 1700, SCE_MESSAGE, 129, 129, 0, 255, 0, 0, 0);
aot_set(3, 14450, 9350, 1700, 1700, SCE_MESSAGE, 129, 130, 0, 255, 0, 0, 0);
aot_set(4, 12410, 7310, 1190, 1190, SCE_MESSAGE, 129, 131, 0, 255, 0, 0, 0);
aot_set(5, 18700, 5950, 1530, 1700, SCE_MESSAGE, 129, 132, 0, 255, 0, 0, 0);
aot_set(6, 5100, 11560, 2720, 2040, SCE_MESSAGE, 129, 133, 0, 255, 0, 0, 0);
aot_set(7, 21760, 5950, 4760, 11900, SCE_MESSAGE, 129, 134, 0, 255, 0, 0, 0);
aot_set(8, 7820, 16490, 2040, 1360, SCE_MESSAGE, 129, 135, 0, 255, 0, 0, 0);
enemy(5, 0, 204, 1, 2, 0, 0, 3838, 0, 0, 17020, 0, 6650, 0, 0, 0, 0);  // a crow
enemy(5, 0, 205, 1, 2, 0, 0, 313, 0, 0, 20080, 0, 16850, 1, 0, 0, 0);  // a crow
enemy(5, 0, 206, 1, 2, 0, 0, 1757, 0, 0, 11920, 0, 15490, 2, 0, 0, 0);  // a crow
if (ck(FG_ITEM, 250, 0)) {  // the road map (maps/pickups.ts)
    item_aot_set(9, 16120, 5750, 1800, 1800, 80, 1, 0, 255, 124, 66, 0, 0, 250, 25, 0, 0, 250, 129, 0, 0);
}
return;

// main procedure 0
if (ck(FG_COMMON, 222, 1)) {
    set(FG_COMMON, 222, 0);
    message(128, 255, 0);
}
return;
