// ROOM3030, the heliport, in Rebecca's scenario (the epilogue). She comes up
// from the house by a chapter break and finds Chris waiting for Brad's
// helicopter. When the scene's message closes the game ends: the script sets
// MSF2_DEATH_VARIANT (bank FG_STATUS, flag 32) and then MSF_PLAYER_DEAD (flag
// 7), so game_loop runs its end fade without the death screen and returns
// into ending_state. Chris's Tyrant fight and events are left out.
//
// FG_COMMON 251: the scene has shown.
// cmpb(5, 3, 128) holds while g_menu_choice_id (state byte 5) is under 0x80,
// that is, no message is open.
// Room messages are 0x80 + index: 135 is message 7.
// init procedure 0
door_aot_set(0, 5800, 3900, 2500, 2700, 0, 13, 17, 64, 255, ROOM_51D, 0, 0, 0, 0, UNLOCKED, 129);
enemy(32 /* Chris (Stars) */, 0, 255, 1, 2, 0, 0, 2560, 0, 0, 16000, 0, 16000, 0, 0, 0, 0);
return;

// main procedure 0
if (ck(FG_COMMON, 251, 1)) {
    set(FG_COMMON, 251, 0);
    message(135, 0, 0);
} else {
    if (cmpb(5, 3, 128)) {
        set(FG_STATUS, 32, 0);
        set(FG_STATUS, 7, 0);
    }
}
return;
