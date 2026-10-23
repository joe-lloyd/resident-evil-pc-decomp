// tower-top (41E), written by day/scripts.ts from day/tower-top/scene.py: edit the scene, not this file.
// init procedure 0
// To tower-stairs.
door_aot_set(0, 5865, 8160, 5100, 2720, 1, 11, 27, 64, 0, ROOM_41D, 12240, 0, 5270, 1024, UNLOCKED, 193);
if (ck(FG_ITEM, 164, 0)) {  // switch key (switch-key)
    item_aot_set(1, 10300, 6050, 1500, 1500, 55, 1, 1, 255, 42, 43, 74, 250, 144, 26, 0, 0, 164, 129, 0, 0);
}
if (ck(FG_ITEM, 189, 0)) {  // clip
    item_aot_set(2, 14400, 4880, 1200, 1200, 11, 15, 0, 255, 152, 58, 0, 0, 104, 21, 0, 0, 189, 129, 0, 0);
}
aot_set(3, 10200, 10200, 2720, 2720, SCE_MESSAGE, 129, 129, 0, 255, 0, 0, 0);
// Lookout log, a file.
if (ck(FG_ITEM, 234, 0)) {
    item_aot_set(4, 10030, 5780, 2210, 2040, 105, 1, 2, 255, 0, 0, 0, 0, 0, 0, 0, 0, 234, 129, 0, 0);
}
aot_set(5, 12240, 6290, 2040, 1530, SCE_MESSAGE, 129, 130, 0, 255, 0, 0, 0);
aot_set(6, 11900, 12920, 1870, 1700, SCE_MESSAGE, 129, 131, 0, 255, 0, 0, 0);
aot_set(7, 12410, 7480, 510, 3230, SCE_MESSAGE, 129, 132, 0, 255, 0, 0, 0);
aot_set(8, 14110, 11050, 2210, 3400, SCE_MESSAGE, 129, 133, 0, 255, 0, 0, 0);
aot_set(9, 14280, 4080, 2040, 4420, SCE_MESSAGE, 129, 134, 0, 255, 0, 0, 0);
if (ck(FG_COMMON, 124, 0)) {
    enemy(5, 0, 211, 1, 2, 0, 0, 2387, 0, 0, 14810, 0, 6990, 0, 0, 0, 0);  // a crow
    enemy(5, 0, 212, 1, 2, 0, 0, 1887, 0, 0, 14810, 0, 13450, 1, 0, 0, 0);  // a crow
}
// cut-tower (day/cutscenes.ts): its people, and what starts it. FG_COMMON 124 once it has run.
return;

// main procedure 0
if (ck(FG_COMMON, 124, 1) && ck(FG_STATUS, 15, 1)) {
    set(FG_COMMON, 124, 0);
    evt_exec(0, 9, 0);
}
return;

// event procedure 0
// cut-tower (day/cutscenes.ts)
scd {
    set(FG_COMMON, 124, 0);
    set(FG_STATUS, 15, 0);
    set(FG_6, 23, 1);
    return;
}
dir_set(0, 0, 3072, 0, 6970, 0, 11475);  // her, in from tower-stairs
cutnext(3);
sleep(40);
message(135, 0, 0);  // her
wait_voice();
message(136, 0, 0);  // her
wait_voice();
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
