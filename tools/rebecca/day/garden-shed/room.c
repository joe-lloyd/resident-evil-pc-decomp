// garden-shed (119), written by day/scripts.ts from day/garden-shed/scene.py: edit the scene, not this file.
// init procedure 0
// To back-garden.
door_aot_set(0, 1700, 3570, 850, 1360, 0, 0, 0, 4, 0, ROOM_110, 23800, 0, 8500, 2048, UNLOCKED, 193);
aot_set(1, 2210, 1700, 1530, 1020, SCE_MESSAGE, 129, 129, 0, 255, 0, 0, 0);
aot_set(2, 4250, 1700, 850, 1020, SCE_MESSAGE, 129, 130, 0, 255, 0, 0, 0);
aot_set(3, 5270, 2380, 1190, 1360, SCE_MESSAGE, 129, 131, 0, 255, 0, 0, 0);
aot_set(4, 3060, 4590, 1360, 1020, SCE_MESSAGE, 129, 132, 0, 255, 0, 0, 0);
aot_set(5, 4420, 4930, 2040, 1530, SCE_MESSAGE, 129, 133, 0, 255, 0, 0, 0);
aot_set(6, 2210, 5440, 2720, 1020, SCE_MESSAGE, 129, 134, 0, 255, 0, 0, 0);
return;

// main procedure 0
if (ck(FG_COMMON, 254, 1)) {
    set(FG_COMMON, 254, 0);
    message(128, 255, 0);
}
return;
