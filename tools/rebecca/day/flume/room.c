// flume (418), written by day/scripts.ts from day/flume/scene.py: edit the scene, not this file.
// init procedure 0
// To pond.
door_aot_set(0, 9180, 20060, 3740, 1020, 0, 15, 48, 4, 0, ROOM_417, 6800, 0, 6460, 3072, UNLOCKED, 1);
// To bridge.
if (ck(FG_COMMON, 137, 1)) {
    aot_set(1, 13430, 12580, 1785, 2040, SCE_MESSAGE, 129, 129, 0, 255, 0, 0, 0);
} else {
    door_aot_set(1, 13430, 12580, 1785, 2040, 0, 15, 48, 4, 0, ROOM_317, 14450, 0, 6800, 3072, UNLOCKED, 1);
}
aot_set(2, 13600, 16660, 1700, 1700, SCE_MESSAGE, 129, 130, 0, 255, 0, 0, 0);
aot_set(3, 17000, 10030, 1360, 1700, SCE_MESSAGE, 129, 131, 0, 255, 0, 0, 0);
aot_set(4, 13600, 8500, 1700, 1700, SCE_MESSAGE, 129, 132, 0, 255, 0, 0, 0);
aot_set(5, 11900, 18700, 2040, 1360, SCE_MESSAGE, 129, 133, 0, 255, 0, 0, 0);
aot_set(6, 13600, 3400, 1700, 1700, SCE_MESSAGE, 129, 134, 0, 255, 0, 0, 0);
aot_set(7, 9520, 15300, 2040, 1360, SCE_MESSAGE, 129, 135, 0, 255, 0, 0, 0);
return;

// main procedure 0
if (ck(FG_COMMON, 221, 1)) {
    set(FG_COMMON, 221, 0);
    message(128, 255, 0);
}
return;
