// The ridge (ROOM3130): where Rebecca's day begins, at dawn on 24 July 1998.
// She has just watched Billy go into the trees. The cliff edge looks down on
// the training facility, still burning in the valley; the trail down leaves
// through the pines on the east side, by a touch door to the mountain trail.
//
// The opening is a cutscene (day/cutscenes.ts, cut-opening), which
// day/scripts.ts writes between the CUTSCENES markers.
// message(n, 255, 0): the 255 is the mask of message flags cleared while it
// is up, which pauses the game the way Chris's scripts do; with 0 she can
// still act under the message box.
// Room messages are 0x80 + index: 128 is message 0. The scene's follow the room's own.
// Outdoor doors walk rather than open: door bytes 0, 15, 48 play walk 0 with
// the footsteps of sound row 15 (src/game/PathWalk.cpp).
// init procedure 0
door_aot_set(0, 11400, 3800, 1600, 3000, 0, 15, 48, 4, 0, ROOM_312, 3500, 0, 1200, 3072, UNLOCKED, 1);
// The edge, all along the south side of the clearing.
aot_set(1, 3000, 9200, 8000, 1000, SCE_MESSAGE, 129, 129, 0, 255, 0, 0, 0);
// The rock face at the back.
aot_set(2, 3000, 3000, 8000, 900, SCE_MESSAGE, 129, 130, 0, 255, 0, 0, 0);
// CUTSCENES INIT (day/scripts.ts writes these)
// cut-opening (day/cutscenes.ts): its people, and what starts it. FG_COMMON 125 once it has run.
// END CUTSCENES INIT
return;

// main procedure 0
// CUTSCENES MAIN (day/scripts.ts writes these)
if (ck(FG_COMMON, 125, 1) && ck(FG_STATUS, 15, 1)) {
    set(FG_COMMON, 125, 0);
    evt_exec(0, 9, 0);
}
// END CUTSCENES MAIN
return;

// CUTSCENE EVENTS (day/scripts.ts writes these, to the end of the file)

// event procedure 0
// cut-opening (day/cutscenes.ts)
scd {
    set(FG_COMMON, 125, 0);
    set(FG_STATUS, 15, 0);
    set(FG_6, 23, 1);
    return;
}
cutnext(0);
dir_set(0, 0, 3072, 0, 7000, 0, 6200);  // her
sleep(30);
message(131, 0, 0);  // her
wait_voice();
message(132, 0, 0);  // her
wait_voice();
// She walks to (7000, 8400).
set_entity(ENT_PLAYER, 0);
anim_begin();
    anim_pose(2, 7000, 8400, 62);
anim_end_release();
do {
    yield();
} while (ck(FG_ROOM, 62, 1));
sleep(20);
message(133, 0, 0);  // her
wait_voice();
message(134, 0, 0);  // her
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
