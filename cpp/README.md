# NiA-Cluster — C++ Port

C++ port of the NiA-Cluster relay/node system, mirroring the Python
`cluster_manager.py` interface. Uses Boost.Beast for WebSockets,
nlohmann/json for JSON, and spdlog for structured logging.

---

## Table of Contents

- [Prerequisites](#prerequisites)
- [Building on Windows (Visual Studio 2022)](#building-on-windows-visual-studio-2022)
- [Building on Linux / macOS](#building-on-linux--macos)
- [Running](#running)
- [Running Tests](#running-tests)
- [Project Layout](#project-layout)
- [CLI Reference](#cli-reference)

---

## Prerequisites

| Tool | Minimum Version | Notes |
|------|-----------------|-------|
| CMake | 3.20 | <https://cmake.org/download/> |
| C++ compiler | MSVC 2022 / GCC 11 / Clang 14 | C++17 required, C++20 preferred |
| Boost | 1.74 | Beast + ASIO for WebSocket support |
| vcpkg | latest | Windows dependency manager (recommended) |
| Ninja | any | Optional — used by non-VS generators |

### Installing Boost

**Windows (vcpkg — recommended):**
```powershell
git clone https://github.com/microsoft/vcpkg.git C:\vcpkg
C:\vcpkg\bootstrap-vcpkg.bat
C:\vcpkg\vcpkg install boost-beast boost-asio boost-system --triplet x64-windows
$env:VCPKG_ROOT = "C:\vcpkg"
```

**Linux (apt):**
```bash
sudo apt-get install libboost-dev libboost-system-dev
```

**macOS (Homebrew):**
```bash
brew install boost
```

All other dependencies (nlohmann/json, spdlog, GoogleTest) are fetched
automatically by CMake at configure time.

---

## Building on Windows (Visual Studio 2022)

### Option A — Open Folder in Visual Studio (easiest)

1. Open **Visual Studio 2022**.
2. Choose **Open a local folder** and select the `cpp/` directory.
3. Visual Studio detects `CMakeLists.txt` and `CMakePresets.json` automatically.
4. In the toolbar, select the `Windows MSVC Debug` or `Windows MSVC Release` preset.
5. Press **Ctrl+Shift+B** to build.

> **Tip:** Set `VCPKG_ROOT` as a system environment variable before opening VS so
> the toolchain file is resolved automatically.

### Option B — Command line (Developer PowerShell)

```powershell
cd cpp
cmake --preset windows-msvc-debug
cmake --build --preset windows-msvc-debug-build
```

The executable is placed in `build\msvc-debug\Debug\nia-cluster.exe`.

---

## Building on Linux / macOS

```bash
cd cpp

# Configure (Ninja generator, debug)
cmake --preset linux-gcc-debug     # Linux
# or
cmake --preset macos-clang-debug   # macOS

# Build
cmake --build --preset linux-debug-build

# The executable is at:
#   build/gcc-debug/nia-cluster
```

---

## Running

### Start the relay server

```bash
./nia-cluster --mode relay --cluster myfleet --relay-port 4040
```

### Start a node

```bash
./nia-cluster --mode node --cluster myfleet --node node1 \
  --relay-host localhost --relay-port 4040 --lan-port 5001 --enable-ble
```

### Enable debug logging

```bash
./nia-cluster --mode relay --cluster myfleet --debug
```

---

## Running Tests

```bash
# After building:
ctest --preset linux-debug-test          # Linux/macOS
ctest --preset windows-msvc-debug-test   # Windows

# Or run the test binary directly:
./build/gcc-debug/tests/nia-cluster-tests
```

---

## Project Layout

```
cpp/
├── CMakeLists.txt              # Root CMake build file
├── CMakePresets.json           # VS 2022 / GCC / Clang presets
├── README.md                   # This file
├── cmake/
│   └── FindDependencies.cmake  # Helper to find Boost / BLE libs
├── include/
│   └── nia/
│       ├── cluster_relay.hpp   # ClusterRelay class declaration
│       ├── cluster_node.hpp    # ClusterNode class declaration
│       ├── message_types.hpp   # Message enums, structs, JSON helpers
│       ├── config.hpp          # Default constants
│       └── logger.hpp          # Logging facade (wraps spdlog)
├── src/
│   ├── main.cpp                # CLI entry point
│   ├── cluster_relay.cpp       # Relay implementation
│   ├── cluster_node.cpp        # Node implementation
│   ├── message_types.cpp       # JSON serialisation helpers
│   └── logger.cpp              # Logger setup
└── tests/
    ├── CMakeLists.txt
    ├── test_main.cpp           # GoogleTest runner
    ├── test_cluster_relay.cpp  # Relay unit tests
    ├── test_cluster_node.cpp   # Node unit tests
    └── test_message_types.cpp  # Message parsing tests
```

---

## CLI Reference

Mirrors the Python `cluster_manager.py` interface exactly.

| Flag | Default | Description |
|------|---------|-------------|
| `--mode` | *(required)* | `relay` or `node` |
| `--cluster` | *(required)* | Cluster name |
| `--relay-port` | `4040` | Relay listen port (relay mode) / relay port to connect to (node mode) |
| `--node` | *(required in node mode)* | Node name |
| `--relay-host` | *(required in node mode)* | Relay server hostname or IP |
| `--lan-port` | *(required in node mode)* | Node LAN port |
| `--enable-ble` | `false` | Enable BLE support (node mode) |
| `--debug` | `false` | Enable debug-level logging |
