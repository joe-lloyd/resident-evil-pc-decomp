// woods (31A), written by day/scripts.ts from day/woods/scene.py: edit the scene, not this file.
// init procedure 0
// To yard.
door_aot_set(0, 3400, 11900, 1020, 3400, 0, 15, 48, 4, 0, ROOM_315, 27200, 0, 10880, 2048, UNLOCKED, 1);
// To den.
door_aot_set(1, 12750, 3400, 4250, 1020, 0, 15, 48, 4, 0, ROOM_31B, 15130, 0, 18020, 1024, UNLOCKED, 1);
// To logging-road.
door_aot_set(2, 29580, 15300, 1020, 4250, 0, 15, 48, 4, 0, ROOM_31C, 4420, 0, 13940, 0, UNLOCKED, 1);
aot_set(3, 4930, 15300, 2040, 2210, SCE_MESSAGE, 129, 129, 0, 255, 0, 0, 0);
aot_set(4, 4420, 13260, 2210, 2040, SCE_MESSAGE, 129, 130, 0, 255, 0, 0, 0);
aot_set(5, 10030, 10370, 1870, 1700, SCE_MESSAGE, 129, 131, 0, 255, 0, 0, 0);
aot_set(6, 12750, 9180, 1870, 1700, SCE_MESSAGE, 129, 132, 0, 255, 0, 0, 0);
aot_set(7, 11560, 6800, 1870, 1530, SCE_MESSAGE, 129, 133, 0, 255, 0, 0, 0);
aot_set(8, 13260, 5100, 3060, 2720, SCE_MESSAGE, 129, 134, 0, 255, 0, 0, 0);
aot_set(9, 20400, 7820, 3570, 3230, SCE_MESSAGE, 129, 135, 0, 255, 0, 0, 0);
aot_set(10, 28220, 19890, 2380, 2550, SCE_MESSAGE, 129, 136, 0, 255, 0, 0, 0);
enemy(2, 1, 188, 1, 2, 0, 0, 2988, 0, 0, 29600, 0, 4100, 0, 0, 0, 0);  // a cerberus
enemy(2, 1, 189, 1, 2, 0, 0, 1554, 0, 0, 15660, 0, 22800, 1, 0, 0, 0);  // a cerberus
return;

// main procedure 0
if (ck(FG_COMMON, 209, 1)) {
    set(FG_COMMON, 209, 0);
    message(128, 255, 0);
}
return;
