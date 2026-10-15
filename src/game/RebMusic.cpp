// Her mode's music table (port addition).
//
// RE1 picks a room's music from compiled tables (SoundTables.cpp section 4):
// the room's row gives up to four groups, the room's state byte picks one,
// and the group names up to three WAVs. Her rooms sit in slots whose rows are
// RE1's, so her mode reads its own rows from her overlay and lays them over
// RE1's. A room she doesn't list, such as the mansion's save room, keeps RE1's
// row. The room's state byte stays where RE1 keeps it, in the save (her
// BIO_CARD.DAT sets it for a new game).
//
// sound\music.dat, little-endian:
//
//   char magic[4] "RBM1"
//   u8   groupCount
//   u8   roomCount
//   u8   pad[2]
//   group[groupCount]: char file[3][16]  NUL-terminated WAV base names under
//                                        sound\, "" for no channel
//                      u8   loop[3]      g_BgmLoopTable's flag: 1 loops
//                      u8   pad
//   room[roomCount]:   u8   stage        0-6, as g_BgmRoomData counts
//                      u8   room         0-31
//                      u8   group[4]     her group index, 0xFF none
//
// Her group n is group REB_MUSIC_FIRST_GROUP + n in the merged table, so
// update_room_bgm's group compare tells hers from RE1's.
#include "RebMusic.h"
#include "SoundTables.h"
#include "../DebugPrint.h"
#include "../platform/platform.h"
#include "../system/AssetPath.h"

#include <stdlib.h>
#include <string.h>

static_assert(sizeof(g_BgmNameTable) / sizeof(g_BgmNameTable[0]) == REB_MUSIC_FIRST_GROUP,
              "her groups are numbered after RE1's");

namespace {

const int kFileLen = 16;
const int kGroupSize = 3 * kFileLen + 4;
const int kRoomSize = 6;
const int kMaxGroups = 0xFF - REB_MUSIC_FIRST_GROUP;

struct Group {
    char file[3][kFileLen];
    unsigned char loop[3];
};

int s_loaded = 0;  // 0 not tried, 1 loaded, -1 missing or bad
unsigned char s_rooms[7][32][4];
Group s_groups[kMaxGroups];
int s_groupCount = 0;

int Load(void)
{
    char resolved[260], normalized[260];
    const char* file = plat_normalize_path(ResolveAssetRoot(GAME_DATA_ROOT "sound\\music.dat", resolved, sizeof(resolved)),
                                           normalized, sizeof(normalized));
    size_t size = 0;
    unsigned char* data = (unsigned char*)plat_file_read_all(file, &size);
    if (data == NULL) {
        dbg_printf("[music] no sound\\music.dat: her mode plays RE1's table\n");
        return -1;
    }
    const int groups = size >= 8 ? data[4] : 0;
    const int rooms = size >= 8 ? data[5] : 0;
    bool ok = size >= 8 && memcmp(data, "RBM1", 4) == 0 && groups <= kMaxGroups &&
              size == 8 + (size_t)groups * kGroupSize + (size_t)rooms * kRoomSize;
    for (int g = 0; ok && g < groups; g++) {
        const unsigned char* p = data + 8 + g * kGroupSize;
        for (int ch = 0; ch < 3; ch++) {
            ok = ok && memchr(p + ch * kFileLen, 0, kFileLen) != NULL;
            memcpy(s_groups[g].file[ch], p + ch * kFileLen, kFileLen);
            s_groups[g].loop[ch] = p[3 * kFileLen + ch];
        }
    }
    memcpy(s_rooms, g_BgmRoomData, sizeof(s_rooms));
    for (int r = 0; ok && r < rooms; r++) {
        const unsigned char* p = data + 8 + groups * kGroupSize + r * kRoomSize;
        ok = p[0] < 7 && p[1] < 32;  // the loop runs only while ok
        for (int n = 0; ok && n < 4; n++) {
            ok = p[2 + n] == 0xFF || p[2 + n] < groups;
            s_rooms[p[0]][p[1]][n] = p[2 + n] == 0xFF ? 0xFF : (unsigned char)(REB_MUSIC_FIRST_GROUP + p[2 + n]);
        }
    }
    free(data);
    if (!ok) {
        dbg_printf("[music] sound\\music.dat is not a music table: her mode plays RE1's table\n");
        return -1;
    }
    s_groupCount = groups;
    dbg_printf("[music] her table: %d groups, %d rooms\n", groups, rooms);
    return 1;
}

}  // namespace

const unsigned char* RebMusic_RoomTable(void)
{
    if (s_loaded == 0) s_loaded = Load();
    return s_loaded > 0 ? &s_rooms[0][0][0] : NULL;
}

const char* RebMusic_File(unsigned char group, int channel, unsigned char* loop)
{
    *loop = 0;
    const int g = (int)group - REB_MUSIC_FIRST_GROUP;
    if (s_loaded <= 0 || g < 0 || g >= s_groupCount || channel < 0 || channel > 2) return NULL;
    if (s_groups[g].file[channel][0] == '\0') return NULL;
    *loop = s_groups[g].loop[channel];
    return s_groups[g].file[channel];
}
