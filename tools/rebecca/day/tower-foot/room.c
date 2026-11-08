// tower-foot (41C), written by day/scripts.ts from day/tower-foot/scene.py: edit the scene, not this file.
// init procedure 0
// To washout.
door_aot_set(0, 31280, 9350, 1020, 5100, 0, 15, 48, 4, 0, ROOM_41A, 4420, 0, 10370, 0, UNLOCKED, 1);
// To depot.
// Shut from this side until skid-road opens it from depot (FG_COMMON 144).
if (ck(FG_COMMON, 144, 1)) {
    aot_set(1, 13770, 3400, 3060, 1020, SCE_MESSAGE, 129, 129, 0, 255, 0, 0, 0);
} else {
    door_aot_set(1, 13770, 3400, 3060, 1020, 0, 15, 48, 4, 0, ROOM_414, 13940, 0, 9690, 2048, UNLOCKED, 1);
}
// To tower-stairs.
door_aot_set(2, 9180, 11135, 2040, 2210, 1, 0, 7, 1, 172, ROOM_41D, 12240, 0, 11730, 3072, 57, 193);
aot_set(3, 20400, 11900, 4930, 4590, SCE_MESSAGE, 129, 130, 0, 255, 0, 0, 0);
aot_set(4, 9180, 9945, 2040, 1190, SCE_MESSAGE, 129, 131, 0, 255, 0, 0, 0);
aot_set(5, 25670, 14450, 3400, 3060, SCE_MESSAGE, 129, 132, 0, 255, 0, 0, 0);
aot_set(6, 29920, 5610, 2040, 3740, SCE_MESSAGE, 129, 133, 0, 255, 0, 0, 0);
aot_set(7, 24310, 2890, 3060, 2380, SCE_MESSAGE, 129, 134, 0, 255, 0, 0, 0);
aot_set(8, 3825, 17340, 1955, 2720, SCE_MESSAGE, 129, 135, 0, 255, 0, 0, 0);
return;

// main procedure 0
return;
