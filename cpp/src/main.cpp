#include "nia/cluster_node.hpp"
#include "nia/cluster_relay.hpp"
#include "nia/config.hpp"
#include "nia/logger.hpp"

#include <iostream>
#include <stdexcept>
#include <string>

// ── Minimal CLI parser ─────────────────────────────────────────────────────────
// Intentionally avoids external dependencies (Boost.Program_options, CLI11, etc.)
// to keep the build simple.  Mirrors the Python argparse interface exactly.

struct Args {
    std::string mode;
    std::string cluster = nia::DEFAULT_CLUSTER_NAME;
    uint16_t    relay_port = nia::DEFAULT_RELAY_PORT;
    std::string node;
    std::string relay_host = nia::DEFAULT_RELAY_HOST;
    int         lan_port   = 0;
    bool        enable_ble = false;
    bool        debug      = false;
};

static void print_usage(const char* prog)
{
    std::cerr
        << "Usage: " << prog << " --mode <relay|node> --cluster <name> [options]\n"
        << "\n"
        << "Common options:\n"
        << "  --mode <relay|node>     Operation mode (required)\n"
        << "  --cluster <name>        Cluster name (required)\n"
        << "  --relay-port <port>     Relay server port (default: "
              << nia::DEFAULT_RELAY_PORT << ")\n"
        << "  --debug                 Enable debug logging\n"
        << "\n"
        << "Node mode options:\n"
        << "  --node <name>           Node name (required)\n"
        << "  --relay-host <host>     Relay server host (required)\n"
        << "  --lan-port <port>       Node LAN port (required)\n"
        << "  --enable-ble            Enable BLE support\n";
}

static Args parse_args(int argc, char** argv)
{
    Args args;

    for (int i = 1; i < argc; ++i) {
        std::string key = argv[i];

        auto next = [&]() -> std::string {
            if (i + 1 >= argc)
                throw std::invalid_argument("Missing value for " + key);
            return argv[++i];
        };

        if      (key == "--mode")       args.mode       = next();
        else if (key == "--cluster")    args.cluster    = next();
        else if (key == "--relay-port") args.relay_port = static_cast<uint16_t>(std::stoi(next()));
        else if (key == "--node")       args.node       = next();
        else if (key == "--relay-host") args.relay_host = next();
        else if (key == "--lan-port")   args.lan_port   = std::stoi(next());
        else if (key == "--enable-ble") args.enable_ble = true;
        else if (key == "--debug")      args.debug      = true;
        else if (key == "--help" || key == "-h") {
            print_usage(argv[0]);
            std::exit(0);
        }
        else {
            throw std::invalid_argument("Unknown option: " + key);
        }
    }

    // Validate required args
    if (args.mode.empty())
        throw std::invalid_argument("--mode is required (relay or node)");
    if (args.mode != "relay" && args.mode != "node")
        throw std::invalid_argument("--mode must be 'relay' or 'node'");
    if (args.cluster.empty())
        throw std::invalid_argument("--cluster is required");

    if (args.mode == "node") {
        if (args.node.empty())
            throw std::invalid_argument("--node is required in node mode");
        if (args.relay_host.empty())
            throw std::invalid_argument("--relay-host is required in node mode");
        if (args.lan_port == 0)
            throw std::invalid_argument("--lan-port is required in node mode");
    }

    return args;
}

// ── main ───────────────────────────────────────────────────────────────────────

int main(int argc, char** argv)
{
    Args args;
    try {
        args = parse_args(argc, argv);
    } catch (const std::invalid_argument& ex) {
        std::cerr << "Error: " << ex.what() << "\n\n";
        print_usage(argv[0]);
        return 1;
    }

    // Initialise the logger
    nia::init_logger(nia::APP_NAME, args.debug);

    try {
        if (args.mode == "relay") {
            nia::ClusterRelay relay(args.relay_port, args.cluster);
            relay.start();

        } else {
            nia::ClusterNode node(
                args.cluster,
                args.node,
                args.relay_host,
                args.relay_port,
                args.lan_port,
                args.enable_ble
            );
            node.start();
        }
    } catch (const std::exception& ex) {
        nia::log_error("Fatal: " + std::string(ex.what()));
        return 1;
    }

    return 0;
}
