// Port addition: feedback capture, no original addresses. State gathering is
// shared with the test link in TestMode.cpp. OS input and files use platform.h.
#include "../Globals.h"
#include "../Version.h"
#include "../platform/platform.h"
#include "../system/AssetPath.h"
#include "Feedback.h"
#include "TestMode.h"
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <string>
#include <vector>

namespace {
// Port-only state, outside the original game's reset/save blocks.
bool enabled = false, requested = false, open = false;
const char* const kinds[] = { "clipping", "drawn-over", "item", "enemy", "text", "other" };
int kind = 0;
std::string note, state, error;
std::vector<unsigned char> pixels;
MarniHandle frozen = MARNI_NULL_HANDLE;
DWORD width = 0, height = 0, capturedAt = 0, lastSample = 0;
char wallTime[32], stamp[32], directory[1024];
struct Spot { DWORD ms; int stage, room, cam, x, y, z, angle; };
Spot trail[40]; // 10 seconds at 4 Hz
unsigned int samples = 0;

std::string quote(const std::string& text)
{
    std::string out = "\"";
    for (unsigned char c : text) {
        if (c == '"' || c == '\\') out += '\\';
        if (c < 32) {
            char escape[7];
            snprintf(escape, sizeof(escape), "\\u%04x", c);
            out += escape;
        } else out += (char)c;
    }
    return out + '"';
}

bool save()
{
    if (pixels.empty() || state.empty()) { error = "Capture failed. Esc cancels."; return false; }
    if (!directory[0]) {
        char root[1024];
        snprintf(root, sizeof(root), "%sfeedback", GetSaveRoot());
        if (!plat_mkdir(GetSaveRoot()) || !plat_mkdir(root)) {
            error = "Cannot create feedback folder.";
            return false;
        }
        // Exclusive creation keeps two quick marks in the same second apart.
        for (int i = 0; i < 100; i++) {
            if (i == 0) snprintf(directory, sizeof(directory), "%s/%s", root, stamp);
            else snprintf(directory, sizeof(directory), "%s/%s-%02d", root, stamp, i);
            if (plat_mkdir_new(directory)) break;
            directory[0] = 0;
        }
        if (!directory[0]) { error = "Cannot create entry folder."; return false; }
    }
    char header[64], file[1100];
    int n = snprintf(header, sizeof(header), "RE1CAP %u %u\n", (unsigned)width, (unsigned)height);
    std::vector<unsigned char> raw(header, header + n);
    raw.insert(raw.end(), pixels.begin(), pixels.end());
    snprintf(file, sizeof(file), "%s/shot.rgba", directory);
    if (!plat_file_write(file, raw.data(), raw.size())) {
        error = "Cannot save shot. Enter retries.";
        return false;
    }
    std::string json = "{\"version\":1,\"kind\":" + quote(kinds[kind]) + ",\"text\":" + quote(note) +
        ",\"time\":" + quote(wallTime) + ",\"mode\":" + quote(GetAssetModeName()[0] ? GetAssetModeName() : "OG") +
        ",\"build\":{\"version\":\"" GAME_VERSION_STRING "\",\"compiled\":\"" __DATE__ " " __TIME__ "\"},\"state\":" + state + ",\"path\":[";
    bool first = true;
    unsigned int count = samples < 40 ? samples : 40;
    for (unsigned int i = 0; i < count; i++) {
        const Spot& p = trail[(samples - count + i) % 40];
        DWORD age = capturedAt - p.ms;
        if (age > 10000) continue;
        char point[256];
        snprintf(point, sizeof(point), "%s{\"agoMs\":%u,\"stage\":%d,\"room\":%d,\"cam\":%d,\"x\":%d,\"y\":%d,\"z\":%d,\"angle\":%d}",
                 first ? "" : ",", (unsigned)age, p.stage, p.room, p.cam, p.x, p.y, p.z, p.angle);
        json += point;
        first = false;
    }
    json += "]}\n";
    snprintf(file, sizeof(file), "%s/note.json", directory);
    if (!plat_file_write(file, json.data(), json.size())) {
        error = "Cannot save note. Enter retries.";
        return false;
    }
    dbg_printf("[feedback] saved %s\n", directory);
    return true;
}
}

