// ROOM5140, by the main lab, in Rebecca's scenario (Chapter 5). Wesker waits
// here. On her first time in he confronts her; the lights fail and she runs.
// Door 1 is then a chapter break back to the mansion (ROOM6010, Chapter 6).
// Chris's events and Rebecca's NPC are left out.
//
// FG_COMMON 240: the confrontation has played.
// Room messages are 0x80 + index: 150 is message 22.
// init procedure 0
door_aot_set(0, 2400, 700, 2400, 1700, 10, 12, 13, 64, 0, ROOM_S13, 4700, 0, 25500, 1024, UNLOCKED, 129);
door_aot_set(1, 13500, 8500, 1800, 2900, 0, 13, 19, 64, 0, ROOM_601, 8700, 0, 7900, 1024, UNLOCKED, 129);
if (ck(FG_COMMON, 240, 1)) {
    tbl37_set(4, 20, 64);
    enemy(36 /* Wesker (Stars) */, 2, 255, 1, 2, 0, 0, 3072, 0, 0, 2950, 0, 3000, 0, 50, 0, 0);
}
return;

// main procedure 0
if (ck(FG_COMMON, 240, 1)) {
    set(FG_COMMON, 240, 0);
    message(150, 0, 0);
}
return;
