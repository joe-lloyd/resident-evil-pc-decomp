// east-path (517), written by day/scripts.ts from day/east-path/scene.py: edit the scene, not this file.
// init procedure 0
// To platform.
door_aot_set(0, 1700, 11050, 1020, 3400, 0, 15, 48, 4, 0, ROOM_318, 26520, 0, 15300, 2048, UNLOCKED, 1);
// To cottage.
door_aot_set(1, 14620, 7055, 1530, 1020, 0, 0, 0, 4, 0, ROOM_518, 5185, 0, 5950, 1024, UNLOCKED, 193);
// To quarry.
door_aot_set(2, 30430, 11900, 1020, 3400, 0, 15, 48, 4, 0, ROOM_519, 4080, 0, 16150, 0, UNLOCKED, 1);
aot_set(3, 6290, 11220, 2550, 2550, SCE_MESSAGE, 129, 129, 0, 255, 0, 0, 0);
aot_set(4, 10200, 10540, 3740, 2040, SCE_MESSAGE, 129, 130, 0, 255, 0, 0, 0);
aot_set(5, 13770, 7055, 850, 1105, SCE_MESSAGE, 129, 131, 0, 255, 0, 0, 0);
aot_set(6, 24480, 11560, 3060, 2380, SCE_MESSAGE, 129, 132, 0, 255, 0, 0, 0);
aot_set(7, 20230, 8500, 2380, 2210, SCE_MESSAGE, 129, 133, 0, 255, 0, 0, 0);
aot_set(8, 6800, 17850, 3400, 2550, SCE_MESSAGE, 129, 134, 0, 255, 0, 0, 0);
aot_set(9, 23460, 17000, 2720, 2720, SCE_MESSAGE, 129, 135, 0, 255, 0, 0, 0);
aot_set(10, 8500, 7140, 2040, 2040, SCE_MESSAGE, 129, 136, 0, 255, 0, 0, 0);
return;

// main procedure 0
if (ck(FG_COMMON, 230, 1)) {
    set(FG_COMMON, 230, 0);
    message(128, 255, 0);
}
return;
