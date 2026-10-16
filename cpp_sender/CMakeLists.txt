cmake_minimum_required(VERSION 3.20)
project(cmapss_sender LANGUAGES C CXX)  # C for the generated code, C++ for our own code

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

add_executable(cmapss_sender
    src/main.cpp
    src/csv_reader.cpp
    src/frames.cpp
    src/udp_sender.cpp
    generated/cmapss_engine.c  # written by protocol/generate_dbc.py from the DBC file
)

target_include_directories(cmapss_sender PRIVATE generated)

# Default location of the test data, so the program works no matter which folder it is started from.
get_filename_component(PROJECT_ROOT "${CMAKE_CURRENT_SOURCE_DIR}/.." ABSOLUTE)
target_compile_definitions(cmapss_sender PRIVATE DEFAULT_DATA_PATH="${PROJECT_ROOT}/data/combined_test_data.csv")

target_link_libraries(cmapss_sender PRIVATE ws2_32)  # Winsock
