#pragma once

#include "message_types.hpp"

#include <boost/asio.hpp>
#include <boost/beast.hpp>
#include <boost/beast/websocket.hpp>

#include <memory>
#include <string>
#include <unordered_map>

namespace nia {

namespace asio  = boost::asio;
namespace beast = boost::beast;
namespace ws    = beast::websocket;
using tcp       = asio::ip::tcp;

// ── Session forward-declaration ───────────────────────────────────────────────

class RelaySession;

// ── ClusterRelay ──────────────────────────────────────────────────────────────

/// WebSocket relay server — coordinates cluster nodes.
///
/// Mirrors Python ClusterRelay:
///   - Accepts WebSocket connections from ClusterNode instances.
///   - Handles register / heartbeat / message-forward protocol.
///   - Broadcasts the current node list after each registration change.
class ClusterRelay {
public:
    /// @param port         TCP port to listen on (default 4040).
    /// @param cluster_name Logical name of this cluster.
    ClusterRelay(uint16_t port, std::string cluster_name);

    /// Register a node session.  Called by RelaySession on receipt of a
    /// "register" message.
    void register_node(const std::string& node_name,
                       const NodeInfo& info,
                       std::shared_ptr<RelaySession> session);

    /// Unregister a node by name.  Called when its WebSocket closes.
    void unregister_node(const std::string& node_name);

    /// Broadcast the current node list to every connected session.
    void broadcast_node_list();

    /// Look up a live session by node name.  Returns nullptr if not found.
    std::shared_ptr<RelaySession> find_session(const std::string& node_name) const;

    /// Start the relay (blocks until the io_context stops).
    void start();

    /// Accessors
    uint16_t           port()         const { return port_; }
    const std::string& cluster_name() const { return cluster_name_; }

private:
    uint16_t    port_;
    std::string cluster_name_;

    asio::io_context ioc_;

    /// node_name → live session
    std::unordered_map<std::string, std::shared_ptr<RelaySession>> sessions_;
    /// node_name → metadata
    std::unordered_map<std::string, NodeInfo> node_info_;
};

// ── RelaySession ──────────────────────────────────────────────────────────────

/// Handles a single WebSocket connection on behalf of a ClusterRelay.
class RelaySession : public std::enable_shared_from_this<RelaySession> {
public:
    RelaySession(tcp::socket socket, ClusterRelay& relay);

    /// Begin the async read loop.
    void start();

    /// Send a JSON message asynchronously.
    void send(const nlohmann::json& msg);

private:
    void do_accept();
    void do_read();
    void on_read(beast::error_code ec, std::size_t bytes);
    void handle_message(const nlohmann::json& msg);

    ws::stream<tcp::socket> ws_;
    beast::flat_buffer      buffer_;
    ClusterRelay&           relay_;
    std::string             node_name_;
};

} // namespace nia
