#include "csv_reader.h"

#include <algorithm>
#include <fstream>
#include <sstream>
#include <stdexcept>

namespace {

std::vector<std::string> split_line(const std::string& line) {
    std::vector<std::string> fields;
    std::stringstream stream(line);
    std::string field;
    while (std::getline(stream, field, ',')) {
        fields.push_back(field);
    }
    return fields;
}

size_t column_index(const std::vector<std::string>& columns, const std::string& name) {
    auto it = std::find(columns.begin(), columns.end(), name);
    if (it == columns.end()) {
        throw std::runtime_error("The CSV has no column called " + name);
    }
    return static_cast<size_t>(it - columns.begin());
}

std::vector<std::string> required_columns() {
    std::vector<std::string> names = {"source_dataset", "unit", "cycle", "setting1", "setting2", "setting3"};
    for (int i = 1; i <= 21; ++i) {
        names.push_back("sensor" + std::to_string(i));
    }
    return names;
}

void check_required_columns(const std::vector<std::string>& columns) {
    for (const std::string& name : required_columns()) {
        if (std::find(columns.begin(), columns.end(), name) == columns.end()) {
            throw std::runtime_error("The CSV has no column called " + name);
        }
    }
}

}  // namespace

std::vector<EngineRow> read_engine_rows(const std::string& path, const std::string& dataset, int unit) {
    std::ifstream file(path);
    if (!file) {
        throw std::runtime_error("Could not open " + path);
    }

    std::string line;
    if (!std::getline(file, line)) {
        throw std::runtime_error("Could not read the header of " + path);
    }
    const std::vector<std::string> columns = split_line(line);
    check_required_columns(columns);
    const size_t dataset_col = column_index(columns, "source_dataset");
    const size_t unit_col = column_index(columns, "unit");

    std::vector<EngineRow> rows;
    while (std::getline(file, line)) {
        const std::vector<std::string> fields = split_line(line);
        if (fields.size() != columns.size()) {
            throw std::runtime_error("A row has " + std::to_string(fields.size()) + " values, but the header has " +
                                     std::to_string(columns.size()));
        }

        if (fields[dataset_col] != dataset || std::stoi(fields[unit_col]) != unit) {
            continue;  // skip other engines before converting all their values
        }

        EngineRow row;
        for (size_t i = 0; i < columns.size(); ++i) {
            if (i == dataset_col) {
                row.source_dataset = fields[i];
            } else {
                row.values[columns[i]] = std::stod(fields[i]);
            }
        }
        rows.push_back(row);
    }

    std::sort(rows.begin(), rows.end(), [](const EngineRow& a, const EngineRow& b) {
        return a.values.at("cycle") < b.values.at("cycle");
    });
    return rows;
}
