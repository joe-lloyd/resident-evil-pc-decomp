// bunkhouse (31F), written by day/scripts.ts from day/bunkhouse/scene.py: edit the scene, not this file.
// init procedure 0
// To camp-yard.
door_aot_set(0, 9690, 8840, 2550, 1870, 1, 0, 7, 1, 0, ROOM_31E, 19465, 0, 5780, 3072, UNLOCKED, 193);
if (ck(FG_ITEM, 181, 0)) {  // clip
    item_aot_set(1, 18990, 4030, 1200, 1200, 11, 15, 0, 255, 134, 76, 0, 0, 22, 18, 0, 0, 181, 129, 0, 0);
}
if (ck(FG_ITEM, 182, 0)) {  // redHerb
    item_aot_set(2, 1990, 4030, 1200, 1200, 67, 1, 1, 255, 30, 10, 0, 0, 22, 18, 0, 0, 182, 129, 1, 0);
}
// Bunkhouse calendar, a file.
if (ck(FG_ITEM, 232, 0)) {
    item_aot_set(3, 11475, 1190, 1402, 2720, 107, 1, 2, 255, 0, 0, 0, 0, 0, 0, 0, 0, 232, 129, 0, 0);
}
aot_set(4, 12878, 3910, 3782, 1360, SCE_MESSAGE, 129, 129, 0, 255, 0, 0, 0);
aot_set(5, 15130, 6460, 4080, 1955, SCE_MESSAGE, 129, 130, 0, 255, 0, 0, 0);
aot_set(6, 12920, 7565, 2210, 1615, SCE_MESSAGE, 129, 131, 0, 255, 0, 0, 0);
aot_set(7, 6970, 4590, 3400, 2890, SCE_MESSAGE, 129, 132, 0, 255, 0, 0, 0);
aot_set(8, 11220, 5780, 2720, 2380, SCE_MESSAGE, 129, 133, 0, 255, 0, 0, 0);
aot_set(9, 9350, 3145, 2550, 1445, SCE_MESSAGE, 129, 134, 0, 255, 0, 0, 0);
aot_set(10, 1700, 3400, 3570, 1870, SCE_MESSAGE, 129, 135, 0, 255, 0, 0, 0);
enemy(17, 0, 195, 1, 2, 0, 0, 2273, 0, 0, 19400, 0, 4780, 0, 0, 0, 0);  // a zombie
return;

// main procedure 0
return;
