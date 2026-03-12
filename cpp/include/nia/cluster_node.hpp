#pragma once

#include "message_types.hpp"

#include <boost/asio.hpp>
#include <boost/beast.hpp>
#include <boost/beast/websocket.hpp>

#include <atomic>
#include <string>
#include <thread>
#include <unordered_map>

namespace nia {

namespace asio  = boost::asio;
namespace beast = boost::beast;
namespace ws    = beast::websocket;
using tcp       = asio::ip::tcp;

/// WebSocket cluster node — connects to a ClusterRelay and participates in the
/// cluster.
///
/// Mirrors Python ClusterNode:
///   - Connects to the relay and sends a "register" message.
///   - Handles "node_list", "heartbeat_ack", "message", and "error" messages.
///   - Sends periodic heartbeats every DEFAULT_HEARTBEAT_INTERVAL_SEC seconds.
class ClusterNode {
public:
    /// @param cluster_name  Logical cluster to join.
    /// @param node_name     Unique name for this node within the cluster.
    /// @param relay_host    Hostname / IP of the relay server.
    /// @param relay_port    TCP port of the relay server.
    /// @param lan_port      LAN port this node exposes to peers.
    /// @param enable_ble    Enable BLE support (informational; forwarded to relay).
    ClusterNode(std::string cluster_name,
                std::string node_name,
                std::string relay_host,
                uint16_t    relay_port,
                int         lan_port,
                bool        enable_ble = false);

    ~ClusterNode();

    /// Establish the WebSocket connection and send the register message.
    /// Throws std::runtime_error on failure.
    void connect_to_relay();

    /// Blocking receive loop — returns when the connection is closed.
    void handle_messages();

    /// Send a heartbeat message; called periodically by the heartbeat thread.
    void send_heartbeat();

    /// Start the node: connect, then run message-handling and heartbeat
    /// concurrently (blocks until disconnected).
    void start();

    /// Accessors
    bool        connected()    const { return connected_; }
    const std::string& node_name()    const { return node_name_; }
    const std::string& cluster_name() const { return cluster_name_; }

    /// Peer nodes as received from the last node_list broadcast.
    const std::unordered_map<std::string, NodeInfo>& peer_nodes() const {
        return peer_nodes_;
    }

private:
    std::string cluster_name_;
    std::string node_name_;
    std::string relay_host_;
    uint16_t    relay_port_;
    int         lan_port_;
    bool        enable_ble_;

    asio::io_context                ioc_;
    ws::stream<tcp::socket>         ws_{ioc_};
    std::atomic<bool>               connected_{false};

    std::unordered_map<std::string, NodeInfo> peer_nodes_;

    std::thread heartbeat_thread_;
};

} // namespace nia
