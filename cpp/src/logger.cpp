#include "nia/logger.hpp"

#include <spdlog/spdlog.h>
#include <spdlog/sinks/stdout_color_sinks.h>
#include <spdlog/sinks/basic_file_sink.h>

namespace nia {

static std::shared_ptr<spdlog::logger> g_logger;

void init_logger(std::string_view name, bool debug)
{
    auto console_sink = std::make_shared<spdlog::sinks::stdout_color_sink_mt>();
    console_sink->set_pattern("[%Y-%m-%d %H:%M:%S.%e] [%n] [%^%l%$] %v");

    g_logger = std::make_shared<spdlog::logger>(std::string(name),
                                                spdlog::sinks_init_list{console_sink});
    g_logger->set_level(debug ? spdlog::level::debug : spdlog::level::info);
    g_logger->flush_on(spdlog::level::warn);

    spdlog::register_logger(g_logger);
    spdlog::set_default_logger(g_logger);
}

std::shared_ptr<spdlog::logger> get_logger()
{
    return g_logger;
}

void log_info(std::string_view msg)
{
    if (g_logger) g_logger->info(msg);
}

void log_debug(std::string_view msg)
{
    if (g_logger) g_logger->debug(msg);
}

void log_warn(std::string_view msg)
{
    if (g_logger) g_logger->warn(msg);
}

void log_error(std::string_view msg)
{
    if (g_logger) g_logger->error(msg);
}

} // namespace nia
