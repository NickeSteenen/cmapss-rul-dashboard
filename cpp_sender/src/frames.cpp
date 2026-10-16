#include "frames.h"

#include <stdexcept>
#include <string>

#include "cmapss_engine.h"  // generated from the DBC file

namespace {

// "FD001" -> 0 ... "FD004" -> 3, using the numbers from the DBC file's value table.
uint8_t dataset_number(const std::string& name) {
    if (name == "FD001") return CMAPSS_ENGINE_ENGINE_INFO_SOURCE_DATASET_FD001_CHOICE;
    if (name == "FD002") return CMAPSS_ENGINE_ENGINE_INFO_SOURCE_DATASET_FD002_CHOICE;
    if (name == "FD003") return CMAPSS_ENGINE_ENGINE_INFO_SOURCE_DATASET_FD003_CHOICE;
    if (name == "FD004") return CMAPSS_ENGINE_ENGINE_INFO_SOURCE_DATASET_FD004_CHOICE;
    throw std::runtime_error("Unknown dataset: " + name);
}

}  // namespace

std::array<Frame, FRAMES_PER_ROW> build_frames(const EngineRow& row, uint8_t counter) {
    const auto& v = row.values;
    std::array<Frame, FRAMES_PER_ROW> frames{};

    // 0x100 ENGINE_INFO: which engine and flight this is, and the flight conditions
    cmapss_engine_engine_info_t info{};
    info.counter = counter;  // already a raw 0-15 value, so no encode function
    info.source_dataset = dataset_number(row.source_dataset);
    info.unit = cmapss_engine_engine_info_unit_encode(v.at("unit"));
    info.cycle = cmapss_engine_engine_info_cycle_encode(v.at("cycle"));
    info.setting1 = cmapss_engine_engine_info_setting1_encode(v.at("setting1"));
    info.setting2 = cmapss_engine_engine_info_setting2_encode(v.at("setting2"));
    info.setting3 = cmapss_engine_engine_info_setting3_encode(v.at("setting3"));
    frames[0].id = CMAPSS_ENGINE_ENGINE_INFO_FRAME_ID;
    cmapss_engine_engine_info_pack(frames[0].data.data(), &info, frames[0].data.size());

    // 0x101 SENSORS_1: sensor1-4
    cmapss_engine_sensors_1_t s1{};
    s1.counter = counter;
    s1.sensor1 = cmapss_engine_sensors_1_sensor1_encode(v.at("sensor1"));
    s1.sensor2 = cmapss_engine_sensors_1_sensor2_encode(v.at("sensor2"));
    s1.sensor3 = cmapss_engine_sensors_1_sensor3_encode(v.at("sensor3"));
    s1.sensor4 = cmapss_engine_sensors_1_sensor4_encode(v.at("sensor4"));
    frames[1].id = CMAPSS_ENGINE_SENSORS_1_FRAME_ID;
    cmapss_engine_sensors_1_pack(frames[1].data.data(), &s1, frames[1].data.size());

    // 0x102 SENSORS_2: sensor5-8
    cmapss_engine_sensors_2_t s2{};
    s2.counter = counter;
    s2.sensor5 = cmapss_engine_sensors_2_sensor5_encode(v.at("sensor5"));
    s2.sensor6 = cmapss_engine_sensors_2_sensor6_encode(v.at("sensor6"));
    s2.sensor7 = cmapss_engine_sensors_2_sensor7_encode(v.at("sensor7"));
    s2.sensor8 = cmapss_engine_sensors_2_sensor8_encode(v.at("sensor8"));
    frames[2].id = CMAPSS_ENGINE_SENSORS_2_FRAME_ID;
    cmapss_engine_sensors_2_pack(frames[2].data.data(), &s2, frames[2].data.size());

    // 0x103 SENSORS_3: sensor9-12
    cmapss_engine_sensors_3_t s3{};
    s3.counter = counter;
    s3.sensor9 = cmapss_engine_sensors_3_sensor9_encode(v.at("sensor9"));
    s3.sensor10 = cmapss_engine_sensors_3_sensor10_encode(v.at("sensor10"));
    s3.sensor11 = cmapss_engine_sensors_3_sensor11_encode(v.at("sensor11"));
    s3.sensor12 = cmapss_engine_sensors_3_sensor12_encode(v.at("sensor12"));
    frames[3].id = CMAPSS_ENGINE_SENSORS_3_FRAME_ID;
    cmapss_engine_sensors_3_pack(frames[3].data.data(), &s3, frames[3].data.size());

    // 0x104 SENSORS_4: sensor13-17
    cmapss_engine_sensors_4_t s4{};
    s4.counter = counter;
    s4.sensor13 = cmapss_engine_sensors_4_sensor13_encode(v.at("sensor13"));
    s4.sensor14 = cmapss_engine_sensors_4_sensor14_encode(v.at("sensor14"));
    s4.sensor15 = cmapss_engine_sensors_4_sensor15_encode(v.at("sensor15"));
    s4.sensor16 = cmapss_engine_sensors_4_sensor16_encode(v.at("sensor16"));
    s4.sensor17 = cmapss_engine_sensors_4_sensor17_encode(v.at("sensor17"));
    frames[4].id = CMAPSS_ENGINE_SENSORS_4_FRAME_ID;
    cmapss_engine_sensors_4_pack(frames[4].data.data(), &s4, frames[4].data.size());

    // 0x105 SENSORS_5: sensor18-21
    cmapss_engine_sensors_5_t s5{};
    s5.counter = counter;
    s5.sensor18 = cmapss_engine_sensors_5_sensor18_encode(v.at("sensor18"));
    s5.sensor19 = cmapss_engine_sensors_5_sensor19_encode(v.at("sensor19"));
    s5.sensor20 = cmapss_engine_sensors_5_sensor20_encode(v.at("sensor20"));
    s5.sensor21 = cmapss_engine_sensors_5_sensor21_encode(v.at("sensor21"));
    frames[5].id = CMAPSS_ENGINE_SENSORS_5_FRAME_ID;
    cmapss_engine_sensors_5_pack(frames[5].data.data(), &s5, frames[5].data.size());

    return frames;
}
