// switch (41F), written by day/scripts.ts from day/switch/scene.py: edit the scene, not this file.
// init procedure 0
// To generator.
door_aot_set(0, 3060, 1700, 1360, 1020, 0, 0, 0, 4, 0, ROOM_41B, 7140, 0, 6120, 1024, UNLOCKED, 129);
// To line-track.
door_aot_set(1, 6800, 3740, 1020, 1530, 0, 0, 0, 4, 0, ROOM_516, 4250, 0, 11305, 0, UNLOCKED, 129);
aot_set(2, 1700, 2040, 1360, 1870, SCE_MESSAGE, 129, 129, 0, 255, 0, 0, 0);
aot_set(3, 1700, 3910, 1360, 850, SCE_MESSAGE, 129, 130, 0, 255, 0, 0, 0);
aot_set(4, 2380, 4250, 1020, 1020, SCE_MESSAGE, 129, 131, 0, 255, 0, 0, 0);
aot_set(5, 4930, 5270, 1700, 1530, SCE_MESSAGE, 129, 132, 0, 255, 0, 0, 0);
aot_set(6, 6800, 3060, 1020, 680, SCE_MESSAGE, 129, 133, 0, 255, 0, 0, 0);
return;

// main procedure 0
if (ck(FG_COMMON, 228, 1)) {
    set(FG_COMMON, 228, 0);
    message(128, 255, 0);
}
return;
