// TestMode.h - automated test support (port addition, test tooling only).
//
// Started by --test-port <n>. A harness connects to 127.0.0.1:<n>, sends one
// command per line and receives one JSON line per state change. See
// docs/TEST_MODE.md for the protocol.
#pragma once

// Open the test link. Returns 0 when the port cannot be opened.
int  TestMode_Start(int port);
int  TestMode_Active(void);

// Run harness commands, expire held keys and send the state line if anything
// changed. gameFrame is 1 after main_loop and 0 from the movie loop, which
// spins without game frames; only game frames advance the frame counter.
void TestMode_Tick(int gameFrame);

// Called by set_message_display so the state can name the message on screen.
void TestMode_NoteMessage(unsigned short msgId);

// Called from inside the game loop task (debug_menu_overlay): runs a room
// change the harness asked for, which needs task context to sleep a frame.
void TestMode_RunPendingRoomChange(void);

// Dev boot (port addition): --boot <chris|jill|rebecca>[:<stage>:<room>]
// starts a new game straight from launch, skipping the logos, title, character
// select and opening movie, then moves to the room if one was given. Works with
// or without test mode. Returns 0 for a spec it cannot read.
int  DevBoot_Configure(const char* spec);
// Called where startup would chain the logos: chains game_start instead and
// returns 1 when a dev boot was configured.
int  DevBoot_Begin(void);
// The room a dev boot starts in, if the spec named one. InitializeGame uses it
// in place of the new-game start room.
int  DevBoot_StartRoom(int* stage, int* room);
