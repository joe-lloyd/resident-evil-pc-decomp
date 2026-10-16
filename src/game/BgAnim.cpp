// ============================================================================
// BgAnim - moving parts of a pre-rendered background (REB mode only)
//
// The shipped game's backgrounds are still pictures. Rebecca's rooms bring a
// file per camera that patches the background texture as the game runs: a
// candle flame, grass in the wind, a fly round a lamp, and patches that show a
// change of state (a fallen tree dragged off the path) while a flag is set. A
// change can also play once as it happens: the tree dragging across the path
// in the moments after its flag is raised, then gone for the state behind it.
//
// objspr\anm0<stage><room, two decimal digits><camera>.dat, next to the mask
// paks (load_room_bg_masks), little-endian:
//
//   char magic[4] "RBA1"
//   u16  layerCount
//   per layer:
//     u8  bank     flag bank (0, 1 or 2, as cmd_bit_test numbers them), 0xFF = always
//     u8  bit      flag index in that bank
//     u8  value    bit 0: 1 = shown while the flag is set, 0 = while it is clear;
//                  bit 1: play once, from the frame the flag turns that way,
//                  and hide after the last frame
//     u8  ticks    game frames per animation frame
//     u16 frameCount
//     per frame:
//       u16 rectCount
//       per rect: u16 x, y, w, h, then w*h background pixels (15-bit, as the
//       background TIM stores them)
//
// Layers draw in file order over the camera's background. The texture is only
// rebuilt when some layer's frame or visibility changes.
//
// A play-once layer needs the moment its flag turned, which may be before the
// camera that shows it loads: a room script raises the flag and cuts to that
// camera in the same frame. So every drawn frame notes when each flag of banks
// 0-2 last turned, room-wide; a new room, or a second with nothing drawn (a
// load, a door), starts the notes over without counting what changed.
// ============================================================================
#include "../Globals.h"
#include "../DebugPrint.h"
#include "../marni/MarniSystem.h"
#include "../platform/platform.h"
#include "../system/AssetPath.h"
#include "BioCard.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

void BgAnim_Clear(void);

namespace {

constexpr int W = 320;
constexpr int H = 240;
constexpr int MAX_LAYERS = 32;
constexpr unsigned char VALUE_SET = 1;
constexpr unsigned char VALUE_ONCE = 2;
// Flags watched for play-once layers: banks 0 (128), 1 (256) and 2 (64).
constexpr int BANK_BITS[3] = {128, 256, 64};
constexpr int WATCHED = 128 + 256 + 64;

struct Layer {
    unsigned char bank, bit, value, ticks;
    unsigned short frameCount;
    const unsigned char* frames;   // first frame record
};

unsigned char* s_file = NULL;
size_t s_fileSize = 0;
Layer s_layers[MAX_LAYERS];
int s_layerCount = 0;
unsigned int s_base[W * H];
unsigned int s_work[W * H];
int s_shown[MAX_LAYERS];           // frame on screen per layer, -1 = hidden
unsigned int s_serial = 0;         // display image the layers belong to

bool s_seen[WATCHED];              // each watched flag at the last drawn frame
DWORD s_turned[WATCHED];           // Game_timer when it last changed; 0 = not since the notes began
DWORD s_lastTick = 0;
int s_watchRoom = -1;              // stage * 256 + room the notes are for
bool s_watching = false;

unsigned int to_rgba(unsigned short px)
{
    unsigned int r = ((px >> 0) & 0x1F) * 255 / 31;
    unsigned int g = ((px >> 5) & 0x1F) * 255 / 31;
    unsigned int b = ((px >> 10) & 0x1F) * 255 / 31;
    return 0xFF000000u | (b << 16) | (g << 8) | r;
}

unsigned short u16(const unsigned char* p) { return (unsigned short)(p[0] | (p[1] << 8)); }

bool flag_set(int bank, int bit)
{
    const void* data = bank == 0 ? (const void*)&g_ScenarioFlags
                     : bank == 1 ? (const void*)&g_ScenarioFlags2
                                 : (const void*)g_LocksFlags;
    // Same bit order as cmd_bit_op: bit 0 of a word is its top bit.
    const unsigned int word = ((const unsigned int*)data)[bit >> 5];
    return (word & (0x80000000u >> (bit & 31))) != 0;
}

// Walk one frame's records; returns the byte after it, or NULL when the file
// ends early. `draw` writes its pixels into s_work.
const unsigned char* walk_frame(const unsigned char* p, bool draw)
{
    const unsigned char* end = s_file + s_fileSize;
    if (p == NULL || p + 2 > end) return NULL;
    int rects = u16(p);
    p += 2;
    for (int r = 0; r < rects; r++) {
        if (p + 8 > end) return NULL;
        int x = u16(p), y = u16(p + 2), w = u16(p + 4), h = u16(p + 6);
        p += 8;
        if (x + w > W || y + h > H || p + (size_t)w * h * 2 > end) return NULL;
        if (draw) {
            for (int j = 0; j < h; j++) {
                unsigned int* dst = &s_work[(y + j) * W + x];
                const unsigned char* src = p + (size_t)j * w * 2;
                for (int i = 0; i < w; i++) dst[i] = to_rgba(u16(src + i * 2));
            }
        }
        p += (size_t)w * h * 2;
    }
    return p;
}

const unsigned char* frame_at(const Layer& l, int frame)
{
    const unsigned char* p = l.frames;
    for (int f = 0; f < frame && p; f++) p = walk_frame(p, false);
    return p;
}

int watched(int bank, int bit)
{
    int at = 0;
    for (int b = 0; b < bank; b++) at += BANK_BITS[b];
    return at + bit;
}

// Note when each watched flag turns. Called every drawn frame.
void watch_flags(void)
{
    const int room = (int)g_stageId * 256 + (int)g_roomId;
    const bool fresh = !s_watching || room != s_watchRoom || Game_timer - s_lastTick > 30;
    int i = 0;
    for (int bank = 0; bank < 3; bank++) {
        for (int bit = 0; bit < BANK_BITS[bank]; bit++, i++) {
            const bool now = flag_set(bank, bit);
            if (fresh) s_turned[i] = 0;
            else if (now != s_seen[i]) s_turned[i] = Game_timer;
            s_seen[i] = now;
        }
    }
    s_watching = true;
    s_watchRoom = room;
    s_lastTick = Game_timer;
}

int wanted_frame(const Layer& l)
{
    if (l.bank != 0xFF && flag_set(l.bank, l.bit) != ((l.value & VALUE_SET) != 0)) return -1;
    if (l.value & VALUE_ONCE) {
        const DWORD turned = l.bank == 0xFF ? 0 : s_turned[watched(l.bank, l.bit)];
        if (turned == 0) return -1;
        const DWORD frame = (Game_timer - turned) / (l.ticks ? l.ticks : 1);
        return frame < l.frameCount ? (int)frame : -1;
    }
    if (l.frameCount <= 1 || l.ticks == 0) return 0;
    return (int)((Game_timer / l.ticks) % l.frameCount);
}

}  // namespace

