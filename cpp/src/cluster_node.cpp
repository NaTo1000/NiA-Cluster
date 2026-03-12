#include "nia/cluster_node.hpp"
#include "nia/config.hpp"
#include "nia/logger.hpp"
#include "nia/message_types.hpp"

#include <boost/asio/connect.hpp>

#include <chrono>
#include <stdexcept>
#include <thread>

namespace nia {

// ── ClusterNode ───────────────────────────────────────────────────────────────

ClusterNode::ClusterNode(std::string cluster_name,
                         std::string node_name,
                         std::string relay_host,
                         uint16_t    relay_port,
                         int         lan_port,
                         bool        enable_ble)
    : cluster_name_(std::move(cluster_name))
    , node_name_(std::move(node_name))
    , relay_host_(std::move(relay_host))
    , relay_port_(relay_port)
    , lan_port_(lan_port)
    , enable_ble_(enable_ble)
{}

ClusterNode::~ClusterNode()
{
    connected_ = false;
    if (heartbeat_thread_.joinable())
        heartbeat_thread_.join();
}

void ClusterNode::connect_to_relay()
{
    std::string relay_url = "ws://" + relay_host_ + ":" + std::to_string(relay_port_);
    log_info("Connecting to relay at " + relay_url);

    tcp::resolver resolver(ioc_);
    auto const results = resolver.resolve(relay_host_, std::to_string(relay_port_));

    beast::error_code ec;
    asio::connect(ws_.next_layer(), results, ec);
    if (ec)
        throw std::runtime_error("Failed to connect to relay: " + ec.message());

    ws_.handshake(relay_host_, "/", ec);
    if (ec)
        throw std::runtime_error("WebSocket handshake failed: " + ec.message());

    connected_ = true;
    log_info("Node '" + node_name_ + "' connected to relay");

    // Send registration message
    RegisterMessage reg;
    reg.node_name   = node_name_;
    reg.cluster     = cluster_name_;
    reg.lan_port    = lan_port_;
    reg.ble_enabled = enable_ble_;

    ws_.text(true);
    ws_.write(asio::buffer(reg.to_json().dump()), ec);
    if (ec)
        throw std::runtime_error("Failed to send register: " + ec.message());

    // Wait for registered acknowledgement
    beast::flat_buffer buf;
    ws_.read(buf, ec);
    if (ec)
        throw std::runtime_error("Failed to read registered ack: " + ec.message());

    auto j    = nlohmann::json::parse(beast::buffers_to_string(buf.data()));
    auto type = peek_message_type(j);

    if (type == MessageType::Registered) {
        auto rm = RegisteredMessage::from_json(j);
        log_info("Successfully registered with cluster '" + rm.cluster + "'");
        if (enable_ble_)
            log_info("BLE support enabled");
    } else {
        log_warn("Unexpected message type after register: " + to_string(type));
    }
}

void ClusterNode::handle_messages()
{
    while (connected_) {
        beast::flat_buffer buf;
        beast::error_code ec;
        ws_.read(buf, ec);

        if (ec == ws::error::closed || ec == beast::error::timeout) {
            log_info("Connection to relay closed");
            connected_ = false;
            break;
        }
        if (ec) {
            log_error("Error handling messages: " + ec.message());
            connected_ = false;
            break;
        }

        try {
            auto j    = nlohmann::json::parse(beast::buffers_to_string(buf.data()));
            auto type = peek_message_type(j);

            switch (type) {
            case MessageType::NodeList: {
                auto nlm  = NodeListMessage::from_json(j);
                peer_nodes_ = std::move(nlm.nodes);
                peer_nodes_.erase(node_name_);

                std::string names;
                for (const auto& [n, _] : peer_nodes_) {
                    if (!names.empty()) names += ", ";
                    names += n;
                }
                log_info("Updated peer list: [" + names + "]");
                break;
            }
            case MessageType::HeartbeatAck: {
                auto ack = HeartbeatAckMessage::from_json(j);
                log_debug("Heartbeat acknowledged at " + ack.timestamp);
                break;
            }
            case MessageType::Message: {
                auto fm = ForwardMessage::from_json(j);
                log_info("Received message from " + fm.source + ": " + fm.payload.dump());
                break;
            }
            case MessageType::Error: {
                auto err = ErrorMessage::from_json(j);
                log_error("Error from relay: " + err.message);
                break;
            }
            default:
                log_warn("Unrecognised message type: " + to_string(type));
                break;
            }
        } catch (const std::exception& ex) {
            log_error("Failed to parse message: " + std::string(ex.what()));
        }
    }
}

void ClusterNode::send_heartbeat()
{
    while (connected_) {
        std::this_thread::sleep_for(
            std::chrono::seconds(DEFAULT_HEARTBEAT_INTERVAL_SEC));

        if (!connected_) break;

        HeartbeatMessage hb;
        hb.node_name = node_name_;

        beast::error_code ec;
        ws_.text(true);
        ws_.write(asio::buffer(hb.to_json().dump()), ec);
        if (ec) {
            log_error("Failed to send heartbeat: " + ec.message());
            connected_ = false;
            break;
        }
    }
}

void ClusterNode::start()
{
    log_info("Starting node '" + node_name_ + "' in cluster '" + cluster_name_ + "'");
    log_info("LAN port: " + std::to_string(lan_port_) +
             ", BLE: " + (enable_ble_ ? "enabled" : "disabled"));

    connect_to_relay();

    // Run heartbeat on a background thread, message loop on this thread
    heartbeat_thread_ = std::thread([this] { send_heartbeat(); });
    handle_messages();

    if (heartbeat_thread_.joinable())
        heartbeat_thread_.join();
}

} // namespace nia
