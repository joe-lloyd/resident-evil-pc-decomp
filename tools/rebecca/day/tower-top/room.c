// tower-top (41E), written by day/scripts.ts from day/tower-top/scene.py: edit the scene, not this file.
// init procedure 0
// To tower-stairs.
door_aot_set(0, 6375, 8500, 1020, 1530, 0, 15, 48, 4, 0, ROOM_41D, 12240, 0, 5270, 1024, UNLOCKED, 1);
aot_set(1, 10200, 10200, 2720, 2720, SCE_MESSAGE, 129, 129, 0, 255, 0, 0, 0);
aot_set(2, 10540, 6290, 1700, 1530, SCE_MESSAGE, 129, 130, 0, 255, 0, 0, 0);
aot_set(3, 12240, 6290, 1870, 1530, SCE_MESSAGE, 129, 131, 0, 255, 0, 0, 0);
aot_set(4, 11900, 12920, 1360, 1190, SCE_MESSAGE, 129, 132, 0, 255, 0, 0, 0);
aot_set(5, 12410, 7480, 510, 3230, SCE_MESSAGE, 129, 133, 0, 255, 0, 0, 0);
aot_set(6, 14620, 11560, 1190, 2380, SCE_MESSAGE, 129, 134, 0, 255, 0, 0, 0);
aot_set(7, 14450, 4590, 1360, 3910, SCE_MESSAGE, 129, 135, 0, 255, 0, 0, 0);
return;

// main procedure 0
if (ck(FG_COMMON, 227, 1)) {
    set(FG_COMMON, 227, 0);
    message(128, 255, 0);
}
return;
