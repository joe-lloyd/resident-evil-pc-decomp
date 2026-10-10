// stubs.cpp - placeholders for the few Windows-only entry points the
// shared code still references.
//
// Every phase's subsystem now has a real Linux implementation:
//   input  -> input.cpp (P5)
//   audio  -> audio.cpp (P6)
//   FMV    -> video.cpp + src/video/VideoPlayback.cpp (P7)
//   misc   -> config.cpp / crash.cpp (P8)
// What is left here is the message box and the two stubs the shared code calls
// but that have no Linux meaning.
#include <SDL2/SDL.h>

#include "Globals.h"
#include "marni/MarniInput.h"
#include "marni/MarniSound.h"
#include "marni/MarniSystem.h"
#include "marni/MarniXInput.h"

int ShowMessageBox(HWND hWnd, LPCSTR lpMsg, LPCSTR lpCaption, UINT uType)
{
    (void)hWnd;
    Uint32 flags = (uType & MB_ICONSTOP) ? SDL_MESSAGEBOX_ERROR
                                         : SDL_MESSAGEBOX_INFORMATION;
    SDL_ShowSimpleMessageBox(flags, lpCaption ? lpCaption : "RESIDENT EVIL",
                             lpMsg ? lpMsg : "", NULL);
    return 1;   // IDOK
}

// Test mode (src/game/TestMode.cpp) has no Linux transport yet: the link never
// opens, so TestMode_Start fails and nothing else here is reached.
BOOL plat_test_link_open(int port) { (void)port; return FALSE; }
void plat_test_link_poll(void (*on_line)(const char* line)) { (void)on_line; }
void plat_test_link_send(const char* text) { (void)text; }
void plat_key_inject_exclusive(BOOL on) { (void)on; }
void plat_key_inject(int vk, BOOL down) { (void)vk; (void)down; }
