// ROOM5110, the power room under the lab, in Rebecca's scenario (Chapter 5:
// underground). She arrives from Plant 42's room by a chapter break and turns
// the elevator power on at the switch (zone 1, inside the machine block, used
// from the east aisle). The door then leads on, by a chapter break, to the
// room where Wesker waits (ROOM5140). Chris's events and Rebecca's NPC are
// left out.
//
// FG_COMMON 230: the power is on. 231: the chapter title has shown.
// The switch zone's own message tells it (a message main opens while the
// zone's is up is dropped); main records it: cmpb(16, 0, 2).
// Room messages are 0x80 + index: 136 is message 8.
// init procedure 0
if (ck(FG_COMMON, 230, 0)) {
    door_aot_set(0, 11300, 15800, 3000, 2900, 12, 1, 11, 3, 0, ROOM_514, 12000, 0, 10000, 2048, UNLOCKED, 129);
    aot_set(1, 17700, 8300, 2100, 1600, SCE_MESSAGE, 129, 137, 0, 255, 0, 0, 0);
} else {
    door_aot_set(0, 11300, 15800, 3000, 2900, 12, 1, 11, 3, 0, ROOM_S10, 12200, 0, 2500, 3072, UNLOCKED, 129);
    aot_set(1, 17700, 8300, 2100, 1600, SCE_MESSAGE, 129, 134, 0, 255, 0, 0, 0);
}
aot_set(2, 5800, 4400, 2100, 1700, SCE_MESSAGE, 129, 129, 0, 255, 0, 0, 0);
return;

// main procedure 0
if (ck(FG_COMMON, 231, 1)) {
    set(FG_COMMON, 231, 0);
    message(136, 0, 0);
}
if (ck(FG_COMMON, 230, 1) && cmpb(16, 0, 2)) {
    set(FG_COMMON, 230, 0);
    aot_reset(1, SCE_MESSAGE, 129, 137, 255, 0);
    door_aot_set(0, 11300, 15800, 3000, 2900, 12, 1, 11, 3, 0, ROOM_514, 12000, 0, 10000, 2048, UNLOCKED, 129);
}
return;
