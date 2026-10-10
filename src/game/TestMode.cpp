// TestMode.cpp - automated test support (port addition, test tooling only).
//
// The harness owns all interpretation. This file reports raw values (flag
// words, positions, flag bank bytes) and carries out a handful of commands, so
// the game build stays small and the meaning lives in testable harness code.
#include "../Globals.h"
#include "../platform/platform.h"
#include "TestMode.h"
#include <cstdarg>
#include <cstdio>
#include <cstdlib>
#include <cstring>

extern int  DebugRoomChange_Request(int stage, int room);

static int          s_active = 0;
static unsigned int s_frame = 0;
static int          s_heldFrames[256];   // frames left; -1 = held until released
static int          s_forceState = 0;
static int          s_lastMessageId = -1;
static int          s_pendingStage = -1;
static int          s_pendingRoom = -1;
static char         s_body[8192];
static char         s_lastBody[8192];

int TestMode_Start(int port)
{
    if (!plat_test_link_open(port)) return 0;
    s_active = 1;
    memset(s_heldFrames, 0, sizeof(s_heldFrames));
    plat_key_inject_exclusive(TRUE);
    return 1;
}

int TestMode_Active(void)
{
    return s_active;
}

void TestMode_NoteMessage(unsigned short msgId)
{
    s_lastMessageId = msgId;
}

// --- Output helpers ---------------------------------------------------------

static int s_len;

static void put(const char* fmt, ...)
{
    if (s_len >= (int)sizeof(s_body)) return;
    va_list ap;
    va_start(ap, fmt);
    int n = vsnprintf(s_body + s_len, sizeof(s_body) - (size_t)s_len, fmt, ap);
    va_end(ap);
    if (n > 0) s_len += n;
}

static void put_hex(const void* data, int size)
{
    const unsigned char* p = (const unsigned char*)data;
    put("\"");
    for (int i = 0; i < size; i++) put("%02x", p[i]);
    put("\"");
}

static void reply(const char* fmt, ...)
{
    char line[512];
    va_list ap;
    va_start(ap, fmt);
    vsnprintf(line, sizeof(line), fmt, ap);
    va_end(ap);
    plat_test_link_send(line);
}

// --- Commands ---------------------------------------------------------------

// Flag banks in the order cmd_bit_test numbers them (CmdFunctions.cpp:149).
struct FlagBank { void* data; int size; };

static FlagBank flag_bank(int bank)
{
    switch (bank) {
    case 0: return { &g_ScenarioFlags, (int)sizeof(g_ScenarioFlags) };
    case 1: return { &g_ScenarioFlags2, (int)sizeof(g_ScenarioFlags2) };
    case 2: return { g_LocksFlags, (int)sizeof(g_LocksFlags) };
    case 3: return { g_EnemiesFlags, (int)sizeof(g_EnemiesFlags) };
    case 4: return { g_SysFlags, (int)sizeof(g_SysFlags) };
    case 5: return { g_MainStateFlagBank, (int)sizeof(g_MainStateFlagBank) };
    case 6: return { &g_message_flags, (int)sizeof(g_message_flags) };
    case 7: return { &g_roomItemsFlags, (int)sizeof(g_roomItemsFlags) };
    case 8: return { &g_RoomFlags, (int)sizeof(g_RoomFlags) };
    case 9: return { g_itemUseFlags, (int)sizeof(g_itemUseFlags) };
    default: return { NULL, 0 };
    }
}

static void on_command(const char* line)
{
    char cmd[32] = "";
    char rest[400] = "";
    sscanf(line, "%31s %399[^\n]", cmd, rest);
    int a = -1, b = -1, c = -1;
    sscanf(rest, "%i %i %i", &a, &b, &c);

    if (strcmp(cmd, "tap") == 0 && a >= 0 && a < 256) {
        s_heldFrames[a] = b > 0 ? b : 2;
    } else if (strcmp(cmd, "down") == 0 && a >= 0 && a < 256) {
        s_heldFrames[a] = -1;
    } else if (strcmp(cmd, "up") == 0 && a >= 0 && a < 256) {
        s_heldFrames[a] = 0;
    } else if (strcmp(cmd, "release") == 0) {
        memset(s_heldFrames, 0, sizeof(s_heldFrames));
    } else if (strcmp(cmd, "state") == 0) {
        s_forceState = 1;
    } else if (strcmp(cmd, "ping") == 0) {
        reply("{\"t\":\"pong\",\"token\":\"%.64s\",\"frame\":%u}\n", rest, s_frame);
        return;
    } else if (strcmp(cmd, "shot") == 0 && rest[0] != '\0') {
        int ok = g_MarniFrameBuffer.SaveBitmapToFile(rest);
        reply("{\"t\":\"ack\",\"cmd\":\"shot\",\"ok\":%d,\"frame\":%u}\n", ok ? 1 : 0, s_frame);
        return;
    } else if (strcmp(cmd, "room") == 0 && a >= 0 && b >= 0) {
        s_pendingStage = a;
        s_pendingRoom = b;
    } else if (strcmp(cmd, "flag") == 0 && a >= 0 && b >= 0 && b < 256 && (c == 0 || c == 1)) {
        FlagBank fb = flag_bank(a);
        int byteAt = (b >> 5) * 4;
        if (fb.data == NULL || byteAt + 4 > fb.size) {
            reply("{\"t\":\"ack\",\"cmd\":\"flag\",\"ok\":0,\"frame\":%u}\n", s_frame);
            return;
        }
        // Same bit order as cmd_bit_op: bit 0 of a word is its top bit.
        unsigned int* word = (unsigned int*)((char*)fb.data + byteAt);
        unsigned int mask = 0x80000000u >> (b & 31);
        *word = c ? (*word | mask) : (*word & ~mask);
    } else {
        reply("{\"t\":\"ack\",\"cmd\":\"%.31s\",\"ok\":0,\"frame\":%u}\n", cmd, s_frame);
        return;
    }
    reply("{\"t\":\"ack\",\"cmd\":\"%s\",\"ok\":1,\"frame\":%u}\n", cmd, s_frame);
}

