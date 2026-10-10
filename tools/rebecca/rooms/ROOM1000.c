// ROOM1000, the mansion 1F save room, in Rebecca's scenario.
// The roles of Chris's first meeting are swapped: Chris waits here and
// Rebecca walks in. None of Chris's events run; the scene is messages.
// Room messages are addressed as 0x80 + index: 174 is message 46, 175 is 47.
// init procedure 0
door_aot_set(0, 2700, 500, 1700, 1800, 3, 0, 0, 4, 0, ROOM_S01, 8700, 0, 7900, 1024, UNLOCKED, 129);
item_aot_set(4, 4260, 7790, 1800, 1800, 51 /* Sword Key */, 3, 0, 255, 40, 20, 94, 252, 242, 33, 66, 14, 22, 129, 0, 135);
eml_rot(0, 0, 0, 132, 3);
// Chris's game gives the item box only to a player who is not Rebecca.
aot_set(5, 6200, 2100, 2000, 1400, SCE_ITEMBOX, 129, 0, 0, 0, 0, 0, 0);
aot_set(8, 2300, 8750, 1600, 2000, SCE_TYPEWRITER, 129, 0, 0, 0, 0, 0, 0);
obj(0, 17, 255, 7480, -1410, 1780, -1024, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0);
tbl37_set(0, 0, 9);
// Chris stands where Rebecca waits in his game; checking him gives his line.
enemy(32 /* Chris (Stars) */, 0, 255, 1, 2, 0, 0, 2220, 0, 0, 7280, 0, 3920, 0, 0, 0, 0);
aot_set(1, 6780, 3420, 1000, 1000, SCE_MESSAGE, 129, 175, 0, 0, 0, 0, 0);
return;

// main procedure 0
// First time in: the meeting. FG_COMMON 36 is the canon "Chris met Rebecca".
// It runs from main, once the room is playing: a message opened during init
// leaves the player frozen after it closes, because game_loop resets the
// message state that the message would restore.
if (ck(FG_COMMON, 36, 1)) {
    set(FG_COMMON, 36, 0);
    message(174, 0, 0);
}
return;
