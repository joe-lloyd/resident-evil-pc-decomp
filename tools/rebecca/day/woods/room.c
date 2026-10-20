// woods (31A), written by day/scripts.ts from day/woods/scene.py: edit the scene, not this file.
// init procedure 0
// To yard.
door_aot_set(0, 3400, 11900, 1020, 3400, 0, 15, 48, 4, 0, ROOM_315, 28560, 0, 10200, 2048, UNLOCKED, 1);
// To den.
door_aot_set(1, 12750, 3400, 4250, 1020, 0, 15, 48, 4, 0, ROOM_31B, 15130, 0, 18020, 1024, UNLOCKED, 1);
// To logging-road.
door_aot_set(2, 29580, 15300, 1020, 4250, 0, 15, 48, 4, 0, ROOM_31C, 4420, 0, 13940, 0, UNLOCKED, 1);
aot_set(3, 4930, 15300, 2040, 2210, SCE_MESSAGE, 129, 129, 0, 255, 0, 0, 0);
aot_set(4, 4420, 13260, 2210, 2040, SCE_MESSAGE, 129, 130, 0, 255, 0, 0, 0);
aot_set(5, 10030, 10370, 1870, 1700, SCE_MESSAGE, 129, 131, 0, 255, 0, 0, 0);
aot_set(6, 12750, 9180, 1870, 1700, SCE_MESSAGE, 129, 132, 0, 255, 0, 0, 0);
aot_set(7, 11560, 6800, 1870, 1530, SCE_MESSAGE, 129, 133, 0, 255, 0, 0, 0);
aot_set(8, 13260, 5100, 3060, 2720, SCE_MESSAGE, 129, 134, 0, 255, 0, 0, 0);
aot_set(9, 20400, 7820, 3570, 3230, SCE_MESSAGE, 129, 135, 0, 255, 0, 0, 0);
aot_set(10, 28220, 19890, 2380, 2550, SCE_MESSAGE, 129, 136, 0, 255, 0, 0, 0);
if (ck(FG_COMMON, 116, 0)) {
    enemy(2, 1, 188, 1, 2, 0, 0, 2988, 0, 0, 29600, 0, 4100, 0, 0, 0, 0);  // a cerberus
    enemy(2, 1, 189, 1, 2, 0, 0, 1554, 0, 0, 15660, 0, 22800, 1, 0, 0, 0);  // a cerberus
}
// cut-partner (day/cutscenes.ts): its people, and what starts it. FG_COMMON 116 once it has run.
if (ck(FG_COMMON, 116, 1)) {
    enemy(33, 0, 255, 1, 2, 0, 0, 1024, 0, 0, 11300, 0, 10000, 6, 9, 24, 0);  // Dana
}
return;

// main procedure 0
if (ck(FG_COMMON, 209, 1)) {
    set(FG_COMMON, 209, 0);
}
if (ck(FG_COMMON, 116, 1) && ck(FG_STATUS, 15, 1)) {
    set(FG_COMMON, 116, 0);
    evt_exec(0, 9, 0);
}
return;

// event procedure 0
// cut-partner (day/cutscenes.ts)
scd {
    set(FG_COMMON, 116, 0);
    set(FG_STATUS, 15, 0);
    set(FG_6, 23, 1);
    return;
}
dir_set(0, 0, 0, 0, 6120, 0, 13770);  // her, in from yard
cutnext(0);
message(137, 0, 0);  // her
wait_voice();
message(138, 0, 0);  // her
wait_voice();
// She walks to (9600, 10600).
set_entity(ENT_PLAYER, 0);
anim_begin();
    anim_pose(2, 9600, 10600, 62);
anim_end_release();
do {
    yield();
} while (ck(FG_ROOM, 62, 1));
cutnext(4);
message(139, 0, 0);  // her
wait_voice();
set_entity(ENT_ENEMY, 6);
anim_begin();
    anim_play(0, 62, 0);
    anim_flags(0, 16);
anim_end();
set_entity(ENT_ENEMY, 6);
anim_begin();
    anim_pose(6, 9600, 10600, 62);
anim_end();
do {
    yield();
} while (ck(FG_ROOM, 62, 1));
set_entity(ENT_ENEMY, 6);
anim_begin();
    anim_play(34, 63, 0);
    anim_flags(0, 16);
anim_end();
message(140, 0, 0);  // Dana
wait_voice();
set_entity(ENT_ENEMY, 6);
anim_begin();
    anim_play(0, 63, 0);
    anim_flags(0, 16);
anim_end();
set_entity(ENT_ENEMY, 6);
anim_begin();
    anim_play(33, 63, 0);
    anim_flags(0, 16);
anim_end();
message(141, 0, 0);  // Dana
wait_voice();
set_entity(ENT_ENEMY, 6);
anim_begin();
    anim_play(0, 63, 0);
    anim_flags(0, 16);
anim_end();
message(142, 0, 0);  // her
wait_voice();
set_entity(ENT_ENEMY, 6);
anim_begin();
    anim_play(37, 63, 0);
    anim_flags(0, 16);
anim_end();
message(143, 0, 0);  // Dana
wait_voice();
set_entity(ENT_ENEMY, 6);
anim_begin();
    anim_play(0, 63, 0);
    anim_flags(0, 16);
anim_end();
message(144, 0, 0);  // her
wait_voice();
set_entity(ENT_ENEMY, 6);
anim_begin();
    anim_play(35, 63, 0);
    anim_flags(0, 16);
anim_end();
message(145, 0, 0);  // Dana
wait_voice();
set_entity(ENT_ENEMY, 6);
anim_begin();
    anim_play(0, 63, 0);
    anim_flags(0, 16);
anim_end();
message(146, 0, 0);  // her
wait_voice();
set_entity(ENT_ENEMY, 6);
anim_begin();
    anim_play(34, 63, 0);
    anim_flags(0, 16);
anim_end();
message(147, 0, 0);  // Dana
wait_voice();
set_entity(ENT_ENEMY, 6);
anim_begin();
    anim_play(0, 63, 0);
    anim_flags(0, 16);
anim_end();
// Dana walks to (14000, 5600).
set_entity(ENT_ENEMY, 6);
anim_begin();
    anim_pose(2, 14000, 5600, 62);
anim_end();
do {
    yield();
} while (ck(FG_ROOM, 62, 1));
pos_set(6, 0, 0, 0, -30000, 0, -30000);  // Dana leaves
message(148, 0, 0);  // her
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
