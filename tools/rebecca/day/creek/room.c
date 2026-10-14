// creek (21C), written by day/scripts.ts from day/creek/scene.py: edit the scene, not this file.
// init procedure 0
// To valley-path.
door_aot_set(0, 15300, 3400, 5100, 1020, 0, 15, 48, 4, 0, ROOM_218, 17000, 0, 26180, 1024, UNLOCKED, 1);
// To lodge.
door_aot_set(1, 10880, 19720, 1020, 1530, 0, 0, 0, 4, 0, ROOM_21D, 7820, 0, 3655, 2048, UNLOCKED, 129);
// To estate-wall.
door_aot_set(2, 18700, 22780, 4250, 1020, 0, 15, 48, 4, 0, ROOM_21E, 20740, 0, 5780, 3072, UNLOCKED, 1);
aot_set(3, 10880, 19210, 1360, 2550, SCE_MESSAGE, 129, 129, 0, 255, 0, 0, 0);
aot_set(4, 5780, 16150, 2380, 1190, SCE_MESSAGE, 129, 130, 0, 255, 0, 0, 0);
aot_set(5, 22100, 10200, 4080, 1700, SCE_MESSAGE, 129, 131, 0, 255, 0, 0, 0);
aot_set(6, 11220, 22780, 2720, 1020, SCE_MESSAGE, 129, 132, 0, 255, 0, 0, 0);
aot_set(7, 17340, 16150, 2720, 1870, SCE_MESSAGE, 129, 133, 0, 255, 0, 0, 0);
aot_set(8, 16320, 9010, 2040, 1700, SCE_MESSAGE, 129, 134, 0, 255, 0, 0, 0);
aot_set(9, 10200, 15810, 2380, 1870, SCE_MESSAGE, 129, 135, 0, 255, 0, 0, 0);
return;

// main procedure 0
if (ck(FG_COMMON, 249, 1)) {
    set(FG_COMMON, 249, 0);
    message(128, 255, 0);
}
return;
