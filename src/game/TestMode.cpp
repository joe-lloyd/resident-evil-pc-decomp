// TestMode.cpp - automated test support (port addition, test tooling only).
//
// The harness owns all interpretation. This file reports raw values (flag
// words, positions, flag bank bytes) and carries out a handful of commands, so
// the game build stays small and the meaning lives in testable harness code.
#include "../Globals.h"
#include "../platform/platform.h"
#include "TestMode.h"
#include "Feedback.h"
#include "../marni/MarniSystem.h"
#include "../marni/MarniSound.h"
#include <cstdarg>
#include <cstdio>
#include <cstdlib>
#include <cstring>

extern int  DebugRoomChange_Request(int stage, int room);
extern void CountHeldItems(void);   // GameStart.cpp

static int          s_active = 0;
static unsigned int s_frame = 0;
// Held keys expire by the clock, one game frame being 33 ms: during movies the
// main loop spins without game frames, so a frame count would never run down.
static const DWORD  kFrameMs = 33;
static DWORD        s_heldUntil[256];    // plat_time_ms deadline; 0 = up
static const DWORD  kHeldForever = 0xFFFFFFFFu;
static int          s_forceState = 0;
static int          s_lastMessageId = -1;
static int          s_gameplayFrame = 0;  // set by game_loop's inner loop each frame
static int          s_pendingStage = -1;
static int          s_pendingRoom = -1;
static char         s_shotPath[260];
static int          s_shotPending = 0;
static int          s_clientSeen = 0;      // plat_test_link_client_id at the last tick
static char         s_body[8192];
static char         s_lastBody[8192];

static int          s_port = 0;
static int          s_god = 0;

void DevCheat_SetGod(int on) { s_god = on ? 1 : 0; s_forceState = 1; }
int  DevCheat_God(void) { return s_god; }

int TestMode_Start(int port)
{
    if (!plat_test_link_open(port)) return 0;
    s_active = 1;
    s_port = port;
    memset(s_heldUntil, 0, sizeof(s_heldUntil));
    plat_key_inject_exclusive(TRUE);
    return 1;
}

