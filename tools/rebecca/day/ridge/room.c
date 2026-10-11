// The ridge (ROOM3130): where Rebecca's day begins, at dawn on 24 July 1998.
// She has just watched Billy go into the trees. The cliff edge looks down on
// the training facility, still burning in the valley; the trail down leaves
// through the pines on the east side, by a touch door to the mountain trail.
//
// FG_COMMON 200: the opening has played.
// Room messages are 0x80 + index: 128 is message 0.
// init procedure 0
door_aot_set(0, 11400, 3800, 1600, 3000, 0, 0, 0, 4, 0, ROOM_312, 3500, 0, 1200, 3072, UNLOCKED, 1);
// The edge, all along the south side of the clearing.
aot_set(1, 3000, 9200, 8000, 1000, SCE_MESSAGE, 129, 130, 0, 255, 0, 0, 0);
// The rock face at the back.
aot_set(2, 3000, 3000, 8000, 900, SCE_MESSAGE, 129, 131, 0, 255, 0, 0, 0);
return;

// main procedure 0
if (ck(FG_COMMON, 200, 1)) {
    set(FG_COMMON, 200, 0);
    message(128, 0, 0);
}
return;
