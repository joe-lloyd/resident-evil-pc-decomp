// The ranger's lookout (ROOM3140), inside: a one-room log cabin, the morning
// after. The ranger left in a hurry: breakfast half eaten, a chair knocked
// over, his rifle gone, the east window smashed in with blood on the sill.
// His logbook says the crank for the truck's winch is in the shed; the shed
// key hangs on the board by the door.
//
// Game units are metres * 1700 (scene.py builds the room in metres).
// FG_COMMON 201: she has been in before. FG_ITEM 241: the spray is still on
// the table, 242: the shed key is still on its hook, 244: the ink ribbons are
// still by the typewriter (bit set = still there).
// item_aot_set operands after the model index: 255, the model's position
// (X, Y, Z as little-endian 16-bit pairs), two rotation bytes, the item flag,
// then 129 (taken with the action key), 0, 0.
// message(n, 255, 0): the 255 pauses the game under the message, as Chris's
// scripts do. Room messages are 0x80 + index: 128 is message 0.
// init procedure 0
// The door out to the yard (ROOM3150): she comes out onto the porch steps,
// facing the yard (+Z, angle 0xC00).
door_aot_set(0, 5950, 9100, 1530, 1100, 0, 0, 0, 4, 0, ROOM_315, 22015, 0, 13515, 3072, UNLOCKED, 129);
// On the table by the cards: the First Aid Spray, model at (7276, -1292, 7310).
if (ck(FG_ITEM, 241, 0)) {
    item_aot_set(1, 6120, 6630, 1700, 1700, 65 /* F-Aid Spray */, 1, 0, 255, 108, 28, 244, 250, 142, 28, 0, 0, 241, 129, 0, 0);
}
// On the key board by the door: the shed key, model at (5576, -2414, 10132).
if (ck(FG_ITEM, 242, 0)) {
    item_aot_set(2, 4930, 9095, 935, 1105, 61 /* Small Key */, 1, 1, 255, 200, 21, 146, 246, 148, 39, 0, 0, 242, 129, 0, 0);
}
aot_set(3, 4335, 4675, 850, 935, SCE_MESSAGE, 129, 129, 0, 255, 0, 0, 0);   // the radio
aot_set(4, 5880, 4675, 800, 935, SCE_MESSAGE, 129, 130, 0, 255, 0, 0, 0);   // the logbook, from the open side of the desk chair
aot_set(5, 9520, 7480, 765, 2550, SCE_MESSAGE, 129, 131, 0, 255, 0, 0, 0);  // the bunk
aot_set(6, 4590, 7310, 850, 1360, SCE_MESSAGE, 129, 132, 0, 255, 0, 0, 0);  // the stove
aot_set(7, 10880, 4420, 1020, 1020, SCE_MESSAGE, 129, 133, 0, 255, 0, 0, 0); // the broken window, its north part: the item box is below the rest
aot_set(8, 8500, 9180, 1530, 1020, SCE_MESSAGE, 129, 134, 0, 255, 0, 0, 0);  // the empty rifle rack
aot_set(9, 7820, 5440, 1190, 714, SCE_MESSAGE, 129, 135, 0, 255, 0, 0, 0);   // breakfast
aot_set(10, 3485, 4760, 765, 935, SCE_MESSAGE, 129, 136, 0, 255, 0, 0, 0);   // the survey map
aot_set(11, 7565, 9180, 850, 1020, SCE_MESSAGE, 129, 137, 0, 255, 0, 0, 0);  // his hat
aot_set(12, 7820, 4080, 2040, 850, SCE_MESSAGE, 129, 138, 0, 255, 0, 0, 0);  // the shelves
// Where she saves, as in the mansion's save room (ROOM1000): the ink ribbons
// beside the typewriter on the corner table (RE1's own ribbon model, from
// ROOM30E0), the typewriter, and the item box at the bunk's foot. Its lid is
// RE1's own object model 0 (from ROOM1000), shrunk with the box to a
// footlocker (scene.py, scale 0.65), hinged at its back edge and opening north
// (angle 1024). The box's zone starts where the broken window's ends.
if (ck(FG_ITEM, 244, 0)) {
    item_aot_set(13, 11305, 3400, 595, 1020, 47 /* Ink Ribbon */, 3, 2, 255, 91, 45, 56, 251, 241, 14, 0, 0, 244, 129, 0, 0);
}
aot_set(14, 10455, 3400, 850, 1020, SCE_TYPEWRITER, 129, 0, 0, 0, 0, 0, 0);
aot_set(15, 10285, 5525, 1530, 1615, SCE_ITEMBOX, 129, 0, 0, 0, 0, 0, 0);
obj(0, 17, 255, 11050, -936, 7106, 1024, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0);
return;

// main procedure 0
if (ck(FG_COMMON, 201, 1)) {
    set(FG_COMMON, 201, 0);
    message(128, 255, 0);
}
return;
