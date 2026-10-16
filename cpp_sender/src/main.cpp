#include <chrono>
#include <cmath>
#include <cstdint>
#include <iostream>
#include <stdexcept>
#include <string>
#include <thread>
#include <vector>

#include "csv_reader.h"
#include "frames.h"
#include "udp_sender.h"

namespace {

const std::string HOST = "127.0.0.1";
const int PORT = 48000;  // must match PORT in python_listener/connection.py

struct Settings {
    std::string dataset = "FD001";
    int unit = 1;
    double delay = 0.5;                         // seconds between rows
    std::string data_path = DEFAULT_DATA_PATH;  // set in CMakeLists.txt
};

// Text -> whole number, but only if the WHOLE text is one. "5" works, "1.9" and "5x" don't.
int parse_whole_number(const std::string& name, const std::string& value) {
    const std::string error = name + " must be a whole number (got: " + value + ")";
    std::size_t used = 0;
    int number = 0;
    try {
        number = std::stoi(value, &used);
    } catch (const std::exception&) {
        throw std::runtime_error(error);
    }
    if (used != value.size()) {  // std::stoi stops early instead of failing, so "1.9" only used the "1"
        throw std::runtime_error(error);
    }
    return number;
}

// Text -> decimal number, but only if the WHOLE text is one. "0.5" works, "0.5s" doesn't.
double parse_number(const std::string& name, const std::string& value) {
    const std::string error = name + " must be a number (got: " + value + ")";
    std::size_t used = 0;
    double number = 0.0;
    try {
        number = std::stod(value, &used);
    } catch (const std::exception&) {
        throw std::runtime_error(error);
    }
    if (used != value.size()) {
        throw std::runtime_error(error);
    }
    return number;
}

// Reads settings from the command line, e.g.: cmapss_sender.exe --dataset FD002 --unit 5 --delay 0.2
Settings parse_settings(int argc, char* argv[]) {
    Settings settings;
    for (int i = 1; i < argc; i += 2) {  // argv[0] is the program itself, and after that the settings come in pairs of --name value
        const std::string name = argv[i];
        if (i + 1 >= argc) {
            throw std::runtime_error("Missing a value after " + name);
        }
        const std::string value = argv[i + 1];

        if (name == "--dataset") {
            if (value != "FD001" && value != "FD002" && value != "FD003" && value != "FD004") {
                throw std::runtime_error("--dataset must be FD001, FD002, FD003 or FD004 (got: " + value + ")");
            }
            settings.dataset = value;
        } else if (name == "--unit") {
            settings.unit = parse_whole_number(name, value);
            if (settings.unit < 1) {
                throw std::runtime_error("--unit must be 1 or more (got: " + value + ")");
            }
        } else if (name == "--delay") {
            settings.delay = parse_number(name, value);
            if (!std::isfinite(settings.delay) || settings.delay < 0) {  // std::stod accepts "nan" and "inf"
                throw std::runtime_error("--delay must be a number of seconds, 0 or more (got: " + value + ")");
            }
        } else if (name == "--data") {
            settings.data_path = value;
        } else {
            throw std::runtime_error("Unknown setting: " + name);
        }
    }
    return settings;
}

}  // namespace

int main(int argc, char* argv[]) {
    try {
        const Settings settings = parse_settings(argc, argv);

        const std::vector<EngineRow> rows = read_engine_rows(settings.data_path, settings.dataset, settings.unit);
        if (rows.empty()) {
            throw std::runtime_error("No rows for " + settings.dataset + " engine " + std::to_string(settings.unit));
        }

        UdpSender sender(HOST, PORT);
        std::cout << "Sending " << rows.size() << " rows of " << settings.dataset << " engine " << settings.unit
                  << " to " << HOST << ":" << PORT << "\n";

        for (std::size_t i = 0; i < rows.size(); ++i) {
            const auto counter = static_cast<uint8_t>(i % 16);
            for (const Frame& frame : build_frames(rows[i], counter)) {
                sender.send(frame);
            }
            std::cout << "  sent cycle " << rows[i].values.at("cycle") << "\n";
            std::this_thread::sleep_for(std::chrono::duration<double>(settings.delay));
        }
    } catch (const std::exception& e) {
        std::cerr << "Error: " << e.what() << "\n";
        return 1;
    }
    return 0;
}
