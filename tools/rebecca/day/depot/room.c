// depot (414), written by day/scripts.ts from day/depot/scene.py: edit the scene, not this file.
// init procedure 0
// To camp-yard.
door_aot_set(0, 9520, 1700, 3060, 1020, 0, 16, 48, 4, 0, ROOM_31E, 5950, 0, 23290, 1024, UNLOCKED, 1);
aot_set(1, 10710, 6630, 1700, 935, SCE_MESSAGE, 129, 129, 0, 255, 0, 0, 0);
aot_set(2, 13770, 4420, 680, 2380, SCE_MESSAGE, 129, 130, 0, 255, 0, 0, 0);
aot_set(3, 6630, 3400, 1530, 1360, SCE_MESSAGE, 129, 131, 0, 255, 0, 0, 0);
aot_set(4, 2040, 7820, 2380, 680, SCE_MESSAGE, 129, 132, 0, 255, 0, 0, 0);
enemy(10, 1, 198, 1, 1, 0, 0, 394, 0, 0, 2400, 0, 10220, 0, 0, 0, 0);  // a adder
enemy(10, 1, 199, 1, 1, 0, 0, 3941, 0, 0, 3420, 0, 2400, 1, 0, 0, 0);  // a adder
if (ck(FG_ITEM, 186, 0)) {  // greenHerb
    item_aot_set(5, 1800, 9620, 1200, 1200, 68, 1, 0, 255, 96, 9, 0, 0, 236, 39, 0, 0, 186, 129, 1, 0);
}
// fuel (day/events.ts), FG_COMMON 130 once it has happened.
if (ck(FG_COMMON, 130, 1)) {
    aot_set(6, 12920, 6460, 1700, 1020, SCE_USEITEM, 1, 9, 0, 4, 0, 1, 0);   // the jerrycan can be used here
    aot_set(7, 12920, 6460, 1700, 1020, SCE_MESSAGE, 129, 133, 0, 255, 0, 0, 0);
} else {
    if (ck(FG_ITEM, 247, 1)) {
        aot_set(7, 12920, 6460, 1700, 1020, SCE_MESSAGE, 129, 134, 0, 255, 0, 0, 0);
    }
}
if (ck(FG_COMMON, 130, 0) && ck(FG_ITEM, 247, 0)) {  // diesel, left here
    item_aot_set(7, 12920, 6460, 1700, 1020, 32, 1, 1, 255, 202, 53, 0, 0, 58, 27, 0, 0, 247, 129, 0, 0);
}
return;

// main procedure 0
if (ck(FG_COMMON, 217, 1)) {
    set(FG_COMMON, 217, 0);
    message(128, 255, 0);
}
if (ck(FG_COMMON, 130, 1)) {
    if (ck(FG_ROOM, 12, 1) && testitem(31)) {
        set(FG_ROOM, 12, 0);
        setw(4, 0, 0);
    }
    if (ck(FG_ROOM, 12, 0) && cmpw(0, 4, 1, 0)) {
        set(FG_ROOM, 12, 1);
        if (item_ck(31)) {
            remove_item(31);
        }
        set(FG_COMMON, 130, 0);
        message(135, 255, 0);
    }
}
if (ck(FG_COMMON, 130, 0) && ck(FG_ITEM, 247, 0) && ck(FG_ROOM, 13, 1)) {
    set(FG_ROOM, 13, 0);
    item_aot_set(7, 12920, 6460, 1700, 1020, 32, 1, 1, 255, 202, 53, 0, 0, 58, 27, 0, 0, 247, 129, 0, 0);
}
return;
