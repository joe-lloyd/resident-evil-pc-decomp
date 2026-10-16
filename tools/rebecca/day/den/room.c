// den (31B), written by day/scripts.ts from day/den/scene.py: edit the scene, not this file.
// init procedure 0
// To woods.
door_aot_set(0, 12750, 19380, 4250, 1020, 0, 15, 48, 4, 0, ROOM_31A, 15130, 0, 6120, 3072, UNLOCKED, 1);
if (ck(FG_ITEM, 160, 0)) {  // ranger keys (truck-keys)
    item_aot_set(1, 18185, 8495, 1200, 1200, 57, 1, 0, 255, 97, 73, 76, 0, 135, 35, 0, 0, 160, 129, 0, 0);
}
aot_set(2, 16320, 6460, 3060, 3400, SCE_MESSAGE, 129, 129, 0, 255, 0, 0, 0);
aot_set(3, 12410, 3570, 3570, 2720, SCE_MESSAGE, 129, 130, 0, 255, 0, 0, 0);
aot_set(4, 15980, 5780, 1870, 1360, SCE_MESSAGE, 129, 131, 0, 255, 0, 0, 0);
aot_set(5, 15810, 3400, 1700, 1700, SCE_MESSAGE, 129, 132, 0, 255, 0, 0, 0);
aot_set(6, 22270, 14280, 3230, 3060, SCE_MESSAGE, 129, 133, 0, 255, 0, 0, 0);
aot_set(7, 8160, 7820, 2040, 2040, SCE_MESSAGE, 129, 134, 0, 255, 0, 0, 0);
aot_set(8, 15130, 6120, 1870, 1700, SCE_MESSAGE, 129, 135, 0, 255, 0, 0, 0);
enemy(2, 1, 190, 1, 2, 0, 0, 2737, 0, 0, 22800, 0, 4440, 0, 0, 0, 0);  // a cerberus
return;

// main procedure 0
if (ck(FG_COMMON, 210, 1)) {
    set(FG_COMMON, 210, 0);
    message(128, 255, 0);
}
return;