int TestMode_Port(void)
{
    return s_port;
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

static void capture_before_present(void)
{
    g_MarniBeforePresent = NULL;
    s_shotPending = 0;
    int ok = g_MarniFrameBuffer.SaveBitmapToFile(s_shotPath);
    reply("{\"t\":\"ack\",\"cmd\":\"shot\",\"ok\":%d,\"frame\":%u}\n", ok ? 1 : 0, s_frame);
}

int CharSelect_State(int* front);   // CharacterSelectionScreen.cpp

static void on_command(const char* line)
{
    char cmd[32] = "";
    char rest[400] = "";
    sscanf(line, "%31s %399[^\n]", cmd, rest);
    // Replies quote the command back; keep anything odd out of the JSON.
    for (char* c = cmd; *c; c++) {
        if (!((*c >= 'a' && *c <= 'z') || *c == '-')) {
            snprintf(cmd, sizeof(cmd), "?");
            break;
        }
    }
    if (Feedback_IsOpen() && strcmp(cmd, "state") != 0 && strcmp(cmd, "ping") != 0) {
        reply("{\"t\":\"ack\",\"cmd\":\"%s\",\"ok\":0,\"frame\":%u}\n", cmd, s_frame);
        return;
    }
    int a = -1, b = -1, c = -1;
    sscanf(rest, "%i %i %i", &a, &b, &c);

    if (strcmp(cmd, "tap") == 0 && a >= 0 && a < 256) {
        int frames = b > 0 ? (b < 3000 ? b : 3000) : 2;   // at most 100 s
        s_heldUntil[a] = plat_time_ms() + (DWORD)frames * kFrameMs;
    } else if (strcmp(cmd, "down") == 0 && a >= 0 && a < 256) {
        s_heldUntil[a] = kHeldForever;
    } else if (strcmp(cmd, "up") == 0 && a >= 0 && a < 256) {
        s_heldUntil[a] = 0;
    } else if (strcmp(cmd, "release") == 0) {
        memset(s_heldUntil, 0, sizeof(s_heldUntil));
    } else if (strcmp(cmd, "state") == 0) {
        s_forceState = 1;
    } else if (strcmp(cmd, "ping") == 0) {
        reply("{\"t\":\"pong\",\"token\":\"%.64s\",\"frame\":%u}\n", rest, s_frame);
        return;
    } else if (strcmp(cmd, "shot") == 0 && rest[0] != '\0') {
        // Captured just before the next present, while the back buffer still
        // holds a whole frame; the ack is sent from there.
        if (s_shotPending) {
            // The earlier request never reached a present; answer it now.
            reply("{\"t\":\"ack\",\"cmd\":\"shot\",\"ok\":0,\"frame\":%u}\n", s_frame);
        }
        snprintf(s_shotPath, sizeof(s_shotPath), "%s", rest);
        s_shotPending = 1;
        g_MarniBeforePresent = capture_before_present;
        return;
    } else if (strcmp(cmd, "room") == 0 && a >= 0 && b >= 0) {
        s_pendingStage = a;
        s_pendingRoom = b;
    } else if (strcmp(cmd, "pos") == 0 && a >= 0 && a < 0x10000 && b >= 0 && b < 0x10000) {
        // Stand the player at (x = a, z = b) on the floor, facing c when given,
        // the way a door's arrival record places her (DoorSystem.cpp).
        g_playerEntity.scaMatrixData.localMatrix.t[0] = a;
        g_playerEntity.scaMatrixData.localMatrix.t[2] = b;
        g_playerEntity.position.x = (short)a;
        g_playerEntity.position.z = (short)b;
        if (c >= 0) g_playerEntity.directionAngle = (short)c;
    } else if (strcmp(cmd, "give") == 0 && a > 0 && a < 256 && b >= 0 && b < 256) {
        // Put item a, quantity b, in the first empty slot, so a test can start
        // from a point in the game with what she would carry there.
        ItemSlot* items = (ItemSlot*)g_ItemSlotsPointer;
        int capacity = (items == g_RebeccaItemSlots || (g_playerEntity.id & 3) != CHAR_JILL) ? 6 : 8;
        int slot = 0;
        while (items != NULL && slot < capacity && items[slot].Id != 0) slot++;
        if (items == NULL || slot == capacity) {
            reply("{\"t\":\"ack\",\"cmd\":\"give\",\"ok\":0,\"frame\":%u}\n", s_frame);
            return;
        }
        items[slot].Id = (unsigned char)a;
        items[slot].qty = (unsigned char)b;
        // The held-item count (get_item_slot searches only that far) and the
        // status screen's icons, as a new game sets them up.
        LoadHeldItemsImages();
    } else if (strcmp(cmd, "slot") == 0 && a >= 0 && a < 8 && b >= 0 && b < 256 && c >= 0 && c < 256) {
        // Set one slot of her bag outright, to load a playthrough's snapshot.
        ItemSlot* items = (ItemSlot*)g_ItemSlotsPointer;
        if (items) { items[a].Id = (unsigned char)b; items[a].qty = (unsigned char)c; }
        // The game searches only the slots it counts as held (get_item_slot): recount, as it does.
        CountHeldItems();
        reply("{\"t\":\"ack\",\"cmd\":\"slot\",\"ok\":%d}\n", items ? 1 : 0);
    } else if (strcmp(cmd, "boxslot") == 0 && a >= 0 && a < 48 && b >= 0 && b < 256 && c >= 0 && c < 256) {
        g_itemboxSlots[a].Id = (unsigned char)b;
        g_itemboxSlots[a].qty = (unsigned char)c;
        reply("{\"t\":\"ack\",\"cmd\":\"boxslot\",\"ok\":1}\n");
    } else if (strcmp(cmd, "equip") == 0 && a >= 0 && a <= 8 && g_playerEntity.jointsStructs != NULL) {
        // Port addition: checkpoints carry a bag slot, counted from one.
        const ItemSlot* items = (const ItemSlot*)g_ItemSlotsPointer;
        int capacity = (items == g_RebeccaItemSlots || (g_playerEntity.id & 3) != CHAR_JILL) ? 6 : 8;
        int id = items && a > 0 && a <= capacity ? items[a - 1].Id : ITEM_NONE;
        // The item-action menu's predicate, MainMenu.cpp: mode 2, action 0.
        bool weapon = id != ITEM_NONE && (id < ITEM_CLIP || id > ITEM_NON_INFINITE_MAX);
        if (!items || a > capacity || (a && !weapon)) {
            reply("{\"t\":\"ack\",\"cmd\":\"equip\",\"ok\":0,\"frame\":%u}\n", s_frame);
            return;
        }
        g_EquippedItemId = (unsigned char)a;
        extern void menu_update_equipped_weapon(void); // 0x00463ec0
        menu_update_equipped_weapon();
        LoadEquippedWeaponAnimation(g_playerEntity.equippedWeaponId, 0x0e,
                                   (unsigned int)g_animationBuffer, (unsigned int)&g_animObjectBuffer);
    } else if (strcmp(cmd, "keyboard") == 0 && (a == 0 || a == 1)) {
        // A restored feedback mark can be explored by hand with the link open.
        memset(s_heldUntil, 0, sizeof(s_heldUntil));
        plat_key_inject_exclusive(a ? FALSE : TRUE);
    } else if (strcmp(cmd, "unequip") == 0) {
        // Nothing in her hands, as after the mine takes her gear.
        g_EquippedItemId = 0;
        g_playerEntity.equippedWeaponId = 0;
        reply("{\"t\":\"ack\",\"cmd\":\"unequip\",\"ok\":1}\n");
    } else if (strcmp(cmd, "god") == 0 && (a == 0 || a == 1)) {
        DevCheat_SetGod(a);
        reply("{\"t\":\"ack\",\"cmd\":\"god\",\"ok\":1}\n");
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

// --- Dev boot -----------------------------------------------------------------

extern void game_start(void);
extern void SetVideoResolution(int w, int h);   // VideoPlayback.cpp
extern void setSomeColor(int r, int g, int b);  // 0x00470a50

static int s_bootCharacter = -1;
static int s_bootStage = -1;
static int s_bootRoom = -1;
static int s_bootRoomUsed = 0;   // the start room applies to the boot's own game only

int DevBoot_Configure(const char* spec)
{
    char name[16] = "";
    int stage = -1, room = -1;
    char extra = 0;
    int n = sscanf(spec, "%15[a-z]:%i:%i%c", name, &stage, &room, &extra);
    // Either a bare name or name:stage:room; a room needs a stage, and the
    // seven base stages hold at most 32 rooms each.
    if (n == 4 && extra != ' ') return 0;
    if (n != 1 && n < 3) return 0;
    if (n == 1 && spec[strlen(name)] != '\0' && spec[strlen(name)] != ' ') return 0;
    if (n >= 3 && (stage < 0 || stage > 6 || room < 0 || room > 31)) return 0;
    if (strcmp(name, "chris") == 0) s_bootCharacter = CHAR_CHRIS;
    else if (strcmp(name, "jill") == 0) s_bootCharacter = CHAR_JILL;
    else if (strcmp(name, "rebecca") == 0) s_bootCharacter = CHAR_REBECCA;
    else return 0;
    if (n == 3) {
        s_bootStage = stage;
        s_bootRoom = room;
    }
    return 1;
}

int DevBoot_Begin(void)
{
    if (s_bootCharacter < 0) return 0;
    // logos_state's video setup, which the boot skips along with the logos:
    // without it the game draws at 320x240 in the window's top-left corner
    // and the pre-rendered backgrounds never appear.
    SetVideoResolution(640, 480);
    SetVideoResolution(320, 240);
    setSomeColor(128, 128, 128);
    // One boot per launch: dying sends the game back through
    // init_and_start_game, and that must reach the title, not a new game.
    static int s_booted = 0;
    if (s_booted) return 0;
    s_booted = 1;
    g_SelectedCharactedId = (unsigned char)s_bootCharacter;
    // Jill alone has her own room variants; Rebecca walks Chris's rooms.
    if (s_bootCharacter == CHAR_JILL) g_main_state_flags |= MSF_CHAR_VARIANT;
    else g_main_state_flags &= ~MSF_CHAR_VARIANT;
    g_bGameActive = 2;
    Task_chain((void*)game_start);
    return 1;
}

extern int DebugRoomChange_IsSelectable(int stage, int room);

int DevBoot_StartRoom(int* stage, int* room)
{
    if (s_bootCharacter < 0 || s_bootStage < 0 || s_bootRoomUsed) return 0;
    if (!DebugRoomChange_IsSelectable(s_bootStage, s_bootRoom)) {
        dbg_printf("[devboot] stage %d room %02X has no room file; using the normal start\n",
                   s_bootStage, s_bootRoom);
        s_bootStage = -1;
        return 0;
    }
    s_bootRoomUsed = 1;
    *stage = s_bootStage;
    *room = s_bootRoom;
    return 1;
}

void TestMode_GameplayFrame(void)
{
    s_gameplayFrame = 1;
    if (s_god && g_playerEntity.health < g_playerEntity.maxHealth) g_playerEntity.health = g_playerEntity.maxHealth;
    if (s_pendingStage < 0) return;
    int ok = DebugRoomChange_Request(s_pendingStage, s_pendingRoom);
    reply("{\"t\":\"ack\",\"cmd\":\"room-start\",\"ok\":%d,\"frame\":%u}\n", ok, s_frame);
    s_pendingStage = -1;
    s_pendingRoom = -1;
}

// --- State ------------------------------------------------------------------

const char* GameState_Json(void)
{
    s_len = 0;
    put("\"play\":%d,\"god\":%d,\"msf\":\"%08x\",\"msf2\":\"%08x\",\"title\":%d,\"fmv\":%d,\"dbg\":%d,",
        s_gameplayFrame, s_god, (unsigned int)g_MainStateFlagBank[0], (unsigned int)g_MainStateFlagBank[1],
        (int)g_titleMode, plat_video_is_active() ? 1 : 0, g_debugMenuOpen);
    put("\"stage\":%d,\"room\":%d,\"cam\":%d,\"cut\":%d,\"charModel\":%d,",
        (int)g_stageId, (int)g_roomId, (int)g_roomCameraId, (int)g_cutId,
        (int)g_CharacterModelId);

    const PlayerEntity& p = g_playerEntity;
    put("\"player\":{\"id\":%d,\"x\":%d,\"y\":%d,\"z\":%d,\"angle\":%d,\"hp\":%d,"
        "\"maxHp\":%d,\"weapon\":%d,\"cf\":%d,\"anim\":[%d,%d,%d],\"action\":[%d,%d,%d,%d]},",
        (int)p.id, (int)p.position.x, (int)p.position.y, (int)p.position.z,
        (int)p.directionAngle, (int)p.health, (int)p.maxHealth, (int)g_EquippedItemId,
        (int)p.healthStatusFlags, (int)p.animationId, (int)p.attackAnim, (int)p.animation_frame_id,
        (int)p.animationId, (int)p.animFrameId, (int)p.action_behavior, (int)p.action_state);

    // Rebecca and Chris carry 6 items, Jill 8.
    const ItemSlot* items = (const ItemSlot*)g_ItemSlotsPointer;
    int capacity = (items == g_RebeccaItemSlots || (p.id & 3) != CHAR_JILL) ? 6 : 8;
    put("\"items\":[");
    for (int i = 0; items != NULL && i < capacity; i++) {
        put("%s[%d,%d]", i ? "," : "", (int)items[i].Id, (int)items[i].qty);
    }
    // The item box's 48 slots, shared by every box in the game.
    put("],\"box\":[");
    for (int i = 0; i < 48; i++) {
        put("%s[%d,%d]", i ? "," : "", (int)g_itemboxSlots[i].Id, (int)g_itemboxSlots[i].qty);
    }
    put("],\"enemies\":[");
    // enemy_set puts each enemy in the slot its script names, so the live ones
    // are not the first g_enemy_count slots; a door clears every slot's status.
    bool first = true;
    for (int i = 0; i < 30; i++) {
        const Entity& e = g_EnemiesList[i];
        if (e.status_flags == 0) continue;
        put("%s[%d,%d,%d,%d,%d,%d]", first ? "" : ",", (int)e.id, (int)e.status_flags,
            (int)e.position.x, (int)e.position.y, (int)e.position.z, (int)e.health);
        first = false;
    }
    int selFront = -1;
    const int selState = CharSelect_State(&selFront);
    put("],\"msg\":{\"choice\":%d,\"id\":%d,\"flags\":%d,\"menu\":%d},\"sel\":{\"state\":%d,\"front\":%d},\"used\":%d,\"banks\":[",
        (int)g_menu_choice_id, s_lastMessageId, (int)g_message_flags, (int)g_openMenuFlag, selState, selFront, (int)g_usedItemId);
    for (int bank = 0; bank < 10; bank++) {
        FlagBank fb = flag_bank(bank);
        if (bank) put(",");
        put_hex(fb.data, fb.size);
    }
    put("],\"bgm\":{\"state\":%d,\"ch\":[", (int)(unsigned char)g_BGM_STATE);
    // Each BGM channel: the WAV it loaded ("" for none), playing, and volume.
    for (int ch = 0; ch < 3; ch++) {
        const char* file = bgm_channel_file(ch);
        const int bank = g_SndBank[ch].handle;
        put("%s[\"%s\",%d,%d]", ch ? "," : "", file ? file : "", getSndStat(bank), bank ? getSndVol(bank) : 0);
    }
    // Sound: the footstep set under the player and the walk step it loaded,
    // her steps played and the last one's file; the room sound set and its
    // two files (a door's open and close), how many played and the last.
    int set = -1;
    if (s_gameplayFrame && g_RdtPointer != NULL && g_RdtPointer->footstep_sound_zones != NULL) {
        set = LookupFootstepZone((short)p.position.x, (short)p.position.z) & 0xFF;
    }
    const char* walk = set >= 0 ? emsnd_slot_file(set) : NULL;
    const char* room0 = room_sfx_file(0);
    const char* room1 = room_sfx_file(1);
    const SoundProbe& sp = g_soundProbe;
    put("]},\"snd\":{\"set\":%d,\"walk\":\"%s\",\"steps\":%u,\"step\":\"%s\",\"door\":%d,\"room\":[\"%s\",\"%s\"],\"sfx\":%u,\"last\":\"%s\",\"recent\":[",
        set, walk ? walk : "", sp.step.plays, sp.step.last ? sp.step.last : "", (int)sp.roomSet,
        room0 ? room0 : "", room1 ? room1 : "", sp.room.plays, sp.room.last ? sp.room.last : "");
    // The last eight room sounds, oldest first: a door or a walk can play several in a frame.
    const unsigned int n = sp.room.plays < 8 ? sp.room.plays : 8;
    for (unsigned int i = 0; i < n; i++) {
        const char* f = sp.room.recent[(sp.room.plays - n + i) % 8];
        put("%s\"%s\"", i ? "," : "", f ? f : "");
    }
    put("]}");
    // Do not persist or send a truncated JSON document.
    if (s_len >= (int)sizeof(s_body)) return NULL;
    static char json[8500]; // Port addition: includes the shared body and test-link envelope.
    snprintf(json, sizeof(json), "{\"t\":\"state\",\"frame\":%u,%s}", s_frame, s_body);
    return json;
}

void TestMode_Tick(int gameFrame)
{
    if (!s_active) return;
    const bool editing = Feedback_IsOpen() != 0;
    if (gameFrame && !editing) s_frame++;
    plat_test_link_poll(on_command);

    // A new client starts clean: nothing held from the last one, and a state
    // line straight away even if the game is idle.
    if (plat_test_link_client_id() != s_clientSeen) {
        s_clientSeen = plat_test_link_client_id();
        memset(s_heldUntil, 0, sizeof(s_heldUntil));
        s_forceState = 1;
    }

    DWORD now = plat_time_ms();
    for (int vk = 0; !editing && vk < 256; vk++) {
        if (s_heldUntil[vk] != 0 && s_heldUntil[vk] != kHeldForever && now >= s_heldUntil[vk]) {
            s_heldUntil[vk] = 0;
        }
        plat_key_inject(vk, s_heldUntil[vk] != 0);
    }

    const char* json = GameState_Json();
    if (gameFrame && !editing) s_gameplayFrame = 0;
    if (!json) return;
    if (s_forceState || strcmp(s_body, s_lastBody) != 0) {
        plat_test_link_send(json);
        plat_test_link_send("\n");
        memcpy(s_lastBody, s_body, sizeof(s_body));
        s_forceState = 0;
    }
}
