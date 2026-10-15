// mess (413), written by day/scripts.ts from day/mess/scene.py: edit the scene, not this file.
// init procedure 0
// To camp-yard.
door_aot_set(0, 10030, 8500, 850, 1530, 1, 0, 7, 1, 0, ROOM_31E, 6290, 0, 16065, 0, UNLOCKED, 193);
aot_set(1, 3910, 7429, 2380, 1020, SCE_MESSAGE, 129, 129, 0, 255, 0, 0, 0);
aot_set(2, 5780, 7259, 1020, 850, SCE_MESSAGE, 129, 130, 0, 255, 0, 0, 0);
aot_set(3, 4760, 3145, 3060, 765, SCE_MESSAGE, 129, 131, 0, 255, 0, 0, 0);
aot_set(4, 8585, 11220, 935, 3060, SCE_MESSAGE, 129, 132, 0, 255, 0, 0, 0);
aot_set(5, 4675, 11220, 935, 3400, SCE_MESSAGE, 129, 133, 0, 255, 0, 0, 0);
aot_set(6, 1700, 7650, 1020, 1700, SCE_MESSAGE, 129, 134, 0, 255, 0, 0, 0);
aot_set(7, 3230, 6970, 1020, 850, SCE_MESSAGE, 129, 135, 0, 255, 0, 0, 0);
enemy(17, 0, 196, 1, 2, 0, 0, 3879, 0, 0, 2400, 0, 7160, 0, 0, 0, 0);  // a zombie
enemy(17, 0, 197, 1, 2, 0, 0, 3228, 0, 0, 7160, 0, 3760, 1, 0, 0, 0);  // a zombie
if (ck(FG_ITEM, 184, 0)) {  // greenHerb
    item_aot_set(8, 1500, 6260, 1800, 1800, 68, 1, 0, 255, 96, 9, 0, 0, 248, 27, 0, 0, 184, 129, 1, 0);
}
if (ck(FG_ITEM, 162, 0)) {  // office key (office-key)
    item_aot_set(9, 4200, 6869, 1800, 1800, 58, 1, 1, 255, 236, 19, 0, 0, 89, 30, 0, 0, 162, 129, 0, 0);
}
return;

// main procedure 0
if (ck(FG_COMMON, 216, 1)) {
    set(FG_COMMON, 216, 0);
    message(128, 255, 0);
}
return;
