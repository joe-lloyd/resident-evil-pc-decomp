// Exercise the Linux platform's text queue and key suppression without a
// window or game. SDL text-start/stop calls are replaced at the OS boundary.
// clang++ -std=c++17 -Isrc tests/feedback_input.cpp \
//   src/platform/linux/platform.cpp -Wl,-dead_strip -o /tmp/feedback-input
// Linux linkers use -Wl,--gc-sections with -ffunction-sections instead.
#include "platform/platform.h"
#include <SDL2/SDL.h>
#include <cassert>

extern "C" void SDL_StartTextInput(void) {}
extern "C" void SDL_StopTextInput(void) {}

int main()
{
    plat_key_event(SDL_SCANCODE_E, TRUE);
    plat_text_input(TRUE);
    assert(plat_key_state('E') == 0);
    const int characters[] = { 'a', 8, 9, 13, 27 };
    for (int c : characters) plat_text_input_event(c);
    plat_text_input_event(233); // The editor accepts printable ASCII and controls.
    for (int c : characters) assert(plat_text_input_read() == c);
    assert(plat_text_input_read() == 0);

    plat_text_input(FALSE);
    assert(plat_key_state('E') == 0); // Still held through closing.
    plat_key_event(SDL_SCANCODE_E, TRUE); // Auto-repeat does not release it.
    assert(plat_key_state('E') == 0);
    plat_key_event(SDL_SCANCODE_E, FALSE);
    plat_key_event(SDL_SCANCODE_E, TRUE); // A new physical press must work.
    assert(plat_key_state('E') == 0x8001);
    assert(plat_key_state('E') == 0x8000);
    plat_key_event(SDL_SCANCODE_E, FALSE);
    assert(plat_key_state('E') == 0);

    plat_key_event(SDL_SCANCODE_RETURN, TRUE);
    plat_text_input(TRUE);
    plat_text_input_event(13);
    plat_text_input(FALSE);
    assert(plat_text_input_read() == 0); // No queued Enter after closing.
    assert(plat_key_state(VK_RETURN) == 0);
    plat_key_event(SDL_SCANCODE_RETURN, FALSE);
    assert(plat_key_state(VK_RETURN) == 0);
}
