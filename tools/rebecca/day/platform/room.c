// platform (318), written by day/scripts.ts from day/platform/scene.py: edit the scene, not this file.
// init procedure 0
// To bridge.
door_aot_set(0, 2720, 3400, 5100, 1020, 0, 15, 48, 4, 0, ROOM_317, 10200, 0, 27710, 1024, UNLOCKED, 1);
// To booth.
door_aot_set(1, 21590, 8670, 1530, 850, 1, 0, 33, 1, 0, ROOM_319, 5185, 0, 4930, 1024, UNLOCKED, 193);
// To east-path.
door_aot_set(2, 31280, 14620, 1020, 3740, 0, 15, 48, 4, 0, ROOM_517, 4420, 0, 12750, 0, UNLOCKED, 1);
// To line-track.
door_aot_set(3, 1020, 10200, 1020, 3400, 0, 16, 48, 4, 0, ROOM_516, 29410, 0, 11900, 2048, UNLOCKED, 1);
// To car.
if (ck(FG_COMMON, 141, 1)) {
    aot_set(4, 10540, 17680, 1700, 1020, SCE_MESSAGE, 129, 129, 0, 255, 0, 0, 0);
} else {
    door_aot_set(4, 10540, 17680, 1700, 1020, 0, 1, 12, 7, 0, ROOM_216, 3485, 0, 2975, 3072, UNLOCKED, 193);
}
aot_set(5, 24480, 18020, 2040, 2380, SCE_MESSAGE, 129, 130, 0, 255, 0, 0, 0);
aot_set(6, 9520, 17510, 4420, 1190, SCE_MESSAGE, 129, 131, 0, 255, 0, 0, 0);
aot_set(7, 15640, 11390, 3060, 2040, SCE_MESSAGE, 129, 132, 0, 255, 0, 0, 0);
aot_set(8, 12070, 3400, 5100, 2040, SCE_MESSAGE, 129, 133, 0, 255, 0, 0, 0);
aot_set(9, 9860, 9860, 3740, 1700, SCE_MESSAGE, 129, 134, 0, 255, 0, 0, 0);
aot_set(10, 30600, 17340, 680, 1020, SCE_MESSAGE, 129, 135, 0, 255, 0, 0, 0);
enemy(5, 0, 186, 1, 2, 0, 0, 1760, 0, 0, 20760, 0, 21100, 0, 0, 0, 0);  // a crow
enemy(5, 0, 187, 1, 2, 0, 0, 2162, 0, 0, 14980, 0, 4100, 1, 0, 0, 0);  // a crow
// fit-cog (day/events.ts), FG_COMMON 139 once it has happened.
if (ck(FG_COMMON, 139, 1)) {
    aot_set(11, 2890, 15980, 4250, 3400, SCE_USEITEM, 1, 9, 0, 14, 0, 1, 0);   // the drive cog can be used here
    aot_set(12, 2890, 15980, 4250, 3400, SCE_MESSAGE, 129, 136, 0, 255, 0, 0, 0);
} else {
    aot_set(12, 2890, 15980, 4250, 3400, SCE_MESSAGE, 129, 137, 0, 255, 0, 0, 0);
}
// cut-gondola (day/cutscenes.ts): its people, and what starts it. FG_COMMON 122 once it has run.
return;

// main procedure 0
if (ck(FG_COMMON, 207, 1)) {
    set(FG_COMMON, 207, 0);
    message(128, 255, 0);
}
if (ck(FG_COMMON, 139, 1)) {
    if (ck(FG_ROOM, 12, 1) && testitem(41)) {
        set(FG_ROOM, 12, 0);
        setw(4, 0, 0);
    }
    if (ck(FG_ROOM, 12, 0) && cmpw(0, 4, 1, 0)) {
        set(FG_ROOM, 12, 1);
        if (item_ck(41)) {
            remove_item(41);
        }
        set(FG_COMMON, 139, 0);
        aot_set(12, 2890, 15980, 4250, 3400, SCE_MESSAGE, 129, 137, 0, 255, 0, 0, 0);
        message(138, 255, 0);
    }
}
if (ck(FG_COMMON, 122, 1) && ck(FG_STATUS, 15, 1) && ck(FG_COMMON, 141, 0)) {
    set(FG_COMMON, 122, 0);
    evt_exec(0, 9, 0);
}
return;

// event procedure 0
// cut-gondola (day/cutscenes.ts)
wait_voice();
scd {
    set(FG_COMMON, 122, 0);
    set(FG_STATUS, 15, 0);
    set(FG_6, 23, 1);
    return;
}
dir_set(0, 0, 3072, 0, 22355, 0, 10710);  // her
cutnext(2);
message(139, 0, 0);  // her
wait_voice();
// She walks to (14500, 14500).
set_entity(ENT_PLAYER, 0);
anim_begin();
    anim_pose(2, 14500, 14500, 62);
anim_end_release();
do {
    yield();
} while (ck(FG_ROOM, 62, 1));
message(140, 0, 0);  // her
wait_voice();
message(141, 0, 0);  // her
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
