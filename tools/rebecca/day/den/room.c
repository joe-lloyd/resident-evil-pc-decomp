// den (31B), written by day/scripts.ts from day/den/scene.py: edit the scene, not this file.
// init procedure 0
// To woods.
door_aot_set(0, 12750, 19380, 4250, 1020, 0, 15, 48, 4, 0, ROOM_31A, 15130, 0, 6120, 3072, UNLOCKED, 1);
if (ck(FG_ITEM, 160, 0)) {  // ranger keys (truck-keys)
    item_aot_set(1, 15923, 7913, 1200, 1200, 57, 1, 0, 255, 139, 64, 66, 0, 65, 33, 0, 0, 160, 129, 0, 0);
}
aot_set(2, 15714, 6483, 3400, 3400, SCE_MESSAGE, 129, 129, 0, 255, 0, 0, 0);
aot_set(3, 13600, 3400, 2380, 2380, SCE_MESSAGE, 129, 130, 0, 255, 0, 0, 0);
aot_set(4, 12070, 5440, 2040, 1360, SCE_MESSAGE, 129, 131, 0, 255, 0, 0, 0);
aot_set(5, 8500, 15300, 3230, 2720, SCE_MESSAGE, 129, 132, 0, 255, 0, 0, 0);
aot_set(6, 15470, 5185, 1700, 1700, SCE_MESSAGE, 129, 133, 0, 255, 0, 0, 0);
if (ck(FG_COMMON, 117, 0)) {
    enemy(2, 1, 190, 1, 2, 0, 0, 2637, 0, 0, 24500, 0, 6140, 0, 0, 0, 0);  // a cerberus
}
// cut-den (day/cutscenes.ts): its people, and what starts it. FG_COMMON 117 once it has run.
if (ck(FG_COMMON, 117, 1)) {
    enemy(33, 0, 255, 1, 2, 0, 0, 1024, 0, 0, 16000, 0, 10600, 6, 9, 24, 0);  // Dana
}
return;

// main procedure 0
if (ck(FG_COMMON, 117, 1) && ck(FG_STATUS, 15, 1)) {
    set(FG_COMMON, 117, 0);
    evt_exec(0, 9, 0);
}
return;

// event procedure 0
// cut-den (day/cutscenes.ts)
scd {
    set(FG_COMMON, 117, 0);
    set(FG_STATUS, 15, 0);
    set(FG_6, 23, 1);
    return;
}
dir_set(0, 0, 1024, 0, 15130, 0, 18020);  // her, in from woods
cutnext(0);
message(134, 0, 0);  // her
wait_voice();
// She walks to (15200, 13600).
set_entity(ENT_PLAYER, 0);
anim_begin();
    anim_pose(2, 15200, 13600, 62);
anim_end_release();
do {
    yield();
} while (ck(FG_ROOM, 62, 1));
set_entity(ENT_ENEMY, 6);
anim_begin();
    anim_play(34, 63, 0);
    anim_flags(0, 16);
anim_end();
message(135, 0, 0);  // Dana
wait_voice();
set_entity(ENT_ENEMY, 6);
anim_begin();
    anim_play(0, 63, 0);
    anim_flags(0, 16);
anim_end();
set_entity(ENT_ENEMY, 6);
anim_begin();
    anim_play(0, 62, 0);
    anim_flags(0, 16);
anim_end();
set_entity(ENT_ENEMY, 6);
anim_begin();
    anim_pose(6, 15200, 13600, 62);
anim_end();
do {
    yield();
} while (ck(FG_ROOM, 62, 1));
cutnext(2);
set_entity(ENT_ENEMY, 6);
anim_begin();
    anim_play(33, 63, 0);
    anim_flags(0, 16);
anim_end();
message(136, 0, 0);  // Dana
wait_voice();
set_entity(ENT_ENEMY, 6);
anim_begin();
    anim_play(0, 63, 0);
    anim_flags(0, 16);
anim_end();
// She takes the truck-keys.
scd {
    set(FG_6, 23, 0);
    give_item(1, 4, 129);
    return;
}
sleep(1);
set(FG_6, 23, 1);
set_entity(ENT_ENEMY, 6);
anim_begin();
    anim_play(37, 63, 0);
    anim_flags(0, 16);
anim_end();
message(137, 0, 0);  // Dana
wait_voice();
set_entity(ENT_ENEMY, 6);
anim_begin();
    anim_play(0, 63, 0);
    anim_flags(0, 16);
anim_end();
message(138, 0, 0);  // her
wait_voice();
set_entity(ENT_ENEMY, 6);
anim_begin();
    anim_play(35, 63, 0);
    anim_flags(0, 16);
anim_end();
message(139, 0, 0);  // Dana
wait_voice();
set_entity(ENT_ENEMY, 6);
anim_begin();
    anim_play(0, 63, 0);
    anim_flags(0, 16);
anim_end();
set_entity(ENT_ENEMY, 6);
anim_begin();
    anim_idle();
anim_end();
eml_state(0, 6, 2, 9, 0);
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
