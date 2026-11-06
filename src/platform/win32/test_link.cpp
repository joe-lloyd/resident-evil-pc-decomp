// test_link.cpp - Windows side of the test link (port addition, test tooling).
//
// A single localhost TCP client. The game polls once per frame, so everything
// here is non-blocking. What the socket cannot take now waits in s_out and
// goes on later frames: a client that is slow to read (a harness busy
// planning a route, behind an ssh tunnel) used to have a send stall past two
// seconds, and the game dropped it, which looked like the game hanging. The
// client is dropped only when s_out fills or nothing moves for kStuckMs.
#include "../platform.h"

#include <winsock2.h>
#include <string.h>

#pragma comment(lib, "ws2_32.lib")

static const DWORD kStuckMs = 30000;

static SOCKET s_listen = INVALID_SOCKET;
static SOCKET s_client = INVALID_SOCKET;
static int    s_clientId = 0;     // bumped for every accepted client
static char   s_inbuf[4096];
static int    s_inlen = 0;
static char   s_out[256 * 1024];
static int    s_outLen = 0;
static DWORD  s_outSince = 0;     // when s_out last emptied or moved

static void flush_out(void);

static void drop_client(void)
{
    if (s_client != INVALID_SOCKET) closesocket(s_client);
    s_client = INVALID_SOCKET;
    s_inlen = 0;
    s_outLen = 0;
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
    flush_out();

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

// Send what the socket takes of s_out now; drop the client on an error, or
// when nothing has gone for kStuckMs.
static void flush_out(void)
{
    while (s_client != INVALID_SOCKET && s_outLen > 0) {
        int sent = send(s_client, s_out, s_outLen, 0);
        if (sent > 0) {
            memmove(s_out, s_out + sent, (size_t)(s_outLen - sent));
            s_outLen -= sent;
            s_outSince = GetTickCount();
            continue;
        }
        if (WSAGetLastError() != WSAEWOULDBLOCK || GetTickCount() - s_outSince > kStuckMs) drop_client();
        return;
    }
}

void plat_test_link_send(const char* text)
{
    if (s_client == INVALID_SOCKET) return;
    int len = (int)strlen(text);
    if (s_outLen == 0) s_outSince = GetTickCount();
    if (s_outLen + len > (int)sizeof(s_out)) {
        drop_client();
        return;
    }
    memcpy(s_out + s_outLen, text, (size_t)len);
    s_outLen += len;
    flush_out();
}

int plat_test_link_pending(void)
{
    return s_client == INVALID_SOCKET ? 0 : s_outLen;
}
