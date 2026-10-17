// road (419), written by day/scripts.ts from day/road/scene.py: edit the scene, not this file.
// init procedure 0
// To yard.
door_aot_set(0, 31280, 8500, 1020, 6800, 0, 15, 48, 4, 0, ROOM_315, 6120, 0, 16600, 0, UNLOCKED, 1);
// To washout.
door_aot_set(1, 14110, 8500, 1020, 6800, 0, 16, 48, 4, 171, ROOM_41A, 29580, 0, 11050, 2048, 28, 193);
if (ck(FG_ITEM, 250, 0)) {  // the road map (maps/pickups.ts)
    item_aot_set(2, 20030, 15950, 1800, 1800, 80, 1, 0, 255, 194, 81, 0, 0, 210, 65, 0, 0, 250, 129, 0, 0);
}
aot_set(3, 14110, 7310, 1530, 1190, SCE_MESSAGE, 129, 129, 0, 255, 0, 0, 0);
aot_set(4, 14450, 9350, 1700, 1700, SCE_MESSAGE, 129, 130, 0, 255, 0, 0, 0);
aot_set(5, 14110, 5950, 1530, 1360, SCE_MESSAGE, 129, 131, 0, 255, 0, 0, 0);
aot_set(6, 18700, 5950, 1530, 1700, SCE_MESSAGE, 129, 132, 0, 255, 0, 0, 0);
aot_set(7, 17340, 11560, 2720, 2040, SCE_MESSAGE, 129, 133, 0, 255, 0, 0, 0);
aot_set(8, 21760, 5950, 4760, 11900, SCE_MESSAGE, 129, 134, 0, 255, 0, 0, 0);
aot_set(9, 15300, 16490, 2040, 1360, SCE_MESSAGE, 129, 135, 0, 255, 0, 0, 0);
enemy(5, 0, 204, 1, 2, 0, 0, 3658, 0, 0, 22970, 0, 6650, 0, 0, 0, 0);  // a crow
enemy(5, 0, 205, 1, 2, 0, 0, 419, 0, 0, 22970, 0, 16850, 1, 0, 0, 0);  // a crow
enemy(5, 0, 206, 1, 2, 0, 0, 2847, 0, 0, 31470, 0, 6650, 2, 0, 0, 0);  // a crow
if (ck(FG_ITEM, 250, 0)) {
    set(FG_ROOM, 12, 0);
}
return;

// main procedure 0
if (ck(FG_COMMON, 222, 1)) {
    set(FG_COMMON, 222, 0);
    message(128, 255, 0);
}
if (ck(FG_ROOM, 12, 0) && ck(FG_ITEM, 250, 1)) {
    set(FG_ROOM, 12, 1);
    message(136, 255, 0);
}
return;
