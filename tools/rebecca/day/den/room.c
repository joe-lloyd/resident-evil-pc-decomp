// den (31B), written by day/scripts.ts from day/den/scene.py: edit the scene, not this file.
// init procedure 0
// To woods.
door_aot_set(0, 12750, 19380, 4250, 1020, 0, 15, 48, 4, 0, ROOM_31A, 15130, 0, 6120, 3072, UNLOCKED, 1);
aot_set(1, 16320, 6460, 3060, 3400, SCE_MESSAGE, 129, 129, 0, 255, 0, 0, 0);
aot_set(2, 12410, 3570, 3570, 2720, SCE_MESSAGE, 129, 130, 0, 255, 0, 0, 0);
aot_set(3, 15980, 5780, 1870, 1360, SCE_MESSAGE, 129, 131, 0, 255, 0, 0, 0);
aot_set(4, 15810, 3400, 1700, 1700, SCE_MESSAGE, 129, 132, 0, 255, 0, 0, 0);
aot_set(5, 22270, 14280, 3230, 3060, SCE_MESSAGE, 129, 133, 0, 255, 0, 0, 0);
aot_set(6, 8160, 7820, 2040, 2040, SCE_MESSAGE, 129, 134, 0, 255, 0, 0, 0);
aot_set(7, 15130, 6120, 1870, 1700, SCE_MESSAGE, 129, 135, 0, 255, 0, 0, 0);
return;

// main procedure 0
if (ck(FG_COMMON, 210, 1)) {
    set(FG_COMMON, 210, 0);
    message(128, 255, 0);
}
return;
