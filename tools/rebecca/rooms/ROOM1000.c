// ROOM1000, the mansion 1F save room, in Rebecca's scenario.
// None of Chris's events run: the room's events are her day's scenes.
// Room messages are addressed as 0x80 + index: 174 is message 46, 175 is 47.
// init procedure 0
door_aot_set(0, 2700, 500, 1700, 1800, 3, 0, 0, 4, 0, ROOM_S01, 8700, 0, 7900, 1024, UNLOCKED, 129);
item_aot_set(4, 4260, 7790, 1800, 1800, 51 /* Sword Key */, 3, 0, 255, 40, 20, 94, 252, 242, 33, 66, 14, 22, 129, 0, 135);
eml_rot(0, 0, 0, 132, 3);
// Chris's game gives the item box only to a player who is not Rebecca.
aot_set(5, 6200, 2100, 2000, 1400, SCE_ITEMBOX, 129, 0, 0, 0, 0, 0, 0);
aot_set(8, 2300, 8750, 1600, 2000, SCE_TYPEWRITER, 129, 0, 0, 0, 0, 0, 0);
obj(0, 17, 255, 7480, -1410, 1780, -1024, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0);
tbl37_set(0, 0, 9);
// Her day ends here (day/cutscenes.ts, cut-sleep): she comes up through the
// hatch, sleeps against the wall, and Chris walks in. FG_COMMON 36 is the
// canon "Chris met Rebecca", which the scene sets.
// CUTSCENES INIT (day/scripts.ts writes these)
// cut-sleep (day/cutscenes.ts): its people, and what starts it. FG_COMMON 121 once it has run.
if (ck(FG_COMMON, 121, 1)) {
    enemy(32, 0, 255, 1, 2, 0, 0, 0, 0, 0, -30000, 0, -30000, 6, 0, 0, 0);  // Chris
}
// END CUTSCENES INIT
return;

// main procedure 0
// CUTSCENES MAIN (day/scripts.ts writes these)
if (ck(FG_COMMON, 121, 1) && ck(FG_ROOM, 13, 1)) {
    if (ck(FG_ROOM, 12, 0)) {
        eml_state(0, 6, 2, 9, 0);
        set(FG_ROOM, 13, 0);
    }
    set(FG_ROOM, 12, 0);
}
if (ck(FG_COMMON, 121, 1) && ck(FG_ROOM, 13, 0)) {
    set(FG_COMMON, 121, 0);
    evt_exec(0, 9, 0);
}
// END CUTSCENES MAIN
return;

// CUTSCENE EVENTS (day/scripts.ts writes these, to the end of the file)

// event procedure 0
// cut-sleep (day/cutscenes.ts)
scd {
    set(FG_COMMON, 121, 0);
    set(FG_STATUS, 15, 0);
    set(FG_6, 23, 1);
    return;
}
dir_set(0, 0, 443, 0, 5200, 0, 5600);  // her, in from crawl
cutnext(0);
message(176, 0, 0);  // her
wait_voice();
// She walks to (7100, 4200).
set_entity(ENT_PLAYER, 0);
anim_begin();
    anim_pose(2, 7100, 4200, 62);
anim_end_release();
do {
    yield();
} while (ck(FG_ROOM, 62, 1));
set_entity(ENT_PLAYER, 0);
anim_begin();
    anim_pose(6, 5200, 5600, 62);
anim_end_release();
do {
    yield();
} while (ck(FG_ROOM, 62, 1));
message(177, 0, 0);  // her
wait_voice();
message(178, 0, 0);  // her
wait_voice();
timer_setup(2, 0, 1, 7, 0);
sleep(120);
timer_setup(2, 0, 0, 7, 0);
sleep(90);
pos_set(6, 0, 0, 0, 3550, 0, 2700);  // Chris
message(179, 0, 0);  // her
wait_voice();
timer_setup(2, 0, 255, 7, 0);
sleep(150);
timer_setup(2, 0, 0, 7, 0);
// Chris walks to (5900, 4400).
set_entity(ENT_ENEMY, 6);
anim_begin();
    anim_pose(2, 5900, 4400, 62);
anim_end();
do {
    yield();
} while (ck(FG_ROOM, 62, 1));
set_entity(ENT_PLAYER, 0);
anim_begin();
    anim_pose(6, 5900, 4400, 62);
anim_end_release();
do {
    yield();
} while (ck(FG_ROOM, 62, 1));
set_entity(ENT_ENEMY, 6);
anim_begin();
    anim_play(34, 63, 0);
    anim_flags(0, 16);
anim_end();
message(180, 0, 0);  // Chris
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
message(181, 0, 0);  // Chris
wait_voice();
set_entity(ENT_ENEMY, 6);
anim_begin();
    anim_play(0, 63, 0);
    anim_flags(0, 16);
anim_end();
message(182, 0, 0);  // her
wait_voice();
set_entity(ENT_ENEMY, 6);
anim_begin();
    anim_play(37, 63, 0);
    anim_flags(0, 16);
anim_end();
message(183, 0, 0);  // Chris
wait_voice();
set_entity(ENT_ENEMY, 6);
anim_begin();
    anim_play(0, 63, 0);
    anim_flags(0, 16);
anim_end();
message(184, 0, 0);  // her
wait_voice();
set_entity(ENT_ENEMY, 6);
anim_begin();
    anim_play(35, 63, 0);
    anim_flags(0, 16);
anim_end();
message(185, 0, 0);  // Chris
wait_voice();
set_entity(ENT_ENEMY, 6);
anim_begin();
    anim_play(0, 63, 0);
    anim_flags(0, 16);
anim_end();
// Chris walks to (3550, 2700).
set_entity(ENT_ENEMY, 6);
anim_begin();
    anim_pose(2, 3550, 2700, 62);
anim_end();
do {
    yield();
} while (ck(FG_ROOM, 62, 1));
pos_set(6, 0, 0, 0, -30000, 0, -30000);  // Chris leaves
set(FG_COMMON, 36, 0);  // canon: Chris met Rebecca
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
