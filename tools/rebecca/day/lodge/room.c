// lodge (21D), written by day/scripts.ts from day/lodge/scene.py: edit the scene, not this file.
// init procedure 0
// To creek.
door_aot_set(0, 8330, 2890, 850, 1530, 0, 0, 0, 4, 0, ROOM_21C, 12750, 0, 20485, 0, UNLOCKED, 129);
aot_set(1, 3400, 3400, 1190, 1360, SCE_MESSAGE, 129, 129, 0, 255, 0, 0, 0);
aot_set(2, 4590, 3400, 1020, 1360, SCE_MESSAGE, 129, 130, 0, 255, 0, 0, 0);
aot_set(3, 5440, 5355, 3485, 850, SCE_MESSAGE, 129, 131, 0, 255, 0, 0, 0);
aot_set(4, 7480, 1700, 1700, 1190, SCE_MESSAGE, 129, 132, 0, 255, 0, 0, 0);
aot_set(5, 8160, 4930, 1020, 850, SCE_MESSAGE, 129, 133, 0, 255, 0, 0, 0);
aot_set(6, 1700, 2380, 1020, 2720, SCE_MESSAGE, 129, 134, 0, 255, 0, 0, 0);
aot_set(7, 1870, 1700, 2550, 1190, SCE_MESSAGE, 129, 135, 0, 255, 0, 0, 0);
aot_set(8, 6630, 3060, 1700, 1360, SCE_MESSAGE, 129, 136, 0, 255, 0, 0, 0);
return;

// main procedure 0
if (ck(FG_COMMON, 250, 1)) {
    set(FG_COMMON, 250, 0);
    message(128, 255, 0);
}
return;
