// Port addition: playthrough feedback. No original functions or addresses.
#pragma once
#include "../marni/MarniDX.h"

void Feedback_Enable(void); // --feedback; REB also enables it by default
int Feedback_IsOpen(void);
// Called by platform key handlers before the original F9 handler.
int Feedback_Key(int vk, int repeat);
// Capture the completed frame, using the same readback as TestMode's shot.
void Feedback_BeforePresent(void);
// Returns 1 while editing. main_loop must skip input and game tasks that frame.
int Feedback_Frame(void);
// Rendering.cpp owns the pending font sprites used by this editor.
void RenderFeedbackFrame(MarniHandle frozen, const char* const* lines, int count);
