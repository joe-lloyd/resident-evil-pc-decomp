// tower-foot (41C), written by day/scripts.ts from day/tower-foot/scene.py: edit the scene, not this file.
// init procedure 0
// To washout.
door_aot_set(0, 31280, 9350, 1020, 5100, 0, 15, 48, 4, 0, ROOM_41A, 4420, 0, 10370, 0, UNLOCKED, 1);
// To tower-stairs.
door_aot_set(1, 9690, 11135, 1020, 1700, 1, 0, 7, 1, 172, ROOM_41D, 12240, 0, 11730, 3072, 57, 193);
aot_set(2, 20910, 12410, 3910, 3570, SCE_MESSAGE, 129, 129, 0, 255, 0, 0, 0);
aot_set(3, 9690, 10455, 1020, 680, SCE_MESSAGE, 129, 130, 0, 255, 0, 0, 0);
aot_set(4, 26180, 14960, 2380, 2040, SCE_MESSAGE, 129, 131, 0, 255, 0, 0, 0);
aot_set(5, 30430, 6120, 1020, 2720, SCE_MESSAGE, 129, 132, 0, 255, 0, 0, 0);
aot_set(6, 24820, 3400, 2040, 1360, SCE_MESSAGE, 129, 133, 0, 255, 0, 0, 0);
aot_set(7, 4335, 17850, 935, 1700, SCE_MESSAGE, 129, 134, 0, 255, 0, 0, 0);
return;

// main procedure 0
if (ck(FG_COMMON, 225, 1)) {
    set(FG_COMMON, 225, 0);
    message(128, 255, 0);
}
return;
