// ROOM2040, the 2F hallway, in Rebecca's scenario. Init only: the room's main
// script is kept. Door 4 to the corridor where Richard lies (ROOM20D0) is not
// locked with the Armor Key: Chapter 2 sends her to him before she could have
// found it. Its second zombie (kill flag 168) is dead at the start (build.ts).
// init procedure 0
door_aot_set(0, 900, 2900, 1900, 1600, 1, 0, 3, 1, 0, ROOM_S03, 31200, -2885, 20500, 2048, UNLOCKED, 129);
door_aot_set(1, 16600, 11000, 2200, 2200, 11, 1, 9, 5, 206, ROOM_S05, 16000, 0, 7300, 2048, 52 /* Armor Key */, 129);
door_aot_set(2, 2300, 19300, 2000, 2100, 0, 0, 0, 4, 64, ROOM_S06, 3000, 0, 2600, 3072, UNLOCKED, 129);
door_aot_set(3, 12300, 19200, 2400, 2200, 0, 0, 0, 7, 150, ROOM_S07, 3000, 0, 3600, 3072, LOCKED, 129);
door_aot_set(4, 11400, 1100, 2100, 1600, 0, 0, 0, 7, 141, ROOM_S0D, 3000, 0, 12600, 1024, UNLOCKED, 129);
enemy(17 /* Zombie (Green Coat) */, 0, 109, 1, 2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0);
enemy(17 /* Zombie (Green Coat) */, 0, 168, 1, 2, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0);
if (ck(FG_SCENARIO, 5, 1)) {
    set(FG_SCENARIO, 5, 0);
}
return;
