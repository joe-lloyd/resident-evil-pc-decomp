// ROOM2010, the 2F corridor at the top of the 1F left stairs, in Rebecca's
// scenario (Chapter 2). Richard lies here poisoned; Chris's game has him in
// ROOM20D0, which she cannot reach from these stairs: the stairs come up into
// the south half of this room, and the door to ROOM2020 is in its north half,
// walled off by the stairwell. None of Chris's events run; the scene is
// messages.
//
// FG_COMMON 200: she has found Richard and his clock runs.
//           201: his fate is settled.
//           202: she saved him.
// ck(bank, n, 1) is true while flag n is clear and ck(bank, n, 0) once it is
// set; set(bank, n, 0) sets it (cmd_bit_test XORs the bit with its last byte).
//
// The clock is state word 4, which the game counts up once a second;
// setw(4, 0, 0) zeroes it, and cmpw(0, 4, 4, 180) holds while 180 >= it:
// three minutes to fetch the serum from the save room (ROOM1000), two rooms
// away, and come back.
//
// Room messages are 0x80 + index: 132 is message 4.
// init procedure 0
door_aot_set(0, 17200, 900, 2000, 2000, 1, 0, 3, 4, 0, ROOM_S02, 6400, 0, 14000, 1024, UNLOCKED, 129);
door_aot_set(1, 14700, 25700, 1500, 1900, 1, 0, 0, 1, 255, ROOM_S14, 6400, 0, 14000, 3072, UNLOCKED, 0);
door_aot_set(2, 12900, 16500, 2100, 1800, 0, 0, 0, 4, 204, ROOM_S15, 8100, 0, 3800, 2048, 54 /* Helmet Key */, 129);
door_aot_set(3, 11345, 10300, 2605, 2500, 1, 5, 24, 96, 0, ROOM_101, 4300, 0, 3100, 2048, UNLOCKED, 129);
aot_set(4, 2000, 10300, 300, 1900, SCE_MESSAGE, 129, 131, 0, 255, 0, 0, 0);
aot_set(5, 14700, 25700, 1500, 1900, SCE_EVENT, 129, 9, 0, 0, 0, 0, 0);
// Chris's three zombies are left out: they stand in the half of the room she
// cannot reach, and the room has no space to spare for their model next to
// Richard's (the writer's headroom check).
// Richard's own clip lies beside him for her to take.
if (ck(FG_ITEM, 40, 0)) {
    item_aot_set(7, 14500, 23300, 2100, 1400, 11 /* Clip */, 15, 0, 255, 10, 0, 0, 0, 10, 0, 0, 0, 40, 129, 1, 0);
}
if (ck(FG_COMMON, 201, 1)) {
    // Alive, waiting for the serum.
    enemy(39 /* Richard */, 0, 255, 1, 2, 0, 0, 1024, 0, 0, 15500, 0, 22000, 0, 2, 39, 0);
    aot_set(6, 14500, 19600, 2100, 1600, SCE_MESSAGE, 129, 135, 0, 0, 0, 0, 0);
} else {
    if (ck(FG_COMMON, 202, 0)) {
        enemy(39 /* Richard */, 0, 255, 1, 2, 0, 0, 1024, 0, 0, 15500, 0, 22000, 0, 2, 39, 0);
        aot_set(6, 14500, 19600, 2100, 1600, SCE_MESSAGE, 129, 136, 0, 0, 0, 0, 0);
    } else {
        enemy(39 /* Richard */, 0, 255, 1, 2, 0, 0, 1024, 0, 0, 15500, 0, 22000, 0, 1, 0, 0);
        aot_set(6, 14500, 19600, 2100, 1600, SCE_MESSAGE, 129, 134, 0, 0, 0, 0, 0);
    }
}
return;

// main procedure 0
// From main, like the meeting in ROOM1000: a message opened during init leaves
// the player frozen after it closes.
if (ck(FG_COMMON, 201, 1)) {
    if (ck(FG_COMMON, 200, 1)) {
        // First time here: she finds him and the clock starts.
        set(FG_COMMON, 200, 0);
        setw(4, 0, 0);
        message(132, 0, 0);
    } else {
        if (item_ck(66 /* Serum */)) {
            if (cmpw(0, 4, 4, 180)) {
                set(FG_COMMON, 201, 0);
                set(FG_COMMON, 202, 0);
                remove_item(66 /* Serum */);
                message(133, 0, 0);
            } else {
                set(FG_COMMON, 201, 0);
                message(134, 0, 0);
            }
        } else {
            if (cmpw(0, 4, 1, 180)) {
                set(FG_COMMON, 201, 0);
                message(134, 0, 0);
            }
        }
    }
}
return;
