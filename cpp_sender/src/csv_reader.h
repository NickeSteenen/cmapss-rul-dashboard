#pragma once

#include <map>
#include <string>
#include <vector>

// One row of the test data.
struct EngineRow {
    std::string source_dataset;            // "FD001" to "FD004", the only text column
    std::map<std::string, double> values;  // every other column by name, such as "unit", "cycle" and "sensor1"
};

// Reads the test data CSV and returns one engine's rows, sorted by cycle.
std::vector<EngineRow> read_engine_rows(const std::string& path, const std::string& dataset, int unit);
