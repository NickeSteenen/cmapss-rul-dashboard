#pragma once

#include <array>
#include <cstddef>
#include <cstdint>

#include "csv_reader.h"

// One CAN message, with its ID and its 8 data bytes.
struct Frame {
    uint32_t id;
    std::array<uint8_t, 8> data;
};

constexpr std::size_t FRAMES_PER_ROW = 6;

// Turns one row into its six CAN messages, all carrying the same counter.
std::array<Frame, FRAMES_PER_ROW> build_frames(const EngineRow& row, uint8_t counter);
