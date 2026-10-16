// booth (319), written by day/scripts.ts from day/booth/scene.py: edit the scene, not this file.
// init procedure 0
// To platform.
door_aot_set(0, 4420, 5440, 1530, 680, 1, 0, 33, 1, 0, ROOM_318, 22355, 0, 10710, 3072, UNLOCKED, 193);
// The typewriter and the item box, its lid on the body the scene paints.
aot_set(1, 3315, 1700, 1020, 1360, SCE_TYPEWRITER, 129, 0, 0, 0, 0, 0, 0);
aot_set(2, 5440, 3349, 1700, 782, SCE_ITEMBOX, 129, 0, 0, 0, 0, 0, 0);
obj(0, 17, 255, 7129, -1440, 3485, 2048, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0);
aot_set(3, 5100, 1700, 1870, 1190, SCE_MESSAGE, 129, 129, 0, 255, 0, 0, 0);
aot_set(4, 1700, 4080, 1530, 850, SCE_MESSAGE, 129, 130, 0, 255, 0, 0, 0);
aot_set(5, 3230, 4080, 1360, 1020, SCE_MESSAGE, 129, 131, 0, 255, 0, 0, 0);
aot_set(6, 5440, 4165, 1700, 850, SCE_MESSAGE, 129, 132, 0, 255, 0, 0, 0);
aot_set(7, 5950, 5015, 1190, 850, SCE_MESSAGE, 129, 133, 0, 255, 0, 0, 0);
aot_set(8, 3570, 5100, 850, 1020, SCE_MESSAGE, 129, 134, 0, 255, 0, 0, 0);
if (ck(FG_ITEM, 180, 0)) {  // greenHerb
    item_aot_set(9, 2820, 2820, 1200, 1200, 68, 1, 0, 255, 92, 13, 0, 0, 92, 13, 0, 0, 180, 129, 1, 0);
}
// fit-fuse (day/events.ts), FG_COMMON 140 once it has happened.
if (ck(FG_COMMON, 140, 1)) {
    aot_set(10, 5440, 2210, 1700, 1105, SCE_USEITEM, 1, 9, 0, 12, 0, 1, 0);   // the fuses can be used here
    aot_set(11, 5440, 2210, 1700, 1105, SCE_MESSAGE, 129, 135, 0, 255, 0, 0, 0);
} else {
    aot_set(11, 5440, 2210, 1700, 1105, SCE_MESSAGE, 129, 136, 0, 255, 0, 0, 0);
}
// gondola-runs (day/events.ts), FG_COMMON 141 once it has happened.
if (ck(FG_COMMON, 141, 1)) {
    if (ck(FG_COMMON, 139, 0) && ck(FG_COMMON, 140, 0) && ck(FG_COMMON, 132, 0)) {
        aot_set(12, 1700, 1870, 1530, 850, SCE_USEITEM, 1, 9, 0, 29, 0, 1, 0);   // the operator key can be used here
    }
    aot_set(13, 1700, 1870, 1530, 850, SCE_MESSAGE, 129, 138, 0, 255, 0, 0, 0);
} else {
    aot_set(13, 1700, 1870, 1530, 850, SCE_MESSAGE, 129, 139, 0, 255, 0, 0, 0);
}
return;

// main procedure 0
if (ck(FG_COMMON, 208, 1)) {
    set(FG_COMMON, 208, 0);
    message(128, 255, 0);
}
if (ck(FG_COMMON, 140, 1)) {
    if (ck(FG_ROOM, 12, 1) && testitem(39)) {
        set(FG_ROOM, 12, 0);
        setw(4, 0, 0);
    }
    if (ck(FG_ROOM, 12, 0) && cmpw(0, 4, 1, 0)) {
        set(FG_ROOM, 12, 1);
        if (item_ck(39)) {
            remove_item(39);
        }
        set(FG_COMMON, 140, 0);
        aot_set(11, 5440, 2210, 1700, 1105, SCE_MESSAGE, 129, 136, 0, 255, 0, 0, 0);
        message(137, 255, 0);
    }
}
if (ck(FG_COMMON, 141, 1)) {
    if (ck(FG_COMMON, 139, 0) && ck(FG_COMMON, 140, 0) && ck(FG_COMMON, 132, 0) && ck(FG_ROOM, 14, 1)) {
        set(FG_ROOM, 14, 0);
        aot_set(12, 1700, 1870, 1530, 850, SCE_USEITEM, 1, 9, 0, 29, 0, 1, 0);   // the operator key can be used here
    }
    if (ck(FG_ROOM, 13, 1) && testitem(56)) {
        set(FG_ROOM, 13, 0);
        setw(4, 0, 0);
    }
    if (ck(FG_ROOM, 13, 0) && cmpw(0, 4, 1, 0)) {
        set(FG_ROOM, 13, 1);
        if (item_ck(56)) {
            remove_item(56);
        }
        set(FG_COMMON, 141, 0);
        aot_set(13, 1700, 1870, 1530, 850, SCE_MESSAGE, 129, 139, 0, 255, 0, 0, 0);
        message(140, 255, 0);
    }
}
return;
