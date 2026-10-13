// The ravine bridge (ROOM3170), below the ranger station, mid-morning. A
// plank footbridge over a gorge; adders in the near bank's long grass; the
// valley trail going on down from the far bank. Act 1 ends at its sign.
//
// Game units are metres * 1700 (scene.py). FG_COMMON 204: she has been here
// before. FG_COMMON 206: she has read the valley trail sign (the end of Act 1
// for now). cmpb(16, 0, n) holds on the frame she presses action at zone n - 1.
// Outdoor doors walk rather than open: door bytes 0, 15, 48 play walk 0 with
// the footsteps of sound row 15 (src/game/PathWalk.cpp).
// init procedure 0
// Back up to the yard, on touch at the near bank's north edge: she comes out
// on the trail below the fallen pine, facing up it (-Z). She arrives here at
// Z 6120, well clear of it: a touch door fires when the spot 600 ahead of her
// is inside, and the walk planner backs up to get round things.
door_aot_set(0, 8500, 3400, 3400, 680, 0, 15, 48, 4, 0, ROOM_315, 26690, 0, 18530, 1024, UNLOCKED, 1);
aot_set(1, 5950, 27880, 8500, 1020, SCE_MESSAGE, 129, 129, 0, 255, 0, 0, 0);   // the valley trail sign
aot_set(2, 8500, 10540, 3400, 1360, SCE_MESSAGE, 129, 130, 0, 255, 0, 0, 0);   // the bridge's near end
aot_set(3, 3400, 10880, 5100, 1020, SCE_MESSAGE, 129, 131, 0, 255, 0, 0, 0);   // the drop, west of it
aot_set(4, 11900, 10880, 5100, 1020, SCE_MESSAGE, 129, 131, 0, 255, 0, 0, 0);  // the drop, east of it
// Adders in the long grass of the near bank.
enemy(10 /* Adder */, 1, 255, 1, 1, 0, 0, 1024, 0, 0, 5100, 0, 8500, 0, 0, 0, 0);
enemy(10 /* Adder */, 1, 255, 1, 1, 0, 0, 3072, 0, 0, 14450, 0, 6800, 1, 0, 0, 0);
enemy(10 /* Adder */, 1, 255, 1, 1, 0, 0, 2048, 0, 0, 13600, 0, 10200, 2, 0, 0, 0);
// KIT DOORS (day/scripts.ts writes these)
// On down to the gondola station, from the far bank's south edge.
door_aot_set(5, 6800, 29580, 6800, 1020, 0, 15, 48, 4, 0, ROOM_318, 7820, 0, 5780, 3072, UNLOCKED, 1);
// END KIT DOORS
return;

// main procedure 0
if (ck(FG_COMMON, 204, 1)) {
    set(FG_COMMON, 204, 0);
    message(128, 255, 0);
}
if (ck(FG_COMMON, 206, 1) && cmpb(16, 0, 2)) {
    set(FG_COMMON, 206, 0);
}
return;
