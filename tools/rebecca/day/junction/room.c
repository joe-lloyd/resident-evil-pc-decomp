// junction (51E), written by day/scripts.ts from day/junction/scene.py: edit the scene, not this file.
// init procedure 0
// To tunnel.
door_aot_set(0, 1700, 8160, 1020, 3400, 0, 1, 8, 0, 0, ROOM_51C, 29920, 0, 13600, 2048, UNLOCKED, 193);
// To mine-lift.
door_aot_set(1, 10625, 1955, 3230, 1020, 0, 1, 8, 0, 0, ROOM_509, 3315, 0, 2805, 1024, UNLOCKED, 193);
// To gallery.
if (ck(FG_COMMON, 135, 1)) {
    aot_set(2, 7140, 13090, 6120, 1020, SCE_MESSAGE, 129, 129, 0, 255, 0, 0, 0);
} else {
    door_aot_set(2, 7140, 13090, 6120, 1020, 0, 1, 8, 0, 0, ROOM_51F, 4420, 0, 8500, 0, UNLOCKED, 193);
}
aot_set(3, 14450, 1700, 1700, 1360, SCE_MESSAGE, 129, 130, 0, 255, 0, 0, 0);
aot_set(4, 7140, 12070, 6120, 1020, SCE_MESSAGE, 129, 131, 0, 255, 0, 0, 0);
aot_set(5, 16830, 6120, 850, 2720, SCE_MESSAGE, 129, 132, 0, 255, 0, 0, 0);
aot_set(6, 9180, 9520, 3400, 2040, SCE_MESSAGE, 129, 133, 0, 255, 0, 0, 0);
enemy(3, 2, 219, 1, 2, 0, 0, 1796, 0, 0, 21100, 0, 16000, 0, 0, 0, 0);  // a spinner
enemy(3, 2, 220, 1, 2, 0, 0, 2307, 0, 0, 21100, 0, 2400, 1, 0, 0, 0);  // a spinner
// drain (day/events.ts), FG_COMMON 135 once it has happened.
if (ck(FG_COMMON, 135, 1)) {
    aot_set(7, 17000, 8840, 1360, 2380, SCE_USEITEM, 129, 4, 0, 12, 0, 1, 0);   // the action button here raises FG_ROOM 12
} else {
    aot_set(8, 17000, 8840, 1360, 2380, SCE_MESSAGE, 129, 135, 0, 255, 0, 0, 0);
}
return;

// main procedure 0
if (ck(FG_COMMON, 135, 1) && ck(FG_ROOM, 12, 0)) {
    set(FG_ROOM, 12, 1);
    if (ck(FG_COMMON, 131, 0)) {
        set(FG_COMMON, 135, 0);
        door_aot_set(2, 7140, 13090, 6120, 1020, 0, 1, 8, 0, 0, ROOM_51F, 4420, 0, 8500, 0, UNLOCKED, 193);
        aot_set(8, 17000, 8840, 1360, 2380, SCE_MESSAGE, 129, 135, 0, 255, 0, 0, 0);
        tbl37_set(4, 28, 40);   // tunnel
        tbl37_set(4, 30, 40);   // junction
        bgm_stop(1);
        message(136, 255, 0);
    } else {
        message(134, 255, 0);
    }
}
return;
