#include <iostream>

// for Windows
#include <winsock2.h>
#include <ws2tcpip.h>

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
    printf("WSAStartup succeeded!");

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

    iResult = connect(sock, result->ai_addr, result->ai_addrlen);
    if (iResult != 0) {
        printWinsockError("connect");
        return 1;
    }

    return 0;
}
