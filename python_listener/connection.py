import struct

# The C++ sender has its own copy of these in main.cpp and udp_sender.cpp
HOST = "127.0.0.1"
PORT = 48000

PACKET_FORMAT = "<I8s"  # a little-endian 4-byte unsigned ID, then the 8 data bytes
PACKET_SIZE = struct.calcsize(PACKET_FORMAT)


def make_packet(frame_id, data):
    return struct.pack(PACKET_FORMAT, frame_id, data)


def split_packet(packet):
    if len(packet) != PACKET_SIZE:
        return None
    return struct.unpack(PACKET_FORMAT, packet)