void Feedback_Enable(void) { enabled = true; }
int Feedback_IsOpen(void) { return open || requested; }

int Feedback_Key(int vk, int repeat)
{
    if (requested) {
        // A transition can prevent the requested present. Esc must work even
        // while the movie pump owns the loop and no game frames are running.
        if (vk == VK_ESCAPE) { requested = false; plat_text_input(FALSE); }
        return 1;
    }
    if (open) return 1;
    if (!(enabled || g_bRebMode) || vk != VK_F9) return 0;
    // F9 belongs to feedback whenever enabled, including the title and movies.
    if (!repeat && g_playingGameFlag && !plat_video_is_active()) {
        requested = true;
        note.clear(); error.clear(); directory[0] = 0;
        kind = 0;
        plat_text_input(TRUE);
    }
    return 1;
}

void Feedback_BeforePresent(void)
{
    if (requested && (!g_playingGameFlag || plat_video_is_active())) {
        requested = false;
        plat_text_input(FALSE);
    }
    if (!(enabled || g_bRebMode) || open || !g_playingGameFlag || plat_video_is_active()) return;
    DWORD now = plat_time_ms();
    if (samples == 0 || now - lastSample >= 250 || requested) {
        const PlayerEntity& p = g_playerEntity;
        trail[samples++ % 40] = { now, g_stageId, g_roomId, g_roomCameraId,
            p.position.x, p.position.y, p.position.z, p.directionAngle };
        lastSample = now;
    }
    if (!requested) return;
    requested = false;
    open = true;
    capturedAt = now;
    plat_wall_time(wallTime, sizeof(wallTime), stamp, sizeof(stamp));
    const char* json = GameState_Json();
    state = json ? json : "";
    void* rgba = NULL;
    MarniDX* dx = Marni_DX();
    pixels.clear();
    if (dx && dx->CaptureBackbufferToRGBA(&rgba, &width, &height) && rgba) {
        pixels.assign((unsigned char*)rgba, (unsigned char*)rgba + (size_t)width * height * 4);
        frozen = dx->CreateTexture((int)width, (int)height, 32, rgba, NULL, NULL);
    }
    free(rgba);
    PauseSounds();
}

int Feedback_Frame(void)
{
    if (requested && (!g_playingGameFlag || plat_video_is_active() || (g_main_state_flags & MSF_FMV_REQUEST))) {
        requested = false;
        plat_text_input(FALSE);
    }
    if (!open) return 0;
    bool close = false;
    for (int c; (c = plat_text_input_read()) != 0;) {
        if (c == 27) { close = true; break; }
        if (c == 13) { close = save(); break; }
        if (c == 8) { if (!note.empty()) note.pop_back(); }
        else if (c == 9) kind = (kind + 1) % 6;
        else if (c >= 32 && c <= 126 && note.size() < 240) note += (char)c;
    }
    if (close) {
        // Return without running a game frame. Keys still physically held are
        // suppressed by the platform until released, including Enter/Escape.
        plat_text_input(FALSE);
        open = false;
        if (Marni_DX()) Marni_DX()->DestroyTexture(frozen);
        frozen = MARNI_NULL_HANDLE;
        pixels.clear();
        ResumePausedSounds();
        return 1;
    }
    char heading[64];
    snprintf(heading, sizeof(heading), "Feedback: %s", kinds[kind]);
    std::vector<std::string> rows;
    rows.push_back(heading);
    rows.push_back("Tab: kind  Enter: save  Esc: cancel");
    for (size_t i = 0; i < note.size(); i += 34) rows.push_back(note.substr(i, 34));
    rows.push_back(error.empty() ? "Type a note, or save an empty mark." : error);
    std::vector<const char*> lines;
    for (const std::string& row : rows) lines.push_back(row.c_str());
    RenderFeedbackFrame(frozen, lines.data(), (int)lines.size());
    return 1;
}
