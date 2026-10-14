// pond (417), written by day/scripts.ts from day/pond/scene.py: edit the scene, not this file.
// init procedure 0
// To sawmill.
door_aot_set(0, 1700, 16320, 1190, 1700, 0, 0, 0, 4, 0, ROOM_416, 21590, 0, 17170, 2048, UNLOCKED, 193);
// To flume.
door_aot_set(1, 5780, 3400, 2040, 1020, 0, 15, 48, 4, 0, ROOM_418, 10880, 0, 18530, 1024, UNLOCKED, 1);
aot_set(2, 13260, 15980, 4080, 1360, SCE_MESSAGE, 129, 129, 0, 255, 0, 0, 0);
aot_set(3, 22100, 15980, 4080, 1360, SCE_MESSAGE, 129, 130, 0, 255, 0, 0, 0);
aot_set(4, 8840, 5100, 2040, 1360, SCE_MESSAGE, 129, 131, 0, 255, 0, 0, 0);
aot_set(5, 4250, 6120, 1700, 3400, SCE_MESSAGE, 129, 132, 0, 255, 0, 0, 0);
aot_set(6, 1700, 15300, 1360, 1020, SCE_MESSAGE, 129, 133, 0, 255, 0, 0, 0);
aot_set(7, 5780, 4420, 2040, 1020, SCE_MESSAGE, 129, 134, 0, 255, 0, 0, 0);
return;

// main procedure 0
if (ck(FG_COMMON, 220, 1)) {
    set(FG_COMMON, 220, 0);
    message(128, 255, 0);
}
return;
