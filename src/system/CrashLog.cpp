// CrashLog.cpp - startup crash diagnostics for standalone (non-debugger) runs.
//
// The Release build died at boot with 0xC0000409 (fail-fast) raised through
// KERNELBASE!RaiseFailFastException. Fail-fast itself cannot be intercepted,
// but its usual triggers can: CRT invalid parameters, pure virtual calls,
// abort()/SIGABRT and ordinary unhandled exceptions all pass through the
// handlers registered here before the CRT escalates to fail-fast. Each one
// appends a symbolized stack trace to crash.log next to the exe, so a
// standalone run tells us exactly where it died.
//
// Dev tooling - no original counterpart.

#include "Globals.h"
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <DbgHelp.h>
#include <csignal>
#include <cstdlib>
#include <cstdarg>
#include <cstdio>
#include <cstring>

#pragma comment(lib, "dbghelp.lib")

static void write_frame(FILE* f, HANDLE proc, SYMBOL_INFO* sym, unsigned i, DWORD64 addr)
{
    DWORD64 disp = 0;
    if (SymFromAddr(proc, addr, &disp, sym)) {
        fprintf(f, "  #%02u %s+0x%llx (0x%08llX)\n",
                i, sym->Name, (unsigned long long)disp, (unsigned long long)addr);
    } else {
        fprintf(f, "  #%02u 0x%08llX\n", i, (unsigned long long)addr);
    }
}

static void write_stack(FILE* f)
{
    void* frames[24];
    USHORT n = CaptureStackBackTrace(1, 24, frames, NULL);

    HANDLE proc = GetCurrentProcess();
    SymSetOptions(SYMOPT_UNDNAME | SYMOPT_DEFERRED_LOADS);
    SymInitialize(proc, NULL, TRUE);

    SYMBOL_INFO* sym = (SYMBOL_INFO*)calloc(1, sizeof(SYMBOL_INFO) + 256);
    sym->MaxNameLen = 255;
    sym->SizeOfStruct = sizeof(SYMBOL_INFO);

    for (USHORT i = 0; i < n; i++) {
        write_frame(f, proc, sym, i, (DWORD64)frames[i]);
    }
    free(sym);
}

static void report(const char* kind, FILE* f)
{
    fprintf(f, "\n==== %s ====\n", kind);
    write_stack(f);
    fflush(f);
    fclose(f);
}

static FILE* open_log(void)
{
    // Write next to the EXE, not the process CWD. A shortcut or a launcher can
    // change the working directory to somewhere the user never looks, which
    // made it look like "no crash log written" when the log was actually going
    // to the shortcut's start-in folder.
    static char path[MAX_PATH];
    GetModuleFileNameA(NULL, path, MAX_PATH);
    char* slash = strrchr(path, '\\');
    if (slash) *slash = '\0';
    strcat_s(path, "\\crash.log");
    return fopen(path, "a");
}

static void __cdecl on_invalid_parameter(const wchar_t*, const wchar_t*,
                                         const wchar_t*, unsigned int, uintptr_t)
{
    FILE* f = open_log();
    if (f) report("CRT INVALID PARAMETER", f);
}

static void __cdecl on_purecall(void)
{
    FILE* f = open_log();
    if (f) report("PURE VIRTUAL CALL", f);
}

static void on_sigabrt(int)
{
    FILE* f = open_log();
    if (f) report("SIGABRT (abort())", f);
    // let the CRT continue to its own reporting
    signal(SIGABRT, SIG_DFL);
}

