// The ranger's lookout (ROOM3140), inside: a one-room log cabin, the morning
// after. The ranger left in a hurry: breakfast half eaten, a chair knocked
// over, his rifle gone, the east window smashed in with blood on the sill.
// His logbook says the crank for the truck's winch is in the shed; the shed
// key hangs on a board past his hat, well along the wall from the door.
//
// Game units are metres * 1700 (scene.py builds the room in metres).
// FG_ITEM 241: the spray is still on
// the table, 242: the shed key is still on its hook, 240: the ink ribbons are
// still by the typewriter, 248: the trail map is still on the desk (bit set =
// still there).
// item_aot_set operands after the model index: 255, the model's position
// (X, Y, Z as little-endian 16-bit pairs), two rotation bytes, the item flag,
// then 129 (taken with the action key), 0, 0.
// message(n, 255, 0): the 255 pauses the game under the message, as Chris's
// scripts do. Room messages are 0x80 + index: 128 is message 0.
// init procedure 0
// The door out to the yard (ROOM3150): she comes out onto the porch steps,
// facing the yard (+Z, angle 0xC00).
door_aot_set(0, 5950, 9100, 1530, 1100, 1, 0, 7, 1, 0, ROOM_315, 22015, 0, 13515, 3072, UNLOCKED, 129);
// On the table by the cards: the First Aid Spray, model at (7276, -1292, 7310).
if (ck(FG_ITEM, 241, 0)) {
    item_aot_set(1, 6120, 6630, 1700, 1700, 65 /* F-Aid Spray */, 1, 0, 255, 108, 28, 244, 250, 142, 28, 0, 0, 241, 129, 0, 0);
}
// On the key board past the hat pegs: the shed key at (9605, -2414, 10106).
// Its zone is 0.85 m clear of the door's, so action by the door opens the
// door. The last operand pair is 0x8000: the item sparkle RE1 gives a pickup.
if (ck(FG_ITEM, 242, 0)) {
    item_aot_set(2, 9010, 9095, 1105, 1105, 61 /* Small Key */, 1, 1, 255, 133, 37, 146, 246, 122, 39, 0, 0, 242, 129, 0, 128);
}
aot_set(3, 4335, 4675, 850, 935, SCE_MESSAGE, 129, 129, 0, 255, 0, 0, 0);   // the radio
// The logbook, a file (tools/rebecca/files/documents.ts): item 0x60 (slot 1), on the
// room's empty model slot 4 (after the spray, the key, the ink ribbons and
// the map), flag 230. Open on the corner table by the broken window, taken
// from in front of it; the window's own zone starts where this one ends.
if (ck(FG_ITEM, 230, 0)) {
    item_aot_set(4, 10115, 4165, 765, 935, 96 /* Ranger's logbook */, 1, 4, 255, 0, 0, 0, 0, 0, 0, 0, 0, 230, 129, 0, 0);
}
// On the desk between the radio and the typewriter: the ranger's trail map
// (item 0x4E, maps/pickups.ts), RE1's own folded map in model slot 3, model
// at (5530, -1292, 4080). FG_ITEM 248 while it is there.
if (ck(FG_ITEM, 248, 0)) {
    item_aot_set(16, 5185, 4675, 695, 935, 78 /* Trail Map */, 1, 3, 255, 154, 21, 244, 250, 240, 15, 0, 0, 248, 129, 0, 0);
}
aot_set(5, 9520, 7480, 765, 2550, SCE_MESSAGE, 129, 130, 0, 255, 0, 0, 0);  // the bunk
aot_set(6, 4590, 7310, 850, 1360, SCE_MESSAGE, 129, 131, 0, 255, 0, 0, 0);  // the stove
aot_set(7, 10880, 4420, 1020, 1020, SCE_MESSAGE, 129, 132, 0, 255, 0, 0, 0); // the broken window, its north part: the item box is below the rest
aot_set(8, 4590, 9180, 1190, 1020, SCE_MESSAGE, 129, 133, 0, 255, 0, 0, 0);  // the empty rifle rack, west of the door
aot_set(9, 7820, 5440, 1190, 714, SCE_MESSAGE, 129, 134, 0, 255, 0, 0, 0);   // breakfast
aot_set(10, 3485, 4760, 765, 935, SCE_MESSAGE, 129, 135, 0, 255, 0, 0, 0);   // the survey map
aot_set(11, 7565, 9180, 850, 1020, SCE_MESSAGE, 129, 136, 0, 255, 0, 0, 0);  // his hat
aot_set(12, 7820, 4080, 2040, 850, SCE_MESSAGE, 129, 137, 0, 255, 0, 0, 0);  // the shelves
// Where she saves, as in the mansion's save room (ROOM1000): the ink ribbons
// beside the typewriter on the desk (RE1's own ribbon model, from
// ROOM30E0), the typewriter, and the item box at the bunk's foot. Its lid is
// RE1's own object model 0 (from ROOM1000), shrunk with the box to a
// footlocker (scene.py, scale 0.65), hinged at its back edge and opening north
// (angle 1024). The box's zone starts where the broken window's ends.
if (ck(FG_ITEM, 240, 0)) {
    item_aot_set(13, 6630, 3570, 680, 1105, 47 /* Ink Ribbon */, 3, 2, 255, 94, 25, 244, 250, 68, 17, 0, 0, 240, 129, 0, 0);
}
aot_set(14, 5880, 4675, 835, 935, SCE_TYPEWRITER, 129, 0, 0, 0, 0, 0, 0);
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
// FG_ROOM 22: the trail map was on the desk when she came in (main says her
// line the frame she takes it).
if (ck(FG_ITEM, 248, 0)) {
    set(FG_ROOM, 22, 0);
}
return;

// main procedure 0
// The people idle. A character's first update clears its idle behaviour
// (npc_state0_init), so on the second frame in the room each is given idle 9,
// which loops its animation 0 (npc_idle_play_anim). FG_ROOM bits clear on
// every room entry: 20 marks the first frame, 21 that it is done.
if (ck(FG_ROOM, 21, 1)) {
    if (ck(FG_ROOM, 20, 0)) {
        eml_state(0, 0, 2, 9, 0);
        eml_state(0, 1, 2, 9, 0);
        set(FG_ROOM, 21, 0);
    }
    set(FG_ROOM, 20, 0);
}
if (ck(FG_ROOM, 22, 0) && ck(FG_ITEM, 248, 1)) {
    set(FG_ROOM, 22, 1);
    message(138, 255, 0);
}
return;
