// mine-entrance (51B), written by day/scripts.ts from day/mine-entrance/scene.py: edit the scene, not this file.
// init procedure 0
// To quarry.
door_aot_set(0, 1105, 10200, 1020, 4080, 0, 15, 48, 4, 0, ROOM_519, 29580, 0, 12580, 2048, UNLOCKED, 1);
// To tunnel.
if (ck(FG_COMMON, 134, 1)) {
    aot_set(1, 20145, 3740, 1785, 1870, SCE_MESSAGE, 129, 129, 0, 255, 0, 0, 0);
} else {
    door_aot_set(1, 20145, 3740, 1785, 1870, 0, 1, 8, 0, 0, ROOM_51C, 8500, 0, 29920, 1024, UNLOCKED, 193);
}
aot_set(2, 18190, 4250, 1955, 2040, SCE_MESSAGE, 129, 130, 0, 255, 0, 0, 0);
aot_set(3, 25840, 14280, 3570, 4930, SCE_MESSAGE, 129, 131, 0, 255, 0, 0, 0);
aot_set(4, 25500, 3740, 2550, 1870, SCE_MESSAGE, 129, 132, 0, 255, 0, 0, 0);
aot_set(5, 24990, 9010, 4080, 4420, SCE_MESSAGE, 129, 133, 0, 255, 0, 0, 0);
aot_set(6, 4335, 10710, 3485, 2465, SCE_MESSAGE, 129, 134, 0, 255, 0, 0, 0);
aot_set(7, 2125, 9690, 2210, 1530, SCE_MESSAGE, 129, 135, 0, 255, 0, 0, 0);
// blast (day/events.ts), FG_COMMON 134 once it has happened.
if (ck(FG_COMMON, 134, 1)) {
    aot_set(8, 21845, 4250, 3655, 4080, SCE_USEITEM, 1, 9, 0, 15, 0, 1, 0);   // the dynamite can be used here
    aot_set(9, 21845, 4250, 3655, 4080, SCE_MESSAGE, 129, 136, 0, 255, 0, 0, 0);
} else {
    aot_set(9, 21845, 4250, 3655, 4080, SCE_MESSAGE, 129, 137, 0, 255, 0, 0, 0);
}
return;

// main procedure 0
if (ck(FG_COMMON, 134, 1)) {
    if (ck(FG_ROOM, 12, 1) && testitem(42)) {
        set(FG_ROOM, 12, 0);
        setw(4, 0, 0);
    }
    if (ck(FG_ROOM, 12, 0) && cmpw(0, 4, 1, 0)) {
        set(FG_ROOM, 12, 1);
        if (item_ck(42)) {
            remove_item(42);
        }
        set(FG_COMMON, 134, 0);
        door_aot_set(1, 20145, 3740, 1785, 1870, 0, 1, 8, 0, 0, ROOM_51C, 8500, 0, 29920, 1024, UNLOCKED, 193);
        aot_set(9, 21845, 4250, 3655, 4080, SCE_MESSAGE, 129, 137, 0, 255, 0, 0, 0);
        message(138, 255, 0);
    }
}
return;
