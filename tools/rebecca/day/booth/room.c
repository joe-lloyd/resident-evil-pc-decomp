// booth (319), written by day/scripts.ts from day/booth/scene.py: edit the scene, not this file.
// init procedure 0
// To platform.
door_aot_set(0, 4420, 5440, 1530, 680, 1, 0, 33, 1, 0, ROOM_318, 22355, 0, 10710, 3072, UNLOCKED, 193);
// The typewriter and the item box, its lid on the body the scene paints.
aot_set(1, 3264, 1700, 816, 1360, SCE_TYPEWRITER, 129, 0, 0, 0, 0, 0, 0);
aot_set(2, 5440, 4454, 1700, 646, SCE_ITEMBOX, 129, 0, 0, 0, 0, 0, 0);
obj(0, 17, 255, 7132, -936, 4845, 2048, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0);
aot_set(3, 5100, 1700, 1870, 1190, SCE_MESSAGE, 129, 129, 0, 255, 0, 0, 0);
aot_set(4, 1700, 4080, 1530, 850, SCE_MESSAGE, 129, 130, 0, 255, 0, 0, 0);
aot_set(5, 3230, 4080, 1360, 1020, SCE_MESSAGE, 129, 131, 0, 255, 0, 0, 0);
aot_set(7, 5950, 5134, 1190, 731, SCE_MESSAGE, 129, 133, 0, 255, 0, 0, 0);
aot_set(8, 3570, 5100, 850, 1020, SCE_MESSAGE, 129, 134, 0, 255, 0, 0, 0);
if (ck(FG_ITEM, 180, 0)) {  // greenHerb
    item_aot_set(9, 3500, 1800, 1200, 1200, 68, 1, 0, 255, 4, 16, 0, 0, 96, 9, 0, 0, 180, 129, 1, 0);
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
// cut-phone (day/cutscenes.ts): its people, and what starts it. FG_COMMON 115 once it has run.
if (ck(FG_COMMON, 115, 1)) {
    aot_set(6, 5440, 3349, 1700, 1071, SCE_EVENT, 129, 9, 0, 0, 0, 0, 0);
} else {
    aot_set(6, 5440, 3349, 1700, 1071, SCE_MESSAGE, 129, 141, 0, 255, 0, 0, 0);
}
return;

// main procedure 0
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

// event procedure 0
// cut-phone (day/cutscenes.ts)
scd {
    set(FG_COMMON, 115, 0);
    aot_set(6, 5440, 3349, 1700, 1071, SCE_MESSAGE, 129, 141, 0, 255, 0, 0, 0);
    set(FG_STATUS, 15, 0);
    set(FG_6, 23, 1);
    return;
}
cutnext(1);
set_entity(ENT_PLAYER, 0);
anim_begin();
    anim_pose(6, 7140, 4590, 62);
anim_end_release();
do {
    yield();
} while (ck(FG_ROOM, 62, 1));
message(142, 0, 0);  // her
wait_voice();
message(143, 0, 0);  // her
wait_voice();
sleep(20);
message(144, 0, 0);  // Hal
wait_voice();
message(145, 0, 0);  // her
wait_voice();
message(146, 0, 0);  // Hal
wait_voice();
message(147, 0, 0);  // her
wait_voice();
message(148, 0, 0);  // Hal
wait_voice();
message(149, 0, 0);  // Hal
wait_voice();
message(150, 0, 0);  // Hal
wait_voice();
message(151, 0, 0);  // Hal
wait_voice();
message(152, 0, 0);  // Hal
wait_voice();
sleep(30);
message(153, 0, 0);  // her
wait_voice();
message(154, 0, 0);  // her
wait_voice();
set_entity(ENT_PLAYER, 0);
anim_begin();
    anim_idle();
anim_end_release();
scd {
    set(FG_STATUS, 15, 1);
    cut_auto(0);
    set(FG_6, 23, 0);
    return;
}
return;
