#include <iostream>
#include <string>

// for Windows
#include <winsock2.h>
#include <ws2tcpip.h>
#include <conio.h>

// #include <netdb.h> // for linux

#include <libssh2.h>
using namespace std;

static const char *raspIP = "10.109.70.209";
static const char *raspHostName = "ieeeRasp";
static const char *username = "user_ieee";
static const char *pass = "pass_ieee8333";

void printWinsockError(const char* func) {
    int err = WSAGetLastError();
    char* msgBuf = nullptr;
    FormatMessageA(
        FORMAT_MESSAGE_ALLOCATE_BUFFER | FORMAT_MESSAGE_FROM_SYSTEM | FORMAT_MESSAGE_IGNORE_INSERTS,
        nullptr, err, MAKELANGID(LANG_NEUTRAL, SUBLANG_DEFAULT),
        (LPSTR)&msgBuf, 0, nullptr);
    printf("%s failed: %d (%s)\n", func, err, msgBuf ? msgBuf : "unknown error");
    LocalFree(msgBuf);
}

int main() {
    WSADATA wsaData;
    int iResult;

    // Initialize Winsock
    iResult = WSAStartup(MAKEWORD(2,2), &wsaData);
    if (iResult != 0) {
        printf("WSAStartup failed: %d\n", iResult);
        return 1;
    }
    printf("WSAStartup succeeded!\n");

    // resolve "host" into an actual IP address
    struct addrinfo hints{};
    struct addrinfo *result;
    hints.ai_family = AF_INET;      // IPv4
    hints.ai_socktype = SOCK_STREAM; // TCP
    iResult = getaddrinfo(raspIP, "22", &hints, &result);
    if (iResult != 0) {
        printf("getaddrinfo failed: %d (%s)\n", iResult, gai_strerrorA(iResult));
        return 1;
    }

    SOCKET sock = socket(result->ai_family, result->ai_socktype, result->ai_protocol);
    if (sock == INVALID_SOCKET) {
        printWinsockError("socket");
        return 1;
    }
    printf("Sock created!\n");

    iResult = connect(sock, result->ai_addr, result->ai_addrlen);
    if (iResult != 0) {
        printWinsockError("connect");
        return 1;
    }

    // This could be a little finicky, so give it time between runs
    libssh2_init(0);
    LIBSSH2_SESSION* session = libssh2_session_init();
    if (!session) {
        printf("libssh2_session_init failed\n");
        return 1;
    }
    printf("Session Started!\n");

    int rc = libssh2_session_handshake(session, sock);
    if (rc != 0) {
        printf("handshake failed: %d\n", rc);
        return 1;
    }
    printf("Session handshake succeeded!\n");

    rc = libssh2_userauth_password(session, username, pass);
    if (rc != 0) {
        char* errmsg;
        int errlen;
        libssh2_session_last_error(session, &errmsg, &errlen, 0);
        printf("auth failed: %s\n", errmsg);
        return 1;
    }

    LIBSSH2_CHANNEL* channel = libssh2_channel_open_session(session);
    if (!channel) {
        printf("channel_open_session failed\n");
        return 1;
    }
    printf("Channel Opened!\n");

    // rc = libssh2_channel_exec(channel, "ls -la");
    // if (rc != 0) {
    //     printf("channel_exec failed: %d\n", rc);
    //     return 1;
    // }
    // printf("Channel command sent!\n");

    // char buf[4096];
    // ssize_t n;
    // while ((n = libssh2_channel_read(channel, buf, sizeof(buf))) > 0) {
    //     fwrite(buf, 1, n, stdout);
    // }

    // Pseudo channel for persistance
    rc = libssh2_channel_request_pty(channel, "xterm");
    if (rc != 0) {
        printf("request_pty failed: %d\n", rc);
        return 1;
    }

    rc = libssh2_channel_shell(channel);
    if (rc != 0) {
        printf("channel_shell failed: %d\n", rc);
        return 1;
    }
    printf("Interactive shell started!\n");

    libssh2_session_set_blocking(session, 0);

    char buf[4096];
    std::string inputLine;

    while (true) {
        ssize_t n = libssh2_channel_read(channel, buf, sizeof(buf));
        if (n > 0) {
            fwrite(buf, 1, n, stdout);
            fflush(stdout);
        } else if (n < 0 && n != LIBSSH2_ERROR_EAGAIN) {
            printf("read error: %zd\n", n);
            break;
        }

        if (libssh2_channel_eof(channel)) {
            printf("[remote shell closed]\n");
            break;
        }

        // This is kind of finicky I believe, but works fine for now until
        // I get started on multi-threading
        if (_kbhit()) {
            getline(cin, inputLine);
            string toSend = inputLine + "\n";
            libssh2_channel_write(channel, toSend.c_str(), toSend.size());
        }
    }

    // Clean Up
    libssh2_channel_close(channel);
    libssh2_channel_free(channel);

    libssh2_session_disconnect(session, "done");
    libssh2_session_free(session);

    closesocket(sock);
    WSACleanup();
    printf("Cleaned up\n");

    return 0;
}
