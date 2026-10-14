// weather (214), written by day/scripts.ts from day/weather/scene.py: edit the scene, not this file.
// init procedure 0
// To summit-trail.
door_aot_set(0, 4250, 6120, 1530, 680, 0, 0, 0, 4, 0, ROOM_213, 6205, 0, 12240, 3072, UNLOCKED, 129);
aot_set(1, 6885, 4420, 1275, 1190, SCE_MESSAGE, 129, 129, 0, 255, 0, 0, 0);
aot_set(2, 6885, 3060, 1275, 1360, SCE_MESSAGE, 129, 130, 0, 255, 0, 0, 0);
aot_set(3, 2720, 1700, 1530, 1105, SCE_MESSAGE, 129, 131, 0, 255, 0, 0, 0);
aot_set(4, 1700, 3060, 1530, 2550, SCE_MESSAGE, 129, 132, 0, 255, 0, 0, 0);
aot_set(5, 2040, 5950, 1870, 850, SCE_MESSAGE, 129, 133, 0, 255, 0, 0, 0);
aot_set(6, 5610, 3230, 1360, 1190, SCE_MESSAGE, 129, 134, 0, 255, 0, 0, 0);
aot_set(7, 6630, 5950, 1530, 850, SCE_MESSAGE, 129, 135, 0, 255, 0, 0, 0);
return;

// main procedure 0
if (ck(FG_COMMON, 241, 1)) {
    set(FG_COMMON, 241, 0);
    message(128, 255, 0);
}
return;
