// line-track (516), written by day/scripts.ts from day/line-track/scene.py: edit the scene, not this file.
// init procedure 0
// To switch.
door_aot_set(0, 1700, 10370, 1020, 1870, 0, 0, 0, 4, 0, ROOM_41F, 5780, 0, 4505, 2048, UNLOCKED, 193);
// To platform.
door_aot_set(1, 31280, 10200, 1020, 3400, 0, 15, 48, 4, 0, ROOM_318, 5780, 0, 11900, 0, UNLOCKED, 1);
aot_set(2, 17340, 14110, 3400, 680, SCE_MESSAGE, 129, 129, 0, 255, 0, 0, 0);
aot_set(3, 13770, 10200, 1700, 1530, SCE_MESSAGE, 129, 130, 0, 255, 0, 0, 0);
aot_set(4, 15300, 11730, 1530, 1360, SCE_MESSAGE, 129, 131, 0, 255, 0, 0, 0);
aot_set(5, 9520, 14620, 3060, 1360, SCE_MESSAGE, 129, 132, 0, 255, 0, 0, 0);
aot_set(6, 29920, 13600, 2380, 1700, SCE_MESSAGE, 129, 133, 0, 255, 0, 0, 0);
aot_set(7, 1700, 8840, 1360, 1530, SCE_MESSAGE, 129, 134, 0, 255, 0, 0, 0);
return;

// main procedure 0
if (ck(FG_COMMON, 229, 1)) {
    set(FG_COMMON, 229, 0);
    message(128, 255, 0);
}
return;