// Called after load_room_bg_image put a camera's background on screen.
void BgAnim_Load(const void* bitmap, int width, int height)
{
    BgAnim_Clear();
    if (!g_bRebMode || width != W || height != H) return;

    char path[40];
    snprintf(path, sizeof(path), GAME_DATA_ROOT "objspr\\anm0%d%02d%d.dat",
             (int)g_stageId, (int)g_roomId % 100, (int)g_roomCameraId);
    char resolved[260], normalized[260];
    const char* file = plat_normalize_path(ResolveAssetRoot(path, resolved, sizeof(resolved)),
                                           normalized, sizeof(normalized));
    FILE* fp = fopen(file, "rb");
    if (fp == NULL) return;   // a still background
    fseek(fp, 0, SEEK_END);
    long size = ftell(fp);
    fseek(fp, 0, SEEK_SET);
    s_file = size > 6 ? (unsigned char*)malloc((size_t)size) : NULL;
    if (s_file == NULL || fread(s_file, 1, (size_t)size, fp) != (size_t)size) {
        fclose(fp);
        BgAnim_Clear();
        return;
    }
    fclose(fp);
    s_fileSize = (size_t)size;

    if (memcmp(s_file, "RBA1", 4) != 0) {
        dbg_printf("[bganim] %s is not an RBA1 file\n", path);
        BgAnim_Clear();
        return;
    }
    int count = u16(s_file + 4);
    const unsigned char* p = s_file + 6;
    for (int i = 0; i < count && i < MAX_LAYERS; i++) {
        if (p == NULL || p + 6 > s_file + s_fileSize) break;
        Layer& l = s_layers[s_layerCount];
        l.bank = p[0];
        l.bit = p[1];
        l.value = p[2];
        l.ticks = p[3];
        l.frameCount = u16(p + 4);
        l.frames = p + 6;
        p = frame_at(l, l.frameCount);
        if (p == NULL || (l.bank != 0xFF && (l.bank > 2 || l.bit >= BANK_BITS[l.bank]))) {
            dbg_printf("[bganim] %s: layer %d is malformed\n", path, i);
            break;
        }
        s_shown[s_layerCount] = -1;
        s_layerCount++;
    }

    const unsigned short* src = (const unsigned short*)bitmap;
    for (int i = 0; i < W * H; i++) s_base[i] = to_rgba(src[i]);
    s_serial = g_displayImageSerial;
}

void BgAnim_Clear(void)
{
    free(s_file);
    s_file = NULL;
    s_fileSize = 0;
    s_layerCount = 0;
}

// Once per drawn frame, before the background quad is queued.
void BgAnim_Tick(void)
{
    if (g_bRebMode) watch_flags();
    if (s_layerCount == 0 || s_serial != g_displayImageSerial || g_displayImageSRV == MARNI_NULL_HANDLE) return;
    int want[MAX_LAYERS];
    bool changed = false;
    for (int i = 0; i < s_layerCount; i++) {
        want[i] = wanted_frame(s_layers[i]);
        changed |= want[i] != s_shown[i];
    }
    if (!changed) return;

    memcpy(s_work, s_base, sizeof(s_work));
    for (int i = 0; i < s_layerCount; i++) {
        s_shown[i] = want[i];
        if (want[i] >= 0) walk_frame(frame_at(s_layers[i], want[i]), true);
    }
    Marni_DX()->UpdateTexturePixels(g_displayImageSRV, s_work, W, H, 32);
}
