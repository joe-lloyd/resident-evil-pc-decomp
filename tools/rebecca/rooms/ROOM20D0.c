// ROOM20D0, the 2F corridor where Richard lies poisoned, in Rebecca's
// scenario (Chapter 2). None of Chris's events run; the scene is messages.
//
// FG_COMMON 200: she has found Richard and his clock runs.
//           201: his fate is settled.
//           202: she saved him.
// ck(bank, n, 1) is true while flag n is clear and ck(bank, n, 0) once it is
// set; set(bank, n, 0) sets it (cmd_bit_test XORs the bit with its last byte).
//
// The clock is state word 4, which the game counts up once a second;
// setw(4, 0, 0) zeroes it, and cmpw(0, 4, 4, 420) holds while 420 >= it. That
// is Chris's own limit for this scene: seven minutes to fetch the serum from
// the save room (ROOM1000) and come back.
//
// Room messages are 0x80 + index: 153 is message 25.
// init procedure 0
door_aot_set(0, 1300, 12900, 3400, 2000, 3, 0, 0, 7, 0, ROOM_S04, 12500, 0, 2800, 3072, UNLOCKED, 129);
door_aot_set(1, 12000, 1100, 2300, 3100, 2, 0, 0, 1, 0, ROOM_S0E, 2700, 0, 2900, 0, UNLOCKED, 129);
// Richard's own clip lies beside him for her to take.
if (ck(FG_ITEM, 40, 0)) {
    item_aot_set(2, 7500, 2500, 1800, 1800, 11 /* Clip */, 15, 0, 255, 10, 0, 0, 0, 10, 0, 0, 0, 40, 129, 1, 0);
}
if (ck(FG_ITEM, 197, 0)) {
    item_aot_set(3, 5800, 6000, 1800, 1800, 68 /* Green Herb */, 1, 1, 255, 44, 26, 0, 0, 244, 26, 0, 0, 197, 129, 1, 0);
}
if (ck(FG_ITEM, 198, 0)) {
    item_aot_set(5, 4100, 6000, 1800, 1800, 68 /* Green Herb */, 1, 2, 255, 136, 19, 0, 0, 244, 26, 0, 0, 198, 129, 1, 0);
}
if (ck(FG_COMMON, 201, 1)) {
    // Alive, waiting for the serum.
    enemy(39 /* Richard */, 0, 255, 1, 2, 0, 0, 2048, 0, 0, 8300, 0, 3600, 0, 2, 39, 0);
    aot_set(4, 7900, 3100, 1800, 1800, SCE_MESSAGE, 129, 156, 0, 0, 0, 0, 0);
} else {
    if (ck(FG_COMMON, 202, 0)) {
        enemy(39 /* Richard */, 0, 255, 1, 2, 0, 0, 2048, 0, 0, 8300, 0, 3600, 0, 2, 39, 0);
        aot_set(4, 7900, 3100, 1800, 1800, SCE_MESSAGE, 129, 157, 0, 0, 0, 0, 0);
    } else {
        enemy(39 /* Richard */, 0, 255, 1, 2, 0, 0, 2048, 0, 0, 8300, 0, 3600, 0, 1, 0, 0);
        aot_set(4, 7900, 3100, 1800, 1800, SCE_MESSAGE, 129, 151, 0, 0, 0, 0, 0);
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
        message(153, 0, 0);
    } else {
        if (item_ck(66 /* Serum */)) {
            if (cmpw(0, 4, 4, 420)) {
                set(FG_COMMON, 201, 0);
                set(FG_COMMON, 202, 0);
                remove_item(66 /* Serum */);
                message(154, 0, 0);
            } else {
                set(FG_COMMON, 201, 0);
                message(155, 0, 0);
            }
        } else {
            if (cmpw(0, 4, 1, 420)) {
                set(FG_COMMON, 201, 0);
                message(155, 0, 0);
            }
        }
    }
}
return;
