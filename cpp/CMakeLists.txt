cmake_minimum_required(VERSION 3.20)
project(NiA-Cluster VERSION 1.0.0 LANGUAGES CXX)

# Require C++17, prefer C++20
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# Check for C++20 support
include(CheckCXXCompilerFlag)
check_cxx_compiler_flag("-std=c++20" COMPILER_SUPPORTS_CXX20)
if(COMPILER_SUPPORTS_CXX20)
    set(CMAKE_CXX_STANDARD 20)
    message(STATUS "Using C++20")
else()
    message(STATUS "Falling back to C++17")
endif()

# Windows/MSVC-specific flags for Visual Studio compatibility
if(MSVC)
    add_compile_options(
        /W4             # Warning level 4
        /WX-            # Warnings not as errors (to stay compatible with third-party headers)
        /MP             # Multi-processor compilation
        /utf-8          # UTF-8 source and execution character sets
        /Zc:__cplusplus # Correct __cplusplus macro
    )
    add_compile_definitions(
        _WIN32_WINNT=0x0A00   # Windows 10+
        WIN32_LEAN_AND_MEAN
        NOMINMAX
        _CRT_SECURE_NO_WARNINGS
    )
else()
    add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# CMake module path
list(APPEND CMAKE_MODULE_PATH "${CMAKE_CURRENT_SOURCE_DIR}/cmake")

# ── Dependencies ────────────────────────────────────────────────────────────────
include(FetchContent)

# nlohmann/json
FetchContent_Declare(
    nlohmann_json
    GIT_REPOSITORY https://github.com/nlohmann/json.git
    GIT_TAG        v3.11.3
    GIT_SHALLOW    TRUE
)
FetchContent_MakeAvailable(nlohmann_json)

# spdlog
FetchContent_Declare(
    spdlog
    GIT_REPOSITORY https://github.com/gabime/spdlog.git
    GIT_TAG        v1.14.1
    GIT_SHALLOW    TRUE
)
FetchContent_MakeAvailable(spdlog)

# Boost (Beast + ASIO for WebSocket support)
# On Windows with Visual Studio, users are encouraged to install Boost via vcpkg:
#   vcpkg install boost-beast boost-asio boost-system
# On Linux: sudo apt-get install libboost-dev libboost-system-dev
find_package(Boost 1.74 REQUIRED COMPONENTS system)
if(NOT Boost_FOUND)
    message(FATAL_ERROR
        "Boost not found. Install via vcpkg (Windows) or your system package manager:\n"
        "  Windows: vcpkg install boost-beast boost-asio boost-system\n"
        "  Linux:   sudo apt-get install libboost-dev libboost-system-dev\n"
        "  macOS:   brew install boost"
    )
endif()

# GoogleTest (for tests only)
FetchContent_Declare(
    googletest
    GIT_REPOSITORY https://github.com/google/googletest.git
    GIT_TAG        v1.14.0
    GIT_SHALLOW    TRUE
)
# Keep gtest from overriding parent project compiler/linker settings on Windows
set(gtest_force_shared_crt ON CACHE BOOL "" FORCE)
FetchContent_MakeAvailable(googletest)

# ── Main library (compiled once, shared between executable and tests) ────────────
add_library(nia-cluster-lib STATIC
    src/cluster_relay.cpp
    src/cluster_node.cpp
    src/message_types.cpp
    src/logger.cpp
)

target_include_directories(nia-cluster-lib PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}/include
    ${Boost_INCLUDE_DIRS}
)

target_link_libraries(nia-cluster-lib PUBLIC
    nlohmann_json::nlohmann_json
    spdlog::spdlog
    ${Boost_LIBRARIES}
)

if(WIN32)
    target_link_libraries(nia-cluster-lib PUBLIC ws2_32 wsock32)
endif()

# ── Executable ──────────────────────────────────────────────────────────────────
add_executable(nia-cluster src/main.cpp)
target_link_libraries(nia-cluster PRIVATE nia-cluster-lib)

# ── Tests ───────────────────────────────────────────────────────────────────────
enable_testing()
add_subdirectory(tests)

# ── Install rules ───────────────────────────────────────────────────────────────
include(GNUInstallDirs)
install(TARGETS nia-cluster
    RUNTIME DESTINATION ${CMAKE_INSTALL_BINDIR}
)
install(DIRECTORY include/nia
    DESTINATION ${CMAKE_INSTALL_INCLUDEDIR}
)
