// generator (41B), written by day/scripts.ts from day/generator/scene.py: edit the scene, not this file.
// init procedure 0
// To washout.
door_aot_set(0, 4250, 1190, 1870, 1700, 0, 1, 11, 3, 0, ROOM_41A, 6460, 0, 19040, 1024, UNLOCKED, 193);
// To switch.
door_aot_set(1, 5950, 7140, 2380, 1530, 0, 1, 11, 3, 173, ROOM_41F, 3740, 0, 3570, 3072, 55, 193);
aot_set(2, 1530, 1190, 2720, 1785, SCE_MESSAGE, 129, 129, 0, 255, 0, 0, 0);
aot_set(3, 5015, 2890, 1190, 1530, SCE_MESSAGE, 129, 130, 0, 255, 0, 0, 0);
aot_set(4, 3910, 6375, 1700, 765, SCE_MESSAGE, 129, 131, 0, 255, 0, 0, 0);
aot_set(5, 2720, 7140, 1530, 1530, SCE_MESSAGE, 129, 132, 0, 255, 0, 0, 0);
aot_set(6, 6460, 1700, 1870, 2720, SCE_MESSAGE, 129, 133, 0, 255, 0, 0, 0);
aot_set(7, 3570, 4420, 1402, 1955, SCE_MESSAGE, 129, 134, 0, 255, 0, 0, 0);
aot_set(8, 5950, 6120, 2380, 1020, SCE_MESSAGE, 129, 135, 0, 255, 0, 0, 0);
// generator-on (day/events.ts), FG_COMMON 131 once it has happened.
if (ck(FG_COMMON, 131, 1)) {
    aot_set(9, 3485, 3230, 1530, 1190, SCE_USEITEM, 1, 9, 0, 5, 0, 1, 0);   // the diesel can be used here
    aot_set(10, 3485, 3230, 1530, 1190, SCE_MESSAGE, 129, 136, 0, 255, 0, 0, 0);
} else {
    aot_set(10, 3485, 3230, 1530, 1190, SCE_MESSAGE, 129, 137, 0, 255, 0, 0, 0);
}
return;

// main procedure 0
if (ck(FG_COMMON, 131, 1)) {
    if (ck(FG_ROOM, 12, 1) && testitem(32)) {
        set(FG_ROOM, 12, 0);
        setw(4, 0, 0);
    }
    if (ck(FG_ROOM, 12, 0) && cmpw(0, 4, 1, 0)) {
        set(FG_ROOM, 12, 1);
        if (item_ck(32)) {
            remove_item(32);
        }
        set(FG_COMMON, 131, 0);
        aot_set(10, 3485, 3230, 1530, 1190, SCE_MESSAGE, 129, 137, 0, 255, 0, 0, 0);
        tbl37_set(2, 21, 24);   // yard
        tbl37_set(2, 26, 56);   // woods
        tbl37_set(2, 23, 24);   // bridge
        tbl37_set(2, 24, 24);   // platform
        tbl37_set(2, 22, 56);   // shed
        message(138, 255, 0);
    }
}
return;
