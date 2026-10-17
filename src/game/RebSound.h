// Her mode's room sounds (port addition). tools/rebecca/build.ts writes them
// from tools/rebecca/sound into her overlay as sound\rooms.dat; the file
// format is in RebSound.cpp. Chris's and Jill's games never read it.
#pragma once

// The WAV base name her room puts in entity sound slot `slot` (0-47,
// g_emSndBanks), "" to leave the slot empty. Null when her room leaves the
// slot to RE1's row, or her file is missing.
const char* RebSound_Slot(int stage, int room, int slot);