static LONG WINAPI on_unhandled(EXCEPTION_POINTERS* ep)
{
    // The vectored handler sees EVERY exception, including benign ones raised
    // by the graphics driver and CRT internals (0x406D1388 GPU throttling,
    // 0x40010006 debugger message, 0x40000015/0x4000001E debug events) that
    // Windows intentionally passes around and nobody ever "handles" - they are
    // not crashes. Only record the codes that actually kill the process.
    switch (ep->ExceptionRecord->ExceptionCode) {
    case 0xC0000005:  // access violation
    case 0xC00000FD:  // stack overflow
    case 0xC000001D:  // illegal instruction
    case 0xC0000094:  // integer divide by zero
    case 0xC0000096:  // privileged instruction
    case 0x80000003:  // breakpoint
    case 0x00000000:  // anything else genuinely odd
        break;
    default:
        return EXCEPTION_CONTINUE_SEARCH;
    }

    FILE* f = open_log();
    if (f) {
        fprintf(f, "\n==== UNHANDLED EXCEPTION 0x%08lX at 0x%08llX ====\n",
                (unsigned long)ep->ExceptionRecord->ExceptionCode,
                (unsigned long long)(uintptr_t)ep->ExceptionRecord->ExceptionAddress);
        if (ep->ContextRecord) {
            fprintf(f, "EIP=%08llX ESP=%08llX EBP=%08llX EAX=%08llX EBX=%08llX "
                       "ECX=%08llX EDX=%08llX ESI=%08llX EDI=%08llX\n",
                    (unsigned long long)ep->ContextRecord->Eip,
                    (unsigned long long)ep->ContextRecord->Esp,
                    (unsigned long long)ep->ContextRecord->Ebp,
                    (unsigned long long)ep->ContextRecord->Eax,
                    (unsigned long long)ep->ContextRecord->Ebx,
                    (unsigned long long)ep->ContextRecord->Ecx,
                    (unsigned long long)ep->ContextRecord->Edx,
                    (unsigned long long)ep->ContextRecord->Esi,
                    (unsigned long long)ep->ContextRecord->Edi);
        }
        // Resolve the faulting instruction against the PDB
        HANDLE proc = GetCurrentProcess();
        SymSetOptions(SYMOPT_UNDNAME | SYMOPT_LOAD_LINES);
        if (SymInitialize(proc, NULL, TRUE)) {
            SYMBOL_INFO* sym = (SYMBOL_INFO*)calloc(1, sizeof(SYMBOL_INFO) + 256);
            sym->MaxNameLen = 255;
            sym->SizeOfStruct = sizeof(SYMBOL_INFO);
            DWORD64 disp = 0;
            DWORD64 eip = (DWORD64)ep->ContextRecord->Eip;
            if (SymFromAddr(proc, eip, &disp, sym)) {
                fprintf(f, "FAULTING FUNCTION: %s+0x%llx (module base 0x%llX)\n",
                        sym->Name, (unsigned long long)disp,
                        (unsigned long long)sym->ModBase);
            } else {
                fprintf(f, "FAULTING FUNCTION: <no symbol for 0x%08llX>\n", (unsigned long long)eip);
            }
            free(sym);
        }
        write_stack(f);
        fclose(f);
    }
    return EXCEPTION_CONTINUE_SEARCH;
}

void crashlog_mark(const char* step)
{
    FILE* f = open_log();
    if (f) {
        fprintf(f, "[step] %s\n", step);
        fflush(f);
        fclose(f);
    }
}

void crashlog_install(void)
{
    FILE* f = open_log();
    if (f) {
        fprintf(f, "\n---- session start (pid %lu) ----\n", (unsigned long)GetCurrentProcessId());
        fclose(f);
    }
    _set_invalid_parameter_handler(on_invalid_parameter);
    _set_purecall_handler(on_purecall);
    signal(SIGABRT, on_sigabrt);
    AddVectoredExceptionHandler(1, on_unhandled);
    SetUnhandledExceptionFilter(on_unhandled);
}

// ---------------------------------------------------------------------------
// Hangs. A game stuck in a loop that never gets back to the main loop is not a
// crash, so nothing above sees it. Test mode beats crashlog_heartbeat() once a
// pass; a watcher thread that sees no beat for 5 s writes the main thread's
// stack to crash.log, and again every 5 s while it stays stuck, so a loop shows
// as the same callers under a moving EIP.
//
// The main thread is only suspended long enough to copy its registers and the
// top of its stack: suspended, it may hold the heap lock, so the symbol lookups
// run on the copy after it is resumed.

