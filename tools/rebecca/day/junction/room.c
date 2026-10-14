// junction (51E), written by day/scripts.ts from day/junction/scene.py: edit the scene, not this file.
// init procedure 0
// To tunnel.
door_aot_set(0, 1700, 8160, 1020, 3400, 0, 0, 0, 4, 0, ROOM_51C, 29920, 0, 13600, 2048, UNLOCKED, 193);
// To mine-lift.
door_aot_set(1, 10625, 1955, 3230, 1020, 0, 0, 0, 4, 0, ROOM_509, 3315, 0, 2805, 1024, UNLOCKED, 193);
// To gallery.
door_aot_set(2, 7140, 13090, 6120, 1020, 0, 0, 0, 4, 0, ROOM_51F, 4420, 0, 8500, 0, UNLOCKED, 193);
aot_set(3, 14450, 1700, 1700, 1360, SCE_MESSAGE, 129, 129, 0, 255, 0, 0, 0);
aot_set(4, 17680, 8840, 4420, 2890, SCE_MESSAGE, 129, 130, 0, 255, 0, 0, 0);
aot_set(5, 20740, 12580, 1360, 1700, SCE_MESSAGE, 129, 131, 0, 255, 0, 0, 0);
aot_set(6, 7140, 12070, 6120, 1020, SCE_MESSAGE, 129, 132, 0, 255, 0, 0, 0);
aot_set(7, 16830, 6120, 850, 2720, SCE_MESSAGE, 129, 133, 0, 255, 0, 0, 0);
aot_set(8, 9180, 9520, 3400, 2040, SCE_MESSAGE, 129, 134, 0, 255, 0, 0, 0);
return;

// main procedure 0
if (ck(FG_COMMON, 237, 1)) {
    set(FG_COMMON, 237, 0);
    message(128, 255, 0);
}
return;
