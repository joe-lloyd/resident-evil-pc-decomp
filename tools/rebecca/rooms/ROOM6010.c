// ROOM6010, the 1F left stairs on the way back through the house, in
// Rebecca's scenario (Chapter 6: the hunters). She arrives from the lab by a
// chapter break. A Hunter prowls the far end; the stairs up (door 3) are a
// chapter break to the heliport (ROOM3030, the epilogue). Chris's Rebecca NPC
// and her scenes are left out.
//
// FG_COMMON 250: the chapter title has shown.
// Room messages are 0x80 + index: 140 is message 12.
// init procedure 0
door_aot_set(0, 7600, 7700, 2400, 1500, 0, 0, 0, 4, 0, ROOM_S00, 3500, 0, 2600, 3072, UNLOCKED, 129);
door_aot_set(1, 14000, 17200, 2000, 1500, 2, 0, 29, 5, 202, ROOM_S02, 3400, 0, 9200, 1024, 52 /* Armor Key */, 129);
door_aot_set(2, 19400, 19000, 2000, 2700, 1, 0, 0, 1, 0, ROOM_S03, 2400, 0, 24800, 0, UNLOCKED, 129);
door_aot_set(3, 4700, 2500, 2605, 1300, 0, 5, 24, 96, 0, ROOM_303, 12000, 0, 12000, 3072, UNLOCKED, 129);
tbl37_set(5, 1, 255);
enemy(6 /* Hunter */, 23, 14, 1, 2, 0, 0, 3000, 0, 0, 4067, 0, 17454, 1, 0, 0, 0);
return;

// main procedure 0
if (ck(FG_COMMON, 250, 1)) {
    set(FG_COMMON, 250, 0);
    message(140, 0, 0);
}
return;