static HANDLE s_mainThread;
static volatile LONG s_beat;
static BYTE s_stack[64 * 1024];
static const ULONG kSymTagFunction = 5;   // SymTagEnum (cvconst.h), not in DbgHelp.h

static void report_hang(HANDLE proc, SYMBOL_INFO* sym, int seconds)
{
    CONTEXT ctx = {};
    ctx.ContextFlags = CONTEXT_CONTROL | CONTEXT_INTEGER;
    if (SuspendThread(s_mainThread) == (DWORD)-1) return;
    BOOL ok = GetThreadContext(s_mainThread, &ctx);
    DWORD len = 0;
    MEMORY_BASIC_INFORMATION mbi;
    if (ok && VirtualQuery((LPCVOID)(uintptr_t)ctx.Esp, &mbi, sizeof(mbi))) {
        DWORD left = (DWORD)((uintptr_t)mbi.BaseAddress + mbi.RegionSize - ctx.Esp);
        len = left < sizeof(s_stack) ? left : (DWORD)sizeof(s_stack);
        memcpy(s_stack, (const void*)(uintptr_t)ctx.Esp, len);
    }
    ResumeThread(s_mainThread);
    if (!ok) return;

    FILE* f = open_log();
    if (!f) return;
    fprintf(f, "\n==== HANG: no main-loop pass for %d s ====\n", seconds);
    fprintf(f, "EIP=%08lX ESP=%08lX EBP=%08lX\n", ctx.Eip, ctx.Esp, ctx.Ebp);
    write_frame(f, proc, sym, 0, ctx.Eip);

    // Tasks run on their own stacks and are entered with a jump, so there is
    // no frame chain to walk. Every word on the stack that points into the exe
    // and inside a function is a likely return address: the callers,
    // innermost first.
    fprintf(f, "  exe addresses on the stack:\n");
    const DWORD64 exe = (DWORD64)(uintptr_t)GetModuleHandleA(NULL);
    unsigned shown = 0;
    for (DWORD at = 0; at + 4 <= len && shown < 32; at += 4) {
        DWORD v = *(const DWORD*)(s_stack + at);
        DWORD64 disp = 0;
        if (SymGetModuleBase64(proc, v) != exe || !SymFromAddr(proc, v, &disp, sym) || sym->Tag != kSymTagFunction) continue;
        write_frame(f, proc, sym, shown++, v);
    }
    fclose(f);
}

static DWORD WINAPI watch_hangs(void*)
{
    // Its own handle, so its symbol session is not the crash handlers'.
    HANDLE proc = NULL;
    DuplicateHandle(GetCurrentProcess(), GetCurrentProcess(), GetCurrentProcess(), &proc, 0, FALSE,
                    DUPLICATE_SAME_ACCESS);
    SymSetOptions(SYMOPT_UNDNAME | SYMOPT_DEFERRED_LOADS);
    if (!proc || !SymInitialize(proc, NULL, TRUE)) return 0;
    SYMBOL_INFO* sym = (SYMBOL_INFO*)calloc(1, sizeof(SYMBOL_INFO) + 256);
    sym->MaxNameLen = 255;
    sym->SizeOfStruct = sizeof(SYMBOL_INFO);

    LONG seen = s_beat;
    int stuck = 0;
    for (;;) {
        Sleep(1000);
        const LONG beat = s_beat;
        if (beat != seen) {
            seen = beat;
            stuck = 0;
            continue;
        }
        if (++stuck % 5 == 0) report_hang(proc, sym, stuck);
    }
}

void crashlog_heartbeat(void)
{
    InterlockedIncrement(&s_beat);
}

void crashlog_watch_hangs(void)
{
    if (s_mainThread) return;
    s_mainThread = OpenThread(THREAD_SUSPEND_RESUME | THREAD_GET_CONTEXT | THREAD_QUERY_INFORMATION, FALSE,
                              GetCurrentThreadId());
    if (s_mainThread) CloseHandle(CreateThread(NULL, 0, watch_hangs, NULL, 0, NULL));
}
