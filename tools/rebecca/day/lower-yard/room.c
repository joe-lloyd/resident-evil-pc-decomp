// lower-yard (219), written by day/scripts.ts from day/lower-yard/scene.py: edit the scene, not this file.
// init procedure 0
// To valley-path.
door_aot_set(0, 1700, 12750, 1020, 4250, 0, 15, 48, 4, 0, ROOM_218, 29580, 0, 15300, 2048, UNLOCKED, 1);
// To lower-station.
door_aot_set(1, 21930, 8500, 1020, 1700, 0, 0, 0, 4, 0, ROOM_21A, 3230, 0, 5270, 0, UNLOCKED, 193);
aot_set(2, 7473, 21764, 3230, 2210, SCE_MESSAGE, 129, 129, 0, 255, 0, 0, 0);
aot_set(3, 15130, 14110, 1190, 2380, SCE_MESSAGE, 129, 130, 0, 255, 0, 0, 0);
aot_set(4, 12580, 9860, 3060, 2040, SCE_MESSAGE, 129, 131, 0, 255, 0, 0, 0);
aot_set(5, 21590, 13430, 1360, 1870, SCE_MESSAGE, 129, 132, 0, 255, 0, 0, 0);
aot_set(6, 3400, 11050, 2720, 1360, SCE_MESSAGE, 129, 133, 0, 255, 0, 0, 0);
aot_set(7, 21590, 6120, 1360, 2040, SCE_MESSAGE, 129, 134, 0, 255, 0, 0, 0);
aot_set(8, 15300, 3060, 2040, 2040, SCE_MESSAGE, 129, 135, 0, 255, 0, 0, 0);
return;

// main procedure 0
if (ck(FG_COMMON, 246, 1)) {
    set(FG_COMMON, 246, 0);
    message(128, 255, 0);
}
return;
