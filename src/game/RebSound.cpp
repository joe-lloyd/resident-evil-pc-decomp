// Her mode's room sounds (port addition).
//
// RE1 loads a room's entity sounds (its footsteps, its enemies' cries, the
// things in it that make a noise) by name from a compiled table indexed by the
// room's stage and id (g_RoomSoundNameTable, Room_LoadEnemySoundBanks). Her
// rooms sit in free slots, whose rows are empty or, past room 0x1C, run on
// into the next stage's first rooms. So her mode lays her own names over
// those rows. Slots she doesn't set keep the row's.
//
// sound\rooms.dat, little-endian:
//
//   char magic[4] "RBS1"
//   u8   roomCount
//   u8   pad[3]
//   room[roomCount]: u8   stage       0-6, as get_stage_id counts
//                    u8   room        0-31
//                    u8   slotCount
//                    u8   pad
//                    slot[slotCount]: u8   slot      0-47
//                                     char name[15] NUL-terminated WAV base
//                                                   name under sound\, "" to
//                                                   leave the slot empty
#include "RebSound.h"
#include "../DebugPrint.h"
#include "../platform/platform.h"
#include "../system/AssetPath.h"

#include <stdlib.h>
#include <string.h>

namespace {

const int kNameLen = 15;
const int kSlotSize = 1 + kNameLen;
const int kSlots = 48;
const int kMaxSlots = 4096;

struct Slot {
    unsigned char stage, room, slot;
    char name[kNameLen];
};

int s_loaded = 0;  // 0 not tried, 1 loaded, -1 missing or bad
Slot s_slots[kMaxSlots];
int s_count = 0;

int Load(void)
{
    char resolved[260], normalized[260];
    const char* file = plat_normalize_path(ResolveAssetRoot(GAME_DATA_ROOT "sound\\rooms.dat", resolved, sizeof(resolved)),
                                           normalized, sizeof(normalized));
    size_t size = 0;
    unsigned char* data = (unsigned char*)plat_file_read_all(file, &size);
    if (data == NULL) {
        dbg_printf("[sound] no sound\\rooms.dat: her rooms keep RE1's rows\n");
        return -1;
    }
    bool ok = size >= 8 && memcmp(data, "RBS1", 4) == 0;
    const int rooms = ok ? data[4] : 0;
    size_t at = 8;
    int count = 0;
    for (int r = 0; ok && r < rooms; r++) {
        ok = at + 4 <= size && data[at] < 7 && data[at + 1] < 32;
        const int slots = ok ? data[at + 2] : 0;
        const unsigned char stage = ok ? data[at] : 0, room = ok ? data[at + 1] : 0;
        at += 4;
        ok = ok && at + (size_t)slots * kSlotSize <= size && count + slots <= kMaxSlots;
        for (int i = 0; ok && i < slots; i++, at += kSlotSize) {
            ok = data[at] < kSlots && memchr(data + at + 1, 0, kNameLen) != NULL;
            Slot& s = s_slots[count++];
            s.stage = stage;
            s.room = room;
            s.slot = data[at];
            memcpy(s.name, data + at + 1, kNameLen);
        }
    }
    ok = ok && at == size;
    free(data);
    if (!ok) {
        dbg_printf("[sound] sound\\rooms.dat is not a room sound table: her rooms keep RE1's rows\n");
        return -1;
    }
    s_count = count;
    dbg_printf("[sound] her room sounds: %d rooms, %d slots\n", rooms, count);
    return 1;
}

}  // namespace

const char* RebSound_Slot(int stage, int room, int slot)
{
    if (s_loaded == 0) s_loaded = Load();
    if (s_loaded <= 0) return NULL;
    for (int i = 0; i < s_count; i++) {
        const Slot& s = s_slots[i];
        if (s.stage == stage && s.room == room && s.slot == slot) return s.name;
    }
    return NULL;
}
