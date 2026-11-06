// depot (414), written by day/scripts.ts from day/depot/scene.py: edit the scene, not this file.
// init procedure 0
// To camp-yard.
// Shut from this side until she opens it from the other (FG_LOCK 41).
if (ck(FG_LOCK, 41, 1)) {
    aot_set(0, 9010, 1190, 4080, 2040, SCE_MESSAGE, 129, 129, 0, 255, 0, 0, 0);
} else {
    door_aot_set(0, 9010, 1190, 4080, 2040, 0, 16, 48, 4, 0, ROOM_31E, 5950, 0, 23290, 1024, UNLOCKED, 193);
}
// To tower-foot.
if (ck(FG_COMMON, 144, 1)) {
    aot_set(1, 15385, 8925, 935, 1870, SCE_MESSAGE, 129, 130, 0, 255, 0, 0, 0);
} else {
    door_aot_set(1, 15385, 8925, 935, 1870, 0, 15, 48, 4, 0, ROOM_41C, 15300, 0, 6120, 3072, UNLOCKED, 1);
}
if (ck(FG_ITEM, 187, 0)) {  // greenHerb
    item_aot_set(2, 1650, 9810, 1200, 1200, 68, 1, 0, 255, 202, 8, 0, 0, 170, 40, 0, 0, 187, 129, 1, 0);
}
aot_set(3, 10200, 6120, 2465, 1955, SCE_MESSAGE, 129, 131, 0, 255, 0, 0, 0);
aot_set(4, 6120, 2890, 2550, 2380, SCE_MESSAGE, 129, 132, 0, 255, 0, 0, 0);
aot_set(5, 1530, 7310, 3400, 1700, SCE_MESSAGE, 129, 133, 0, 255, 0, 0, 0);
enemy(10, 1, 203, 1, 1, 0, 0, 394, 0, 0, 2400, 0, 10220, 0, 0, 0, 0);  // a adder
enemy(10, 1, 204, 1, 1, 0, 0, 3969, 0, 0, 3420, 0, 2740, 1, 0, 0, 0);  // a adder
// fuel (day/events.ts), FG_COMMON 130 once it has happened.
if (ck(FG_COMMON, 130, 1)) {
    aot_set(6, 12665, 5950, 2167, 1657, SCE_USEITEM, 1, 9, 0, 4, 0, 1, 0);   // the jerrycan can be used here
    aot_set(7, 12665, 5950, 2167, 1657, SCE_MESSAGE, 129, 134, 0, 255, 0, 0, 0);
} else {
    if (ck(FG_ITEM, 247, 1)) {
        aot_set(7, 12665, 5950, 2167, 1657, SCE_MESSAGE, 129, 135, 0, 255, 0, 0, 0);
    }
}
if (ck(FG_COMMON, 130, 0) && ck(FG_ITEM, 247, 0)) {  // diesel, left here
    item_aot_set(7, 12665, 5950, 2167, 1657, 32, 1, 1, 255, 181, 53, 0, 0, 123, 26, 0, 0, 247, 129, 0, 0);
}
// skid-road (day/events.ts), FG_COMMON 144 once it has happened.
if (ck(FG_COMMON, 144, 1)) {
    aot_set(8, 14833, 7608, 1487, 1317, SCE_USEITEM, 129, 4, 0, 14, 0, 1, 0);   // the action button here raises FG_ROOM 14
} else {
    aot_set(9, 14833, 7608, 1487, 1317, SCE_MESSAGE, 129, 138, 0, 255, 0, 0, 0);
}
return;

// main procedure 0
if (ck(FG_COMMON, 130, 1)) {
    if (ck(FG_ROOM, 12, 1) && testitem(31)) {
        set(FG_ROOM, 12, 0);
        setw(4, 0, 0);
    }
    if (ck(FG_ROOM, 12, 0) && cmpw(0, 4, 1, 0)) {
        set(FG_ROOM, 12, 1);
        if (ck(FG_COMMON, 135, 0)) {
            if (item_ck(31)) {
                remove_item(31);
            }
        }
        set(FG_COMMON, 130, 0);
        message(136, 255, 0);
    }
}
if (ck(FG_COMMON, 130, 0) && ck(FG_ITEM, 247, 0) && ck(FG_ROOM, 13, 1)) {
    set(FG_ROOM, 13, 0);
    item_aot_set(7, 12665, 5950, 2167, 1657, 32, 1, 1, 255, 181, 53, 0, 0, 123, 26, 0, 0, 247, 129, 0, 0);
}
if (ck(FG_COMMON, 144, 1) && ck(FG_ROOM, 14, 0)) {
    set(FG_ROOM, 14, 1);
    set(FG_COMMON, 144, 0);
    door_aot_set(1, 15385, 8925, 935, 1870, 0, 15, 48, 4, 0, ROOM_41C, 15300, 0, 6120, 3072, UNLOCKED, 1);
    aot_set(9, 14833, 7608, 1487, 1317, SCE_MESSAGE, 129, 138, 0, 255, 0, 0, 0);
    message(139, 255, 0);
}
return;
