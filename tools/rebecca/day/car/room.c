// car (216), written by day/scripts.ts from day/car/scene.py: edit the scene, not this file.
// init procedure 0
// To platform.
door_aot_set(0, 2720, 1190, 1530, 1275, 0, 1, 12, 7, 0, ROOM_318, 11730, 0, 16830, 1024, UNLOCKED, 193);
// To pylon.
door_aot_set(1, 4165, 2380, 867, 1020, 1, 11, 27, 64, 0, ROOM_217, 5440, 0, 7905, 0, UNLOCKED, 193);
aot_set(2, 1190, 1700, 2040, 2380, SCE_MESSAGE, 129, 129, 0, 255, 0, 0, 0);
aot_set(3, 3570, 1785, 1445, 935, SCE_MESSAGE, 129, 130, 0, 255, 0, 0, 0);
aot_set(4, 2550, 3230, 1530, 1360, SCE_MESSAGE, 129, 131, 0, 255, 0, 0, 0);
aot_set(5, 2720, 2465, 1530, 765, SCE_MESSAGE, 129, 132, 0, 255, 0, 0, 0);
aot_set(6, 4930, 1700, 1360, 2890, SCE_MESSAGE, 129, 133, 0, 255, 0, 0, 0);
// cut-pylon (day/cutscenes.ts): its people, and what starts it. FG_COMMON 123 once it has run.
return;

// main procedure 0
if (ck(FG_COMMON, 123, 1) && ck(FG_STATUS, 15, 1)) {
    set(FG_COMMON, 123, 0);
    evt_exec(0, 9, 0);
}
return;

// event procedure 0
// cut-pylon (day/cutscenes.ts)
scd {
    set(FG_COMMON, 123, 0);
    set(FG_STATUS, 15, 0);
    set(FG_6, 23, 1);
    return;
}
dir_set(0, 0, 3072, 0, 3485, 0, 2975);  // her, in from platform
cutnext(1);
set(FG_STATUS, 62, 0);
message(134, 0, 0);  // her
wait_voice();
sleep(60);
set(FG_STATUS, 62, 1);
sleep(30);
message(135, 0, 0);  // her
wait_voice();
set(FG_STATUS, 62, 0);
sleep(8);
set(FG_STATUS, 62, 1);
message(136, 0, 0);  // her
wait_voice();
cutnext(0);
sleep(20);
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
