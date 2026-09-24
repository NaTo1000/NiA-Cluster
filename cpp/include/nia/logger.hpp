#pragma once

#include <memory>
#include <string>
#include <string_view>

// Forward-declare spdlog types so callers don't need to pull in spdlog headers.
namespace spdlog {
class logger;
}

namespace nia {

/// Initialise the global spdlog logger.
/// Call once at startup before any log calls.
///
/// @param name   Logger name shown in log output.
/// @param debug  When true, set the log level to debug; otherwise info.
void init_logger(std::string_view name, bool debug = false);

/// Return the shared spdlog logger created by init_logger().
/// Returns nullptr if init_logger() has not been called.
std::shared_ptr<spdlog::logger> get_logger();

/// Convenience helpers — delegate to get_logger().
/// They are no-ops when the logger has not been initialised.
void log_info (std::string_view msg);
void log_debug(std::string_view msg);
void log_warn (std::string_view msg);
void log_error(std::string_view msg);

} // namespace nia
