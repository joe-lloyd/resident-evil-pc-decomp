// ROOM10F0, the bar, in Rebecca's scenario (Chapter 3: Moonlight). In Chris's
// game he cannot read music and Rebecca plays from the sheet he finds. Here
// she finds the Music Notes herself, plays "Moonlight Sonata", and the Gold
// Emblem turns up on the piano. None of Chris's events run.
//
// FG_COMMON 210: she has played the piano. 211: the chapter title has shown.
// 213: the door to Chapter 4 is open. FG_ITEM 7: the Music Notes are taken.
// (ck(bank, n, 1) holds while flag n is clear; set(bank, n, 0) sets it.)
// cmpb(16, 0, n) holds on the frame she presses action facing zone n - 1.
// Room messages are 0x80 + index: 157 is message 29.
// && in a condition is the decompiler's chain of ck/cmpb tests.
// aot_delete(n, type, flags) re-arms zone n with that handler and flags; a
// zone is dead only with SCE_NONE and flags 0 (cmd_room_action_arm).
// init procedure 0
// Door 0 needs the Sword Key in Chris's game. Once she has the emblem it is
// her way on: a chapter break to the guardhouse (ROOM4080).
if (ck(FG_ITEM, 21, 1)) {
    door_aot_set(0, 13700, 960, 1700, 1900, 1, 0, 31, 5, 0, ROOM_408, 4000, 0, 4500, 0, UNLOCKED, 129);
} else {
    door_aot_set(0, 13700, 960, 1700, 1900, 1, 0, 31, 5, 134, ROOM_S04, 30700, 0, 3900, 1024, 51 /* Sword Key */, 129);
}
// The piano (zone 2) is a message zone: the engine skips SCE_NONE zones when
// she presses action, and a message zone records which zone she checked
// (cmpb(16, 0, zone + 1)) for main to react to. Its message is the scene, so
// it is chosen to suit: no music, or the music in her bag.
// The Music Notes lie past the furniture in front of them (object 1, whose
// collision stops her at Z 10270); their zone reaches out to her.
if (ck(FG_COMMON, 210, 1)) {
    if (ck(FG_ITEM, 7, 0)) {
        item_aot_set(5, 16900, 10000, 1000, 2500, 35 /* Music Notes */, 1, 2, 255, 98, 67, 72, 244, 30, 45, 226, 4, 7, 129, 0, 0);
    }
    if (item_ck(35 /* Music Notes */)) {
        aot_set(2, 10200, 7300, 600, 1500, SCE_MESSAGE, 129, 159, 0, 255, 0, 0, 0);
    } else {
        aot_set(2, 10200, 7300, 600, 1500, SCE_MESSAGE, 129, 158, 0, 255, 0, 0, 0);
    }
}
// Once she has played, the emblem lies on the piano: model at (10500, -800, 8050).
if (ck(FG_COMMON, 210, 0) && ck(FG_ITEM, 21, 0)) {
    item_aot_set(4, 10200, 7300, 600, 1500, 32 /* Gold Emblem */, 1, 1, 255, 4, 41, 224, 252, 114, 31, 0, 4, 21, 129, 0, 0);
}
obj(0, 53, 255, 9100, 0, 12576, 1024, 62, 254, 0, 0, 194, 1, 0, 0, 84, 6, 24, 21, 128, 62, 144, 1);
obj(1, 1, 255, 17394, 0, 11190, 1024, 0, 0, 108, 3, 0, 0, 148, 252, 44, 1, 32, 2, 20, 5, 38, 2);
obj(2, 35, 255, 15000, 0, 11200, 1024, 0, 0, 0, 0, 0, 0, 0, 0, 88, 2, 32, 2, 132, 3, 88, 2);
return;

// main procedure 0
if (ck(FG_COMMON, 211, 1)) {
    set(FG_COMMON, 211, 0);
    message(157, 0, 0);
}
// She took the Music Notes: the piano now plays.
if (testpickup(35 /* Music Notes */)) {
    aot_reset(2, SCE_MESSAGE, 129, 159, 255, 0);
}
// She played: the notes are spent and the piano gives up the emblem.
if (ck(FG_COMMON, 210, 1) && cmpb(16, 0, 3) && item_ck(35 /* Music Notes */)) {
    set(FG_COMMON, 210, 0);
    remove_item(35 /* Music Notes */);
    aot_delete(2, SCE_NONE, 0);
    item_aot_set(4, 10200, 7300, 600, 1500, 32 /* Gold Emblem */, 1, 1, 255, 4, 41, 224, 252, 114, 31, 0, 4, 21, 129, 0, 0);
}
// She took the emblem: the door opens onto the guardhouse.
if (ck(FG_ITEM, 21, 1) && ck(FG_COMMON, 213, 1)) {
    set(FG_COMMON, 213, 0);
    door_aot_set(0, 13700, 960, 1700, 1900, 1, 0, 31, 5, 0, ROOM_408, 4000, 0, 4500, 0, UNLOCKED, 129);
}
return;
