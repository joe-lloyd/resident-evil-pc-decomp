// mess (413), written by day/scripts.ts from day/mess/scene.py: edit the scene, not this file.
// init procedure 0
// To camp-yard.
door_aot_set(0, 9520, 7990, 1870, 2550, 1, 0, 7, 1, 0, ROOM_31E, 6290, 0, 16065, 0, UNLOCKED, 193);
if (ck(FG_ITEM, 162, 0)) {  // office key (office-key)
    item_aot_set(1, 4350, 7019, 1500, 1500, 58, 1, 1, 255, 236, 19, 0, 0, 89, 30, 0, 0, 162, 129, 0, 0);
}
if (ck(FG_ITEM, 185, 0)) {  // greenHerb
    item_aot_set(2, 9470, 15590, 1200, 1200, 68, 1, 0, 255, 86, 39, 0, 0, 62, 63, 0, 0, 185, 129, 1, 0);
}
aot_set(3, 3910, 7429, 2380, 1530, SCE_MESSAGE, 129, 129, 0, 255, 0, 0, 0);
aot_set(4, 5780, 6749, 1530, 1360, SCE_MESSAGE, 129, 130, 0, 255, 0, 0, 0);
aot_set(5, 4250, 2635, 4080, 1785, SCE_MESSAGE, 129, 131, 0, 255, 0, 0, 0);
aot_set(6, 8075, 10710, 1955, 4080, SCE_MESSAGE, 129, 132, 0, 255, 0, 0, 0);
aot_set(7, 4165, 10710, 1955, 4420, SCE_MESSAGE, 129, 133, 0, 255, 0, 0, 0);
aot_set(8, 1190, 7140, 1785, 2720, SCE_MESSAGE, 129, 134, 0, 255, 0, 0, 0);
aot_set(9, 2975, 6460, 1275, 1360, SCE_MESSAGE, 129, 135, 0, 255, 0, 0, 0);
enemy(17, 0, 196, 1, 2, 0, 0, 3528, 0, 0, 4440, 0, 4440, 0, 0, 0, 0);  // a zombie
enemy(17, 0, 197, 1, 2, 0, 0, 31, 0, 0, 2740, 0, 9540, 1, 0, 0, 0);  // a zombie
return;

// main procedure 0
return;
