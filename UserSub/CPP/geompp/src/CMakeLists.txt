cmake_minimum_required(VERSION 3.16)
project(geompp VERSION 1.0.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Header-only interface library
add_library(geompp INTERFACE)
target_include_directories(geompp INTERFACE ${CMAKE_CURRENT_SOURCE_DIR})

# Minimal smoke-test executable
add_executable(geompp_test main.cpp)
target_link_libraries(geompp_test PRIVATE geompp)
