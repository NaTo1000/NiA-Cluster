# FindDependencies.cmake
#
# Helper module called by the root CMakeLists.txt to locate optional
# system-level dependencies that are not fetched via FetchContent.
#
# Currently handles:
#   - Boost (Beast + ASIO) — required for WebSocket support
#   - BlueZ (Linux BLE)    — optional, enabled when ENABLE_BLE is ON

# ── Boost ─────────────────────────────────────────────────────────────────────

# Prefer config-mode packages (vcpkg, Conan, system installs) over the legacy
# FindBoost module shipped with older CMake versions.
set(Boost_USE_STATIC_LIBS        OFF)
set(Boost_USE_MULTITHREADED      ON)
set(Boost_USE_STATIC_RUNTIME     OFF)

find_package(Boost 1.74 QUIET CONFIG COMPONENTS system)
if(NOT Boost_FOUND)
    # Fall back to the CMake FindBoost module
    find_package(Boost 1.74 REQUIRED COMPONENTS system)
endif()

if(Boost_FOUND)
    message(STATUS "Found Boost ${Boost_VERSION} at ${Boost_INCLUDE_DIRS}")
else()
    message(FATAL_ERROR
        "Boost 1.74+ not found.\n"
        "  Windows : vcpkg install boost-beast boost-asio boost-system\n"
        "  Linux   : sudo apt-get install libboost-dev libboost-system-dev\n"
        "  macOS   : brew install boost"
    )
endif()

# ── BlueZ / BLE (Linux only, optional) ───────────────────────────────────────

option(ENABLE_BLE "Enable Bluetooth Low Energy (BLE) support (Linux only)" OFF)

if(ENABLE_BLE)
    if(NOT UNIX OR APPLE)
        message(WARNING "BLE support via BlueZ is only available on Linux. "
                        "ENABLE_BLE will be ignored on this platform.")
    else()
        find_package(PkgConfig QUIET)
        if(PkgConfig_FOUND)
            pkg_check_modules(BLUEZ bluez)
            if(BLUEZ_FOUND)
                message(STATUS "Found BlueZ ${BLUEZ_VERSION} — BLE support enabled")
                add_compile_definitions(NIA_BLE_ENABLED)
                # Callers should link against ${BLUEZ_LIBRARIES} and add
                # ${BLUEZ_INCLUDE_DIRS} to their include paths.
            else()
                message(WARNING "BlueZ not found; BLE support disabled. "
                                "Install via: sudo apt-get install libbluetooth-dev")
            endif()
        else()
            message(WARNING "pkg-config not found; cannot detect BlueZ.")
        endif()
    endif()
endif()
