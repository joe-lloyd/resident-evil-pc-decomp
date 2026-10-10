// TestMode.h - automated test support (port addition, test tooling only).
//
// Started by --test-port <n>. A harness connects to 127.0.0.1:<n>, sends one
// command per line and receives one JSON line per state change. See
// docs/TEST_MODE.md for the protocol.
#pragma once

// Open the test link. Returns 0 when the port cannot be opened.
int  TestMode_Start(int port);
int  TestMode_Active(void);

// Once per frame, after main_loop: run harness commands, advance held keys and
// send the state line if anything changed.
void TestMode_Tick(void);

// Called by set_message_display so the state can name the message on screen.
void TestMode_NoteMessage(unsigned short msgId);

// Called from inside the game loop task (debug_menu_overlay): runs a room
// change the harness asked for, which needs task context to sleep a frame.
void TestMode_RunPendingRoomChange(void);
