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
// The logbook, a file (tools/rebecca/files/documents.ts): item 0x5F, on the
// room's empty model slot 3 (after the spray, the key and the ink ribbons), flag 230. Taken
// from the open side of the desk chair.
if (ck(FG_ITEM, 230, 0)) {
    item_aot_set(4, 5880, 4675, 800, 935, 95 /* Ranger's logbook */, 1, 3, 255, 0, 0, 0, 0, 0, 0, 0, 0, 230, 129, 0, 0);
}
aot_set(5, 9520, 7480, 765, 2550, SCE_MESSAGE, 129, 130, 0, 255, 0, 0, 0);  // the bunk
aot_set(6, 4590, 7310, 850, 1360, SCE_MESSAGE, 129, 131, 0, 255, 0, 0, 0);  // the stove
aot_set(7, 10880, 4420, 1020, 1020, SCE_MESSAGE, 129, 132, 0, 255, 0, 0, 0); // the broken window, its north part: the item box is below the rest
aot_set(8, 8500, 9180, 1530, 1020, SCE_MESSAGE, 129, 133, 0, 255, 0, 0, 0);  // the empty rifle rack
aot_set(9, 7820, 5440, 1190, 714, SCE_MESSAGE, 129, 134, 0, 255, 0, 0, 0);   // breakfast
aot_set(10, 3485, 4760, 765, 935, SCE_MESSAGE, 129, 135, 0, 255, 0, 0, 0);   // the survey map
aot_set(11, 7565, 9180, 850, 1020, SCE_MESSAGE, 129, 136, 0, 255, 0, 0, 0);  // his hat
aot_set(12, 7820, 4080, 2040, 850, SCE_MESSAGE, 129, 137, 0, 255, 0, 0, 0);  // the shelves
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
// The proof for her day's two people (tools/rebecca/npc/people.ts): Hal in
// Barry's model (id 34), in the open floor north-east, and Dana, the
// ranger's partner, in Jill's NPC model (id 33) by the desk, both facing the
// south-west camera. enemy operands: id, weapon (0: none), kill flag (255:
// none), 1, 2, 0, 0, angle (0 faces +X, 0x800 -X, 0xC00 +Z), 0, 0, X, Y, Z,
// enemy slot, animation, frame, 0: the shape every shipped NPC spawn has.
// Only while FG_COMMON 199 is set, which tests/people.ts sets: in the story
// neither of them is in the cabin.
if (ck(FG_COMMON, 199, 0)) {   // ck(f, 0): the bit is set, as set(f, 0) leaves it
    enemy(34 /* Barry (Stars) */, 0, 255, 1, 2, 0, 0, 2656, 0, 0, 10710, 0, 5610, 0, 0, 0, 0);
    enemy(33 /* Jill (Stars) */, 0, 255, 1, 2, 0, 0, 2944, 0, 0, 5780, 0, 6290, 1, 0, 0, 0);
}
return;

// main procedure 0
// The people idle. A character's first update clears its idle behaviour
// (npc_state0_init), so on the second frame in the room each is given idle 9,
// which loops its animation 0 (npc_idle_play_anim). FG_ROOM bits clear on
// every room entry: 20 marks the first frame, 21 that it is done. A message
// pauses the characters but not this script, so the room's first message
// waits for 21: shown on the first frame, it would hold back their first
// update until after this ran, and that update would clear the idle again.
if (ck(FG_ROOM, 21, 1)) {
    if (ck(FG_ROOM, 20, 0)) {
        eml_state(0, 0, 2, 9, 0);
        eml_state(0, 1, 2, 9, 0);
        set(FG_ROOM, 21, 0);
    }
    set(FG_ROOM, 20, 0);
}
if (ck(FG_ROOM, 21, 0) && ck(FG_COMMON, 201, 1)) {
    set(FG_COMMON, 201, 0);
    message(128, 255, 0);
}
return;
