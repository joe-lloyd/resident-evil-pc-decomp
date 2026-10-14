// logging-road (31C), written by day/scripts.ts from day/logging-road/scene.py: edit the scene, not this file.
// init procedure 0
// To woods.
door_aot_set(0, 1700, 10880, 1020, 6120, 0, 15, 48, 4, 0, ROOM_31A, 27880, 0, 17340, 2048, UNLOCKED, 1);
// To camp-gate.
door_aot_set(1, 31280, 10540, 1020, 8160, 0, 15, 48, 4, 0, ROOM_31D, 4420, 0, 16830, 0, UNLOCKED, 1);
// Quarantine notice, a file.
if (ck(FG_ITEM, 231, 0)) {
    item_aot_set(2, 7990, 7480, 2720, 1360, 99, 1, 0, 255, 0, 0, 0, 0, 0, 0, 0, 0, 231, 129, 0, 0);
}
aot_set(3, 21590, 15980, 3400, 1700, SCE_MESSAGE, 129, 129, 0, 255, 0, 0, 0);
aot_set(4, 21760, 16490, 2720, 2210, SCE_MESSAGE, 129, 130, 0, 255, 0, 0, 0);
aot_set(5, 24990, 16320, 1870, 1530, SCE_MESSAGE, 129, 131, 0, 255, 0, 0, 0);
aot_set(6, 26860, 15640, 3060, 1700, SCE_MESSAGE, 129, 132, 0, 255, 0, 0, 0);
aot_set(7, 28050, 11730, 1190, 4420, SCE_MESSAGE, 129, 133, 0, 255, 0, 0, 0);
aot_set(8, 5440, 11900, 1360, 4080, SCE_MESSAGE, 129, 134, 0, 255, 0, 0, 0);
return;

// main procedure 0
if (ck(FG_COMMON, 211, 1)) {
    set(FG_COMMON, 211, 0);
    message(128, 255, 0);
}
return;
