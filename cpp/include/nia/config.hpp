#pragma once

#include <cstdint>
#include <string>

namespace nia {

/// Default relay server port (matches Python default)
inline constexpr uint16_t DEFAULT_RELAY_PORT = 4040;

/// Default heartbeat interval in seconds (matches Python 30 s sleep)
inline constexpr int DEFAULT_HEARTBEAT_INTERVAL_SEC = 30;

/// Default cluster name used when none is supplied
inline constexpr const char* DEFAULT_CLUSTER_NAME = "nia-cluster";

/// Default relay host for node mode
inline constexpr const char* DEFAULT_RELAY_HOST = "localhost";

/// Application name / version strings
inline constexpr const char* APP_NAME    = "NiA-Cluster";
inline constexpr const char* APP_VERSION = "1.0.0";

} // namespace nia
