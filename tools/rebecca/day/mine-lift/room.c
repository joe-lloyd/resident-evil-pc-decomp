// mine-lift (509), written by day/scripts.ts from day/mine-lift/scene.py: edit the scene, not this file.
// init procedure 0
// To junction.
door_aot_set(0, 1870, 3553, 2890, 1292, 0, 1, 8, 0, 0, ROOM_51E, 12240, 0, 6120, 3072, UNLOCKED, 193);
// To summit-trail.
if (ck(FG_COMMON, 136, 1)) {
    aot_set(1, 1870, 1190, 2890, 1292, SCE_MESSAGE, 129, 129, 0, 255, 0, 0, 0);
} else {
    door_aot_set(1, 1870, 1190, 2890, 1292, 0, 14, 20, 64, 0, ROOM_213, 26180, 0, 16490, 1024, UNLOCKED, 193);
}
aot_set(2, 2380, 2482, 1530, 1071, SCE_MESSAGE, 129, 130, 0, 255, 0, 0, 0);
aot_set(3, 1190, 2482, 1190, 1071, SCE_MESSAGE, 129, 131, 0, 255, 0, 0, 0);
// lift-up (day/events.ts), FG_COMMON 136 once it has happened.
if (ck(FG_COMMON, 136, 1)) {
    aot_set(4, 3910, 2482, 1530, 1071, SCE_USEITEM, 129, 4, 0, 12, 0, 1, 0);   // the action button here raises FG_ROOM 12
} else {
    aot_set(5, 3910, 2482, 1530, 1071, SCE_MESSAGE, 129, 133, 0, 255, 0, 0, 0);
}
// cut-mine-chase (day/cutscenes.ts): its people, and what starts it. FG_COMMON 127 once it has run.
return;

// main procedure 0
if (ck(FG_COMMON, 136, 1) && ck(FG_ROOM, 12, 0)) {
    set(FG_ROOM, 12, 1);
    if (ck(FG_COMMON, 131, 0)) {
        set(FG_COMMON, 136, 0);
        door_aot_set(1, 1870, 1190, 2890, 1292, 0, 14, 20, 64, 0, ROOM_213, 26180, 0, 16490, 1024, UNLOCKED, 193);
        aot_set(5, 3910, 2482, 1530, 1071, SCE_MESSAGE, 129, 133, 0, 255, 0, 0, 0);
        message(134, 255, 0);
    } else {
        message(132, 255, 0);
    }
}
if (ck(FG_COMMON, 127, 1) && ck(FG_STATUS, 15, 1) && ck(FG_COMMON, 118, 0) && ck(FG_COMMON, 119, 0)) {
    set(FG_COMMON, 127, 0);
    evt_exec(0, 9, 0);
}
return;

// event procedure 0
// cut-mine-chase (day/cutscenes.ts)
scd {
    set(FG_COMMON, 127, 0);
    set(FG_STATUS, 15, 0);
    set(FG_6, 23, 1);
    return;
}
dir_set(0, 0, 1024, 0, 3315, 0, 2805);  // her, in from junction
cutnext(1);
// She runs to (3315, 2500).
set_entity(ENT_PLAYER, 0);
anim_begin();
    anim_pose(3, 3315, 2500, 62);
anim_end_release();
do {
    yield();
} while (ck(FG_ROOM, 62, 1));
set_entity(ENT_PLAYER, 0);
anim_begin();
    anim_pose(6, 3315, 5000, 62);
anim_end_release();
do {
    yield();
} while (ck(FG_ROOM, 62, 1));
message(135, 0, 0);  // her
wait_voice();
message(136, 0, 0);  // her
wait_voice();
cutnext(0);
set_entity(ENT_PLAYER, 0);
anim_begin();
    anim_pose(6, 4500, 3000, 62);
anim_end_release();
do {
    yield();
} while (ck(FG_ROOM, 62, 1));
message(137, 0, 0);  // her
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
