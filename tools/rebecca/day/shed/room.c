// The ranger's tool shed (ROOM3160), inside. The winch's crank is on the
// workbench beside the chainsaw he gave up on.
//
// Game units are metres * 1700 (scene.py). FG_COMMON 203: she has been in
// before. FG_ITEM 243: the crank is still on the bench (bit set = still there);
// 244 and 245 the jerrycan and the fuses. Her key items' names are
// items/items.ts.
// init procedure 0
// Out to the yard: outside the shed door, facing east (+X, angle 0).
door_aot_set(0, 5100, 2890, 1020, 1360, 1, 0, 7, 1, 0, ROOM_315, 10880, 0, 13090, 0, UNLOCKED, 129);
// On the bench: the Hex Crank, model at (2346, -1581, 3825).
if (ck(FG_ITEM, 243, 0)) {
    // Two uses (the slot's count): the winch and the pond's sluice each spend one.
    item_aot_set(1, 2805, 3145, 1105, 1360, 30 /* Hex Crank */, 2, 0, 255, 42, 9, 211, 249, 241, 14, 0, 0, 243, 129, 0, 0);
}
aot_set(2, 2805, 1955, 935, 1105, SCE_MESSAGE, 129, 129, 0, 255, 0, 0, 0);   // the chainsaw in pieces
aot_set(3, 3740, 1700, 2040, 850, SCE_MESSAGE, 129, 130, 0, 255, 0, 0, 0);   // the pegboard
aot_set(4, 4420, 4420, 1530, 425, SCE_MESSAGE, 129, 131, 0, 255, 0, 0, 0);   // the fuel cans
// By the fuel cans: an empty jerrycan (JERRYCAN, item 31), model slot 1 at
// (4590, 0, 4845). FG_ITEM 244: still there.
if (ck(FG_ITEM, 244, 0)) {
    item_aot_set(5, 3910, 4165, 1360, 1360, 31, 1, 1, 255, 238, 17, 0, 0, 237, 18, 0, 0, 244, 129, 0, 0);
}
// On the bench by the nail can: the ranger's spare fuses (FUSES, item 39),
// model slot 2 at (2414, -1564, 4335). FG_ITEM 245: still there.
if (ck(FG_ITEM, 245, 0)) {
    item_aot_set(6, 2805, 4505, 1105, 850, 39, 1, 2, 255, 110, 9, 228, 249, 239, 16, 0, 0, 245, 129, 0, 0);
}
return;

// main procedure 0
if (ck(FG_COMMON, 203, 1)) {
    set(FG_COMMON, 203, 0);
    message(128, 255, 0);
}
return;
