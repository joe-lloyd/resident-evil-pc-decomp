// car (216), written by day/scripts.ts from day/car/scene.py: edit the scene, not this file.
// init procedure 0
// To platform.
door_aot_set(0, 2720, 1700, 1530, 765, 0, 0, 0, 4, 0, ROOM_318, 11730, 0, 16830, 1024, UNLOCKED, 193);
// To pylon.
door_aot_set(1, 4165, 2380, 867, 1020, 0, 0, 0, 4, 0, ROOM_217, 5440, 0, 7905, 0, UNLOCKED, 193);
aot_set(2, 1700, 1700, 1530, 2380, SCE_MESSAGE, 129, 129, 0, 255, 0, 0, 0);
aot_set(3, 3570, 1785, 1445, 935, SCE_MESSAGE, 129, 130, 0, 255, 0, 0, 0);
aot_set(4, 2550, 3230, 1530, 850, SCE_MESSAGE, 129, 131, 0, 255, 0, 0, 0);
aot_set(5, 2720, 1700, 1530, 850, SCE_MESSAGE, 129, 132, 0, 255, 0, 0, 0);
aot_set(6, 4930, 1700, 850, 2380, SCE_MESSAGE, 129, 133, 0, 255, 0, 0, 0);
return;

// main procedure 0
if (ck(FG_COMMON, 243, 1)) {
    set(FG_COMMON, 243, 0);
    message(128, 255, 0);
}
return;
