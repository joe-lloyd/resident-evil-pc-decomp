// pylon (217), written by day/scripts.ts from day/pylon/scene.py: edit the scene, not this file.
// init procedure 0
// To car.
door_aot_set(0, 3740, 6800, 2720, 850, 0, 11, 27, 64, 0, ROOM_216, 3400, 0, 2975, 2048, UNLOCKED, 193);
// To valley-path.
door_aot_set(1, 11050, 10710, 1700, 1190, 1, 11, 27, 64, 0, ROOM_218, 16320, 0, 6120, 3072, UNLOCKED, 193);
aot_set(2, 12070, 9520, 1190, 1190, SCE_MESSAGE, 129, 129, 0, 255, 0, 0, 0);
aot_set(3, 13770, 6970, 2550, 1870, SCE_MESSAGE, 129, 130, 0, 255, 0, 0, 0);
aot_set(4, 10030, 8840, 2210, 850, SCE_MESSAGE, 129, 131, 0, 255, 0, 0, 0);
aot_set(5, 11050, 10030, 1700, 680, SCE_MESSAGE, 129, 132, 0, 255, 0, 0, 0);
enemy(5, 0, 225, 1, 2, 0, 0, 2266, 0, 0, 17700, 0, 7500, 0, 0, 0, 0);  // a crow
enemy(5, 0, 226, 1, 2, 0, 0, 2125, 0, 0, 8860, 0, 7500, 1, 0, 0, 0);  // a crow
return;

// main procedure 0
if (ck(FG_COMMON, 244, 1)) {
    set(FG_COMMON, 244, 0);
    message(128, 255, 0);
}
return;
