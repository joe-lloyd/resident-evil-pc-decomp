// tower-top (41E), written by day/scripts.ts from day/tower-top/scene.py: edit the scene, not this file.
// init procedure 0
// To tower-stairs.
door_aot_set(0, 6375, 7650, 4590, 3230, 1, 11, 27, 64, 0, ROOM_41D, 12240, 0, 5270, 1024, UNLOCKED, 193);
if (ck(FG_ITEM, 164, 0)) {  // switch key (switch-key)
    item_aot_set(1, 10450, 6200, 1200, 1200, 55, 1, 1, 255, 42, 43, 74, 250, 144, 26, 0, 0, 164, 129, 0, 0);
}
aot_set(2, 10200, 10200, 2720, 2720, SCE_MESSAGE, 129, 129, 0, 255, 0, 0, 0);
// Lookout log, a file.
if (ck(FG_ITEM, 234, 0)) {
    item_aot_set(3, 10540, 6290, 1700, 1530, 105, 1, 2, 255, 0, 0, 0, 0, 0, 0, 0, 0, 234, 129, 0, 0);
}
aot_set(4, 12240, 6290, 1870, 1530, SCE_MESSAGE, 129, 130, 0, 255, 0, 0, 0);
aot_set(5, 11900, 12920, 1360, 1190, SCE_MESSAGE, 129, 131, 0, 255, 0, 0, 0);
aot_set(6, 12410, 7480, 510, 3230, SCE_MESSAGE, 129, 132, 0, 255, 0, 0, 0);
aot_set(7, 14620, 11560, 1190, 2380, SCE_MESSAGE, 129, 133, 0, 255, 0, 0, 0);
aot_set(8, 14450, 4590, 1360, 3910, SCE_MESSAGE, 129, 134, 0, 255, 0, 0, 0);
enemy(5, 0, 211, 1, 2, 0, 0, 2562, 0, 0, 13110, 0, 5290, 0, 0, 0, 0);  // a crow
enemy(5, 0, 212, 1, 2, 0, 0, 1878, 0, 0, 13110, 0, 13110, 1, 0, 0, 0);  // a crow
if (ck(FG_ITEM, 189, 0)) {  // clip
    item_aot_set(9, 12510, 4690, 1200, 1200, 11, 15, 0, 255, 54, 51, 0, 0, 170, 20, 0, 0, 189, 129, 0, 0);
}
return;

// main procedure 0
if (ck(FG_COMMON, 227, 1)) {
    set(FG_COMMON, 227, 0);
    message(128, 255, 0);
}
return;
