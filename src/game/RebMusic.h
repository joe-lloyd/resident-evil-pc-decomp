// Her mode's music table (port addition). tools/rebecca/build.ts writes it
// from tools/rebecca/plan/music.ts into her overlay as sound\music.dat; the
// file format is in RebMusic.cpp. Chris's and Jill's games never read it.
#pragma once

// RE1's g_BgmNameTable holds this many groups; her groups are numbered after them.
#define REB_MUSIC_FIRST_GROUP 57

// The room-to-group table bgm_group_for indexes in her mode: RE1's
// g_BgmRoomData with her rooms' rows laid over it, the same 7 x 32 x 4 bytes.
// Null when her file is missing or bad, so her mode falls back to RE1's.
const unsigned char* RebMusic_RoomTable(void);

// The file her group `group` (REB_MUSIC_FIRST_GROUP and up) plays on
// `channel` (0-2), and its loop flag. Null for a channel with no file.
const char* RebMusic_File(unsigned char group, int channel, unsigned char* loop);
