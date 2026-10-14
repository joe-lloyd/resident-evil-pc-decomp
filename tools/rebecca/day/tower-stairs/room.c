// tower-stairs (41D), written by day/scripts.ts from day/tower-stairs/scene.py: edit the scene, not this file.
// init procedure 0
// To tower-foot.
door_aot_set(0, 11050, 8670, 1190, 1530, 0, 15, 48, 4, 0, ROOM_41C, 8160, 0, 11985, 2048, UNLOCKED, 1);
// To tower-top.
door_aot_set(1, 11050, 6800, 1190, 1530, 0, 15, 48, 4, 0, ROOM_41E, 6970, 0, 11475, 3072, UNLOCKED, 1);
aot_set(2, 5780, 4590, 2210, 2040, SCE_MESSAGE, 129, 129, 0, 255, 0, 0, 0);
aot_set(3, 3627, 7480, 1190, 1870, SCE_MESSAGE, 129, 130, 0, 255, 0, 0, 0);
aot_set(4, 12183, 10200, 1190, 2720, SCE_MESSAGE, 129, 131, 0, 255, 0, 0, 0);
aot_set(5, 3627, 3627, 9746, 1020, SCE_MESSAGE, 129, 132, 0, 255, 0, 0, 0);
return;

// main procedure 0
if (ck(FG_COMMON, 226, 1)) {
    set(FG_COMMON, 226, 0);
    message(128, 255, 0);
}
return;
