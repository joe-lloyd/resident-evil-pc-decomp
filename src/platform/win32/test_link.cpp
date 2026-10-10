// test_link.cpp - Windows side of the test link (port addition, test tooling).
//
// A single localhost TCP client. The game polls once per frame, so everything
// here is non-blocking; a send that cannot finish within kSendTimeoutMs drops
// the client rather than freezing the game.
#include "../platform.h"

#include <winsock2.h>
#include <string.h>

#pragma comment(lib, "ws2_32.lib")

static const DWORD kSendTimeoutMs = 2000;

static SOCKET s_listen = INVALID_SOCKET;
static SOCKET s_client = INVALID_SOCKET;
static int    s_clientId = 0;     // bumped for every accepted client
static char   s_inbuf[4096];
static int    s_inlen = 0;

static void drop_client(void)
{
    if (s_client != INVALID_SOCKET) closesocket(s_client);
    s_client = INVALID_SOCKET;
    s_inlen = 0;
}

BOOL plat_test_link_open(int port)
{
    if (port <= 0 || port > 65535) return FALSE;
    WSADATA wsa;
    if (WSAStartup(MAKEWORD(2, 2), &wsa) != 0) return FALSE;

    s_listen = socket(AF_INET, SOCK_STREAM, IPPROTO_TCP);
    if (s_listen == INVALID_SOCKET) return FALSE;

    sockaddr_in addr = {};
    addr.sin_family = AF_INET;
    addr.sin_addr.s_addr = htonl(INADDR_LOOPBACK);
    addr.sin_port = htons((u_short)port);
    u_long nonblocking = 1;
    if (bind(s_listen, (sockaddr*)&addr, sizeof(addr)) != 0 ||
        listen(s_listen, 1) != 0 ||
        ioctlsocket(s_listen, FIONBIO, &nonblocking) != 0) {
        closesocket(s_listen);
        s_listen = INVALID_SOCKET;
        return FALSE;
    }
    return TRUE;
}

int plat_test_link_client_id(void)
{
    return s_clientId;
}

// Hand every complete line in s_inbuf to on_line. Lines are copied out first:
// on_line may reply, and a failed reply drops the client and empties s_inbuf.
static void deliver_lines(void (*on_line)(const char* line))
{
    for (;;) {
        char* nl = (char*)memchr(s_inbuf, '\n', (size_t)s_inlen);
        if (nl == NULL) return;
        int len = (int)(nl - s_inbuf);
        char line[sizeof(s_inbuf)];
        memcpy(line, s_inbuf, (size_t)len);
        if (len > 0 && line[len - 1] == '\r') len--;
        line[len] = '\0';
        int consumed = (int)(nl - s_inbuf) + 1;
        memmove(s_inbuf, s_inbuf + consumed, (size_t)(s_inlen - consumed));
        s_inlen -= consumed;
        on_line(line);
        if (s_client == INVALID_SOCKET) return;
    }
}

void plat_test_link_poll(void (*on_line)(const char* line))
{
    if (s_listen == INVALID_SOCKET) return;

    // The newest connection wins, so a harness that reconnects is never stuck
    // behind a stale client the game still thinks is alive.
    SOCKET incoming = accept(s_listen, NULL, NULL);
    if (incoming != INVALID_SOCKET) {
        drop_client();
        s_client = incoming;
        s_clientId++;
        u_long nonblocking = 1;
        ioctlsocket(s_client, FIONBIO, &nonblocking);
    }

    while (s_client != INVALID_SOCKET) {
        int room = (int)sizeof(s_inbuf) - s_inlen;
        if (room == 0) {
            // A full buffer with no newline is not a valid command; drop it.
            s_inlen = 0;
            room = (int)sizeof(s_inbuf);
        }
        int got = recv(s_client, s_inbuf + s_inlen, room, 0);
        if (got > 0) {
            s_inlen += got;
            deliver_lines(on_line);
            continue;
        }
        if (got < 0 && WSAGetLastError() == WSAEWOULDBLOCK) return;
        // Closed (0) or failed: lines already delivered stand, the rest goes.
        drop_client();
        return;
    }
}

void plat_test_link_send(const char* text)
{
    if (s_client == INVALID_SOCKET) return;
    int len = (int)strlen(text);
    DWORD started = GetTickCount();
    while (len > 0) {
        int sent = send(s_client, text, len, 0);
        if (sent > 0) {
            text += sent;
            len -= sent;
        } else if (WSAGetLastError() == WSAEWOULDBLOCK && GetTickCount() - started < kSendTimeoutMs) {
            Sleep(1);
        } else {
            drop_client();
            return;
        }
    }
}
