// ============================================================================
// PathWalk - the walk between two outdoor rooms (REB mode only)
//
// A door into a room usually plays the 3D door-opening animation from a .dor
// file (DoorSystem.cpp) while the next room loads underneath. Rebecca's
// outdoor rooms join with a walk instead: a few seconds of a dark path seen
// as she walks it, and her footsteps on it, played the same way, in the door
// animation's place.
//
// A door record whose door type (record +0x0A) is DOOR_TYPE_WALK plays walk
// number record +0x08 from objspr\walkNN.dat, and the record's sound byte
// (+0x09) loads the footsteps into room sound slots 0 and 1, which the walk
// plays in turn. The file, little-endian:
//
//   char magic[4] "RBW1"
//   u16  frameCount
//   u8   ticks        game frames per picture
//   u8   stepTicks    game frames between footsteps
//   u32  offset[frameCount]   each picture: a background pak (LZW-packed
//                             320x240 16 bpp TIM, as the room backgrounds)
// ============================================================================
#include "../Globals.h"
#include "../DebugPrint.h"
#include "../platform/platform.h"
#include "../system/AssetPath.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

namespace {

unsigned char* s_walk = NULL;
size_t s_walkSize = 0;
// As big as g_TimImageBuffer: unpack_pakfile_ writes the TIM, its picture 20 bytes in.
unsigned char s_frame[187160 + 20];

unsigned short u16(const unsigned char* p) { return (unsigned short)(p[0] | (p[1] << 8)); }
unsigned int u32(const unsigned char* p) { return p[0] | (p[1] << 8) | (p[2] << 16) | ((unsigned int)p[3] << 24); }

bool LoadWalk(unsigned char variant)
{
    char path[48];
    snprintf(path, sizeof(path), GAME_DATA_ROOT "objspr\\walk%02u.dat", (unsigned int)variant);
    char resolved[260], normalized[260];
    const char* file = plat_normalize_path(ResolveAssetRoot(path, resolved, sizeof(resolved)),
                                           normalized, sizeof(normalized));
    FILE* fp = fopen(file, "rb");
    if (fp == NULL) {
        dbg_printf("[walk] %s missing - the door animation plays instead\n", path);
        return false;
    }
    fseek(fp, 0, SEEK_END);
    long size = ftell(fp);
    fseek(fp, 0, SEEK_SET);
    free(s_walk);
    s_walk = size > 12 ? (unsigned char*)malloc((size_t)size) : NULL;
    bool ok = s_walk != NULL && fread(s_walk, 1, (size_t)size, fp) == (size_t)size;
    fclose(fp);
    s_walkSize = ok ? (size_t)size : 0;
    unsigned int frames = ok ? u16(s_walk + 4) : 0;
    ok = ok && memcmp(s_walk, "RBW1", 4) == 0 && frames > 0 && 8 + frames * 4 <= s_walkSize;
    for (unsigned int i = 0; ok && i < frames; i++) ok = u32(s_walk + 8 + i * 4) < s_walkSize;
    if (!ok) {
        dbg_printf("[walk] %s is not a walk file\n", path);
        free(s_walk);
        s_walk = NULL;
        s_walkSize = 0;
    }
    return ok;
}

// The task that plays the walk while room_transition_load loads the room. It
// holds MSF_ROOM_TRANSITION for as long as it runs, as the door animation
// does, and room_transition_load waits for it to clear.
void WalkTask(void)
{
    g_bGameActive = 0;
    // A transition presents in the flat-colour screen mode, which leaves out
    // the background picture (the door animation is 3D, so it still shows).
    // The walk is the picture, so it shows in the picture mode, and the
    // transition's own mode comes back when it ends.
    const DWORD transitionMode = g_main_state_flags & MSF_SCREEN_MODE_MASK;
    const unsigned int frames = u16(s_walk + 4);
    const unsigned int ticks = s_walk[6] ? s_walk[6] : 2;
    const unsigned int stepTicks = s_walk[7];
    unsigned int t = 0;
    unsigned int step = 0;
    for (unsigned int f = 0; f < frames; f++) {
        unpack_pakfile_(s_walk + u32(s_walk + 8 + f * 4), s_frame);
        display_image(8, s_frame + 20, 320, 240);
        g_main_state_flags = (g_main_state_flags & ~MSF_SCREEN_MODE_MASK) | MSF_SCREEN_REBUILD;
        for (unsigned int k = 0; k < ticks; k++, t++) {
            if (stepTicks && t % stepTicks == stepTicks / 2) play_sfx(0, (int)(step++ & 1), 0);
            Task_sleep(1);
        }
        // Holding a direction or the run button skips the rest, as at a door.
        if ((g_PlayerPadHeld & 0xC0) != 0 && f > 10) break;
    }
    free(s_walk);
    s_walk = NULL;
    g_main_state_flags = (g_main_state_flags & ~MSF_SCREEN_MODE_MASK) | transitionMode;
    g_bGameActive = 2;
    g_main_state_flags &= ~MSF_ROOM_TRANSITION;
    Task_exit();
}

}  // namespace

// From room_transition_load in place of the door animation. False when there
// is no walk to play, and the door animation should run as usual.
bool PathWalk_Start(unsigned char variant)
{
    if (!g_bRebMode || !LoadWalk(variant)) return false;
    // Slots 0 and 1 (handles at g_RoomSfxBanks[0] and [2]) hold the footsteps
    // the door record's sound row loaded; say so, as the walk has no picture of them.
    dbg_printf("[walk] walk %u, footsteps %s\n", (unsigned int)variant,
               g_RoomSfxBanks[0] != 0 && g_RoomSfxBanks[2] != 0 ? "loaded" : "MISSING");
    g_main_state_flags |= MSF_ROOM_TRANSITION;
    Task_execute(1, (void*)WalkTask);
    return true;
}
