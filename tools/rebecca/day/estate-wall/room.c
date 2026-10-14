// estate-wall (21E), written by day/scripts.ts from day/estate-wall/scene.py: edit the scene, not this file.
// init procedure 0
// To creek.
door_aot_set(0, 18700, 3400, 4250, 1020, 0, 15, 48, 4, 0, ROOM_21C, 20740, 0, 21420, 1024, UNLOCKED, 1);
// To kennels.
door_aot_set(1, 15810, 20060, 2380, 1020, 0, 15, 48, 4, 0, ROOM_21F, 17000, 0, 5780, 3072, UNLOCKED, 1);
aot_set(2, 15810, 19550, 2380, 1530, SCE_MESSAGE, 129, 129, 0, 255, 0, 0, 0);
aot_set(3, 13940, 19890, 1700, 1190, SCE_MESSAGE, 129, 130, 0, 255, 0, 0, 0);
aot_set(4, 15300, 18360, 2720, 1190, SCE_MESSAGE, 129, 131, 0, 255, 0, 0, 0);
aot_set(5, 13770, 17170, 1700, 1700, SCE_MESSAGE, 129, 132, 0, 255, 0, 0, 0);
aot_set(6, 11050, 15300, 3570, 1700, SCE_MESSAGE, 129, 133, 0, 255, 0, 0, 0);
return;

// main procedure 0
if (ck(FG_COMMON, 251, 1)) {
    set(FG_COMMON, 251, 0);
    message(128, 255, 0);
}
return;
