// generator (41B), written by day/scripts.ts from day/generator/scene.py: edit the scene, not this file.
// init procedure 0
// To washout.
door_aot_set(0, 4420, 1700, 1700, 1020, 0, 1, 11, 3, 0, ROOM_41A, 6460, 0, 19040, 1024, UNLOCKED, 193);
// To switch.
door_aot_set(1, 6460, 7140, 1360, 1020, 0, 1, 11, 3, 173, ROOM_41F, 3740, 0, 3570, 3072, 55, 193);
aot_set(2, 2040, 1700, 2040, 1020, SCE_MESSAGE, 129, 129, 0, 255, 0, 0, 0);
aot_set(3, 5015, 3060, 680, 1360, SCE_MESSAGE, 129, 130, 0, 255, 0, 0, 0);
aot_set(4, 3910, 6630, 1190, 510, SCE_MESSAGE, 129, 131, 0, 255, 0, 0, 0);
aot_set(5, 3230, 7140, 1020, 1020, SCE_MESSAGE, 129, 132, 0, 255, 0, 0, 0);
aot_set(6, 6800, 2210, 1020, 1700, SCE_MESSAGE, 129, 133, 0, 255, 0, 0, 0);
aot_set(7, 4080, 4420, 850, 1700, SCE_MESSAGE, 129, 134, 0, 255, 0, 0, 0);
aot_set(8, 6460, 6630, 1360, 510, SCE_MESSAGE, 129, 135, 0, 255, 0, 0, 0);
// generator-on (day/events.ts), FG_COMMON 131 once it has happened.
if (ck(FG_COMMON, 131, 1)) {
    aot_set(9, 3995, 3230, 1020, 1190, SCE_USEITEM, 1, 9, 0, 5, 0, 1, 0);   // the diesel can be used here
    aot_set(10, 3995, 3230, 1020, 1190, SCE_MESSAGE, 129, 136, 0, 255, 0, 0, 0);
} else {
    aot_set(10, 3995, 3230, 1020, 1190, SCE_MESSAGE, 129, 137, 0, 255, 0, 0, 0);
}
return;

// main procedure 0
if (ck(FG_COMMON, 224, 1)) {
    set(FG_COMMON, 224, 0);
    message(128, 255, 0);
}
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
        aot_set(10, 3995, 3230, 1020, 1190, SCE_MESSAGE, 129, 137, 0, 255, 0, 0, 0);
        tbl37_set(2, 21, 24);   // yard
        tbl37_set(2, 26, 56);   // woods
        tbl37_set(2, 23, 24);   // bridge
        tbl37_set(2, 24, 24);   // platform
        tbl37_set(2, 22, 24);   // shed
        message(138, 255, 0);
    }
}
return;
