#include "udp_sender.h"

#include <array>
#include <cstdint>
#include <cstring>
#include <stdexcept>
#include <string>

#include <ws2tcpip.h>

namespace {

std::string winsock_error(int code) {
    return " (Winsock error " + std::to_string(code) + ")";
}

}  // namespace

UdpSender::UdpSender(const std::string& host, int port) {
    WSADATA wsa;
    const int startup_result = WSAStartup(MAKEWORD(2, 2), &wsa);  // Winsock version 2.2
    if (startup_result != 0) {
        throw std::runtime_error("Could not start Winsock" + winsock_error(startup_result));  // WSAStartup returns the code itself
    }

    sock_ = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP);
    if (sock_ == INVALID_SOCKET) {
        const int code = WSAGetLastError();  // ask for the reason before cleaning up, which could replace it
        WSACleanup();
        throw std::runtime_error("Could not create a UDP socket" + winsock_error(code));
    }

    destination_.sin_family = AF_INET;
    destination_.sin_port = htons(static_cast<u_short>(port));
    if (inet_pton(AF_INET, host.c_str(), &destination_.sin_addr) != 1) {
        closesocket(sock_);
        WSACleanup();
        throw std::runtime_error("Invalid address: " + host);
    }
}

UdpSender::~UdpSender() {
    closesocket(sock_);
    WSACleanup();
}

void UdpSender::send(const Frame& frame) {
    std::array<uint8_t, 12> packet{};
    packet[0] = static_cast<uint8_t>(frame.id);
    packet[1] = static_cast<uint8_t>(frame.id >> 8);
    packet[2] = static_cast<uint8_t>(frame.id >> 16);
    packet[3] = static_cast<uint8_t>(frame.id >> 24);
    std::memcpy(packet.data() + 4, frame.data.data(), frame.data.size());

    const int sent = sendto(sock_, reinterpret_cast<const char*>(packet.data()), static_cast<int>(packet.size()), 0,
                            reinterpret_cast<const sockaddr*>(&destination_), sizeof(destination_));
    if (sent == SOCKET_ERROR) {  // a UDP packet is sent whole or not at all, so this is the only failure
        throw std::runtime_error("Could not send a UDP packet" + winsock_error(WSAGetLastError()));
    }
}
