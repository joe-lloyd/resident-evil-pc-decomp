// crash (21B), written by day/scripts.ts from day/crash/scene.py: edit the scene, not this file.
// init procedure 0
// To valley-path.
door_aot_set(0, 31280, 12920, 1020, 3740, 0, 15, 48, 4, 0, ROOM_218, 4420, 0, 15470, 0, UNLOCKED, 1);
if (ck(FG_ITEM, 168, 0)) {  // crowbar (crowbar)
    item_aot_set(1, 8920, 17930, 1200, 1200, 43, 1, 2, 255, 48, 37, 250, 255, 98, 72, 0, 0, 168, 129, 0, 0);
}
aot_set(2, 10540, 14280, 2380, 1700, SCE_MESSAGE, 129, 129, 0, 255, 0, 0, 0);
aot_set(3, 14280, 14280, 2720, 1360, SCE_MESSAGE, 129, 130, 0, 255, 0, 0, 0);
aot_set(4, 11560, 16830, 2720, 1700, SCE_MESSAGE, 129, 131, 0, 255, 0, 0, 0);
aot_set(5, 14790, 15640, 4760, 2890, SCE_MESSAGE, 129, 132, 0, 255, 0, 0, 0);
aot_set(6, 9520, 15300, 2040, 1530, SCE_MESSAGE, 129, 133, 0, 255, 0, 0, 0);
aot_set(7, 20570, 6800, 5100, 4420, SCE_MESSAGE, 129, 134, 0, 255, 0, 0, 0);
aot_set(8, 18700, 18870, 1700, 1700, SCE_MESSAGE, 129, 135, 0, 255, 0, 0, 0);
aot_set(9, 22270, 12410, 3230, 3400, SCE_MESSAGE, 129, 136, 0, 255, 0, 0, 0);
aot_set(10, 29750, 12920, 1870, 1020, SCE_MESSAGE, 129, 137, 0, 255, 0, 0, 0);
aot_set(11, 26860, 14280, 2380, 1020, SCE_MESSAGE, 129, 138, 0, 255, 0, 0, 0);
if (ck(FG_ITEM, 196, 0)) {  // beretta
    item_aot_set(12, 1120, 4860, 1200, 1200, 2, 15, 0, 255, 184, 6, 0, 0, 84, 21, 0, 0, 196, 129, 0, 0);
}
if (ck(FG_ITEM, 197, 0)) {  // clip
    item_aot_set(13, 1120, 22200, 1200, 1200, 11, 15, 1, 255, 184, 6, 0, 0, 16, 89, 0, 0, 197, 129, 0, 0);
}
// cut-kevin (day/cutscenes.ts): its people, and what starts it. FG_COMMON 120 once it has run.
return;

// main procedure 0
if (ck(FG_COMMON, 248, 1)) {
    set(FG_COMMON, 248, 0);
}
if (ck(FG_COMMON, 120, 1) && ck(FG_STATUS, 15, 1)) {
    set(FG_COMMON, 120, 0);
    evt_exec(0, 9, 0);
}
return;

// event procedure 0
// cut-kevin (day/cutscenes.ts)
scd {
    set(FG_COMMON, 120, 0);
    set(FG_STATUS, 15, 0);
    set(FG_6, 23, 1);
    return;
}
dir_set(0, 0, 2048, 0, 29750, 0, 14790);  // her, in from valley-path
cutnext(7);
message(139, 0, 0);  // her
wait_voice();
// She walks to (24500, 14000).
set_entity(ENT_PLAYER, 0);
anim_begin();
    anim_pose(2, 24500, 14000, 62);
anim_end_release();
do {
    yield();
} while (ck(FG_ROOM, 62, 1));
cutnext(3);
sleep(30);
message(140, 0, 0);  // her
wait_voice();
message(141, 0, 0);  // her
wait_voice();
message(142, 0, 0);  // her
wait_voice();
sleep(30);
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
