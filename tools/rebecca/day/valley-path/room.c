// valley-path (218), written by day/scripts.ts from day/valley-path/scene.py: edit the scene, not this file.
// init procedure 0
// To pylon.
door_aot_set(0, 15300, 3230, 1700, 1190, 0, 0, 0, 4, 0, ROOM_217, 11900, 0, 9520, 1024, UNLOCKED, 193);
// To crash.
door_aot_set(1, 1700, 13260, 1020, 4080, 0, 15, 48, 4, 0, ROOM_21B, 26520, 0, 13600, 2048, UNLOCKED, 1);
// To lower-yard.
door_aot_set(2, 31280, 13260, 1020, 4080, 0, 15, 48, 4, 0, ROOM_219, 4420, 0, 14790, 0, UNLOCKED, 1);
// To creek.
door_aot_set(3, 14960, 27880, 4080, 1020, 0, 15, 48, 4, 0, ROOM_21C, 17680, 0, 5780, 3072, UNLOCKED, 1);
aot_set(4, 25330, 17340, 2210, 2720, SCE_MESSAGE, 129, 129, 0, 255, 0, 0, 0);
aot_set(5, 6800, 12410, 1700, 1530, SCE_MESSAGE, 129, 130, 0, 255, 0, 0, 0);
aot_set(6, 17340, 12920, 2380, 1360, SCE_MESSAGE, 129, 131, 0, 255, 0, 0, 0);
aot_set(7, 18700, 17680, 1700, 2720, SCE_MESSAGE, 129, 132, 0, 255, 0, 0, 0);
aot_set(8, 15130, 3910, 2380, 1190, SCE_MESSAGE, 129, 133, 0, 255, 0, 0, 0);
return;

// main procedure 0
if (ck(FG_COMMON, 245, 1)) {
    set(FG_COMMON, 245, 0);
    message(128, 255, 0);
}
return;
