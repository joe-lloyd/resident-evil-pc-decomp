// The ranger station's yard (ROOM3150), outside the lookout, morning.
//
// The puzzle: the trail down the mountain is blocked by a fallen pine. The
// truck's winch can drag it clear, but its crank is in the shed, and the shed
// is padlocked. The key hangs by the cabin door. Once she has it, a Cerberus
// comes out of the trees.
//
// Game units are metres * 1700 (scene.py). Flags: FG_COMMON 202 she has been
// here before; FG_COMMON 205 the pine is dragged clear (the background shows
// it moved while this is set, src/game/BgAnim.cpp); FG_ITEM 242 clear once she
// has the shed key; FG_LOCK 60 the shed's padlock is open; FG_ENEMY 200 the
// dog is dead. ck(bank, n, 1) is true while flag n is clear.
// Outdoor doors walk rather than open: door bytes 0, 15, 48 play walk 0 with
// the footsteps of sound row 15 (src/game/PathWalk.cpp).
// init procedure 0
// Back up the trail to the ridge, on touch at the yard's north-west corner.
door_aot_set(0, 3400, 3400, 4250, 850, 0, 15, 48, 4, 0, ROOM_312, 3500, 0, 14400, 1024, UNLOCKED, 1);
// The cabin door, from the porch steps: inside the door, facing in (-Z).
door_aot_set(1, 21080, 12325, 1870, 1020, 0, 0, 0, 4, 0, ROOM_314, 6715, 0, 9180, 1024, UNLOCKED, 129);
// The shed, padlocked: lock 60 (0x80 | 60 = 188) opens with the Small Key.
door_aot_set(2, 9180, 12410, 1190, 1360, 0, 0, 0, 4, 188, ROOM_316, 4845, 0, 3570, 2048, 61 /* Small Key */, 129);
// The trail down: the pine blocks it until it is dragged clear.
if (ck(FG_COMMON, 205, 1)) {
    aot_set(3, 24310, 19380, 4930, 1360, SCE_MESSAGE, 129, 129, 0, 255, 0, 0, 0);
} else {
    door_aot_set(3, 24310, 19380, 4930, 1360, 0, 15, 48, 4, 0, ROOM_317, 10200, 0, 6120, 3072, UNLOCKED, 1);
}
// In front of the winch: the Hex Crank can be used here (item-use bank 9,
// bit 30 - 27 = 3), and checking it says what it needs.
aot_set(4, 19210, 17170, 1700, 2380, SCE_USEITEM, 1, 9, 0, 3, 0, 1, 0);
aot_set(5, 19210, 17170, 1700, 2380, SCE_MESSAGE, 129, 130, 0, 255, 0, 0, 0);
aot_set(6, 14450, 14280, 2210, 1020, SCE_MESSAGE, 129, 131, 0, 255, 0, 0, 0);   // the truck's open door
aot_set(7, 9180, 6120, 2720, 1360, SCE_MESSAGE, 129, 132, 0, 255, 0, 0, 0);     // the station sign
aot_set(8, 26010, 13260, 2210, 2040, SCE_MESSAGE, 129, 133, 0, 255, 0, 0, 0);   // his rifle in the grass
aot_set(9, 27540, 4420, 1360, 1700, SCE_MESSAGE, 129, 134, 0, 255, 0, 0, 0);    // the smashed window
aot_set(10, 27540, 9860, 2380, 2040, SCE_MESSAGE, 129, 135, 0, 255, 0, 0, 0);   // drag marks into the trees
// The dog comes out of the trees once she has the key: from behind the
// cabin's far corner, so she sees it come round before it reaches her.
if (ck(FG_ITEM, 242, 1)) {
    enemy(2 /* Cerberus */, 12, 200, 1, 2, 0, 0, 2048, 0, 0, 29750, 0, 5100, 0, 0, 0, 0);
}
return;

// main procedure 0
if (ck(FG_COMMON, 202, 1)) {
    set(FG_COMMON, 202, 0);
    message(128, 255, 0);
}
// The crank used at the winch. The status screen is still closing on the
// frame she uses it, and a message opened then is dropped, so the line waits
// a second (the state word 4 counts seconds; setw restarts it). The pine
// moves as she says it drags clear: FG_COMMON 205 switches the background.
// FG_ROOM 10: the crank is on the winch, her line still to come.
if (ck(FG_COMMON, 205, 1)) {
    if (ck(FG_ROOM, 10, 1) && testitem(30 /* Hex Crank */)) {
        set(FG_ROOM, 10, 0);
        remove_item(30 /* Hex Crank */);
        setw(4, 0, 0);
    }
    if (ck(FG_ROOM, 10, 0) && cmpw(0, 4, 1, 0)) {
        // Using a crank puts her in the scripted crank pose (MainMenu.cpp);
        // the player-property op's sub-command 7 stands her back up.
        sys_multi(7);
        set(FG_COMMON, 205, 0);
        door_aot_set(3, 24310, 19380, 4930, 1360, 0, 15, 48, 4, 0, ROOM_317, 10200, 0, 6120, 3072, UNLOCKED, 1);
        message(136, 255, 0);
    }
}
return;