void TestMode_RunPendingRoomChange(void)
{
    if (!s_active || s_pendingStage < 0) return;
    int ok = DebugRoomChange_Request(s_pendingStage, s_pendingRoom);
    reply("{\"t\":\"ack\",\"cmd\":\"room-start\",\"ok\":%d,\"frame\":%u}\n", ok, s_frame);
    s_pendingStage = -1;
    s_pendingRoom = -1;
}

// --- State ------------------------------------------------------------------

static void build_state(void)
{
    s_len = 0;
    put("\"msf\":\"%08x\",\"msf2\":\"%08x\",\"title\":%d,\"fmv\":%d,\"dbg\":%d,",
        (unsigned int)g_MainStateFlagBank[0], (unsigned int)g_MainStateFlagBank[1],
        (int)g_titleMode, plat_video_is_active() ? 1 : 0, g_debugMenuOpen);
    put("\"stage\":%d,\"room\":%d,\"cam\":%d,\"cut\":%d,\"charModel\":%d,",
        (int)g_stageId, (int)g_roomId, (int)g_roomCameraId, (int)g_cutId,
        (int)g_CharacterModelId);

    const PlayerEntity& p = g_playerEntity;
    put("\"player\":{\"id\":%d,\"x\":%d,\"y\":%d,\"z\":%d,\"angle\":%d,\"hp\":%d,"
        "\"maxHp\":%d,\"weapon\":%d},",
        (int)p.id, (int)p.position.x, (int)p.position.y, (int)p.position.z,
        (int)p.directionAngle, (int)p.health, (int)p.maxHealth, (int)g_EquippedItemId);

    // Rebecca and Chris carry 6 items, Jill 8.
    const ItemSlot* items = (const ItemSlot*)g_ItemSlotsPointer;
    int capacity = (items == g_RebeccaItemSlots || (p.id & 3) != CHAR_JILL) ? 6 : 8;
    put("\"items\":[");
    for (int i = 0; items != NULL && i < capacity; i++) {
        put("%s[%d,%d]", i ? "," : "", (int)items[i].Id, (int)items[i].qty);
    }
    put("],\"enemies\":[");
    int count = g_enemy_count < 30 ? g_enemy_count : 30;
    for (int i = 0; i < count; i++) {
        const Entity& e = g_EnemiesList[i];
        put("%s[%d,%d,%d,%d,%d,%d]", i ? "," : "", (int)e.id, (int)e.status_flags,
            (int)e.position.x, (int)e.position.y, (int)e.position.z, (int)e.health);
    }
    put("],\"msg\":{\"choice\":%d,\"id\":%d},\"banks\":[",
        (int)g_menu_choice_id, s_lastMessageId);
    for (int bank = 0; bank < 10; bank++) {
        FlagBank fb = flag_bank(bank);
        if (bank) put(",");
        put_hex(fb.data, fb.size);
    }
    put("]");
}

void TestMode_Tick(void)
{
    if (!s_active) return;
    s_frame++;
    plat_test_link_poll(on_command);

    for (int vk = 0; vk < 256; vk++) {
        plat_key_inject(vk, s_heldFrames[vk] != 0);
        if (s_heldFrames[vk] > 0) s_heldFrames[vk]--;
    }

    build_state();
    if (s_forceState || strcmp(s_body, s_lastBody) != 0) {
        char head[64];
        snprintf(head, sizeof(head), "{\"t\":\"state\",\"frame\":%u,", s_frame);
        plat_test_link_send(head);
        plat_test_link_send(s_body);
        plat_test_link_send("}\n");
        memcpy(s_lastBody, s_body, sizeof(s_body));
        s_forceState = 0;
    }
}
