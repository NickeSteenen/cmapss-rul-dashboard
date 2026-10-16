#pragma once

#include <string>

#include <winsock2.h>

#include "frames.h"

// Sends CAN messages as UDP packets, each with 4 bytes ID (lowest byte first) and then the 8 data bytes.
// This is the only part of the program that knows about UDP, so it's what you'd replace to use real CAN hardware.
// Networking starts when a UdpSender is created, and is shut down again when it is destroyed.
class UdpSender {
public:
    UdpSender(const std::string& host, int port);
    ~UdpSender();

    UdpSender(const UdpSender&) = delete;  // no copies, because two copies would both try to close the same socket
    UdpSender& operator=(const UdpSender&) = delete;

    void send(const Frame& frame);

private:
    SOCKET sock_ = INVALID_SOCKET;
    sockaddr_in destination_{};
};
