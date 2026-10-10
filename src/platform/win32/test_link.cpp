// test_link.cpp - Windows side of the test link (port addition, test tooling).
//
// A single localhost TCP client. The game polls once per frame, so everything
// here is non-blocking except send, which is small and local.
#include "../platform.h"

#include <winsock2.h>
#include <string.h>

#pragma comment(lib, "ws2_32.lib")

static SOCKET s_listen = INVALID_SOCKET;
static SOCKET s_client = INVALID_SOCKET;
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

void plat_test_link_poll(void (*on_line)(const char* line))
{
    if (s_listen == INVALID_SOCKET) return;

    if (s_client == INVALID_SOCKET) {
        s_client = accept(s_listen, NULL, NULL);
        if (s_client == INVALID_SOCKET) return;
        u_long nonblocking = 1;
        ioctlsocket(s_client, FIONBIO, &nonblocking);
    }

    for (;;) {
        int room = (int)sizeof(s_inbuf) - 1 - s_inlen;
        if (room <= 0) {
            // A line longer than the buffer is not a valid command; drop it.
            s_inlen = 0;
            room = (int)sizeof(s_inbuf) - 1;
        }
        int got = recv(s_client, s_inbuf + s_inlen, room, 0);
        if (got == 0) {
            drop_client();
            return;
        }
        if (got < 0) {
            if (WSAGetLastError() != WSAEWOULDBLOCK) drop_client();
            break;
        }
        s_inlen += got;
    }

    int start = 0;
    for (int i = 0; i < s_inlen; i++) {
        if (s_inbuf[i] != '\n') continue;
        int end = i;
        if (end > start && s_inbuf[end - 1] == '\r') end--;
        s_inbuf[end] = '\0';
        on_line(s_inbuf + start);
        start = i + 1;
    }
    memmove(s_inbuf, s_inbuf + start, (size_t)(s_inlen - start));
    s_inlen -= start;
}

void plat_test_link_send(const char* text)
{
    if (s_client == INVALID_SOCKET) return;
    int len = (int)strlen(text);
    while (len > 0) {
        int sent = send(s_client, text, len, 0);
        if (sent > 0) {
            text += sent;
            len -= sent;
        } else if (WSAGetLastError() == WSAEWOULDBLOCK) {
            Sleep(1);
        } else {
            drop_client();
            return;
        }
    }
}
