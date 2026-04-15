#include "nia/cluster_relay.hpp"
#include "nia/logger.hpp"
#include "nia/message_types.hpp"

#include <chrono>
#include <iomanip>
#include <sstream>
#include <stdexcept>

namespace nia {

// ── Helpers ────────────────────────────────────────────────────────────────────

static std::string now_iso8601()
{
    auto now   = std::chrono::system_clock::now();
    auto t     = std::chrono::system_clock::to_time_t(now);
    std::ostringstream oss;
    oss << std::put_time(std::gmtime(&t), "%Y-%m-%dT%H:%M:%SZ");
    return oss.str();
}

// ── ClusterRelay ──────────────────────────────────────────────────────────────

ClusterRelay::ClusterRelay(uint16_t port, std::string cluster_name)
    : port_(port)
    , cluster_name_(std::move(cluster_name))
{}

ClusterRelay::~ClusterRelay()
{
    stop();
}

void ClusterRelay::register_node(const std::string& node_name,
                                  const NodeInfo& info,
                                  std::shared_ptr<RelaySession> session)
{
    {
        std::lock_guard<std::mutex> lock(state_mutex_);
        sessions_[node_name]  = std::move(session);
        node_info_[node_name] = info;
    }

    log_info("Node '" + node_name + "' registered (BLE: " +
             (info.ble_enabled ? "true" : "false") + ")");

    broadcast_node_list();
}

void ClusterRelay::unregister_node(const std::string& node_name)
{
    {
        std::lock_guard<std::mutex> lock(state_mutex_);
        sessions_.erase(node_name);
        node_info_.erase(node_name);
    }

    log_info("Node '" + node_name + "' unregistered");

    broadcast_node_list();
}

void ClusterRelay::broadcast_node_list()
{
    // Build a snapshot of the current node list and active sessions while
    // holding the lock, so we do not hold it while doing I/O.
    NodeListMessage nlm;
    std::vector<std::pair<std::string, std::shared_ptr<RelaySession>>> snapshot;

    {
        std::lock_guard<std::mutex> lock(state_mutex_);
        nlm.nodes = node_info_;
        for (auto& [name, session] : sessions_) {
            if (session)  // Skip null sessions (used in unit tests without live sockets)
                snapshot.emplace_back(name, session);
        }
    }

    auto payload = nlm.to_json();
    std::vector<std::string> dead;

    for (auto& [name, session] : snapshot) {
        try {
            session->send(payload);
        } catch (const std::exception& ex) {
            log_error("Failed to send node_list to '" + name + "': " + ex.what());
            dead.push_back(name);
        }
    }

    for (const auto& name : dead)
        unregister_node(name);
}

std::shared_ptr<RelaySession>
ClusterRelay::find_session(const std::string& node_name) const
{
    std::lock_guard<std::mutex> lock(state_mutex_);
    auto it = sessions_.find(node_name);
    return it != sessions_.end() ? it->second : nullptr;
}

size_t ClusterRelay::node_count() const
{
    std::lock_guard<std::mutex> lock(state_mutex_);
    return node_info_.size();
}

bool ClusterRelay::has_node(const std::string& name) const
{
    std::lock_guard<std::mutex> lock(state_mutex_);
    return node_info_.count(name) > 0;
}

void ClusterRelay::start()
{
    log_info("Starting relay server for cluster '" + cluster_name_ +
             "' on port " + std::to_string(port_));

    beast::error_code ec;
    auto endpoint = tcp::endpoint(asio::ip::make_address("0.0.0.0"), port_);

    acceptor_.open(endpoint.protocol(), ec);
    if (ec) throw std::runtime_error("acceptor open failed: " + ec.message());

    acceptor_.set_option(asio::socket_base::reuse_address(true), ec);
    acceptor_.bind(endpoint, ec);
    if (ec) throw std::runtime_error("acceptor bind failed: " + ec.message());

    acceptor_.listen(asio::socket_base::max_listen_connections, ec);
    if (ec) throw std::runtime_error("acceptor listen failed: " + ec.message());

    log_info("Relay server running on ws://0.0.0.0:" + std::to_string(port_));

    // Signal start_async() (if used) that we are now accepting connections.
    {
        std::lock_guard<std::mutex> lock(state_mutex_);
        listening_ = true;
    }
    listen_cv_.notify_one();

    do_accept();
    ioc_.run();
}

void ClusterRelay::do_accept()
{
    acceptor_.async_accept(
        [this](beast::error_code ec, tcp::socket socket) {
            if (ec == asio::error::operation_aborted || !acceptor_.is_open())
                return;

            if (ec) {
                log_error("Accept error: " + ec.message());
            } else {
                auto session = std::make_shared<RelaySession>(std::move(socket), *this);
                // Each session runs on its own detached thread with blocking I/O.
                // TODO: track session threads in a container for graceful shutdown
                //       once a thread-pool or session registry is added.
                std::thread([session]() { session->start(); }).detach();
            }

            do_accept();
        });
}

void ClusterRelay::start_async()
{
    server_thread_ = std::thread([this] { start(); });
    // Block until the acceptor is bound and listening (avoids race in tests).
    std::unique_lock<std::mutex> lock(state_mutex_);
    listen_cv_.wait(lock, [this] { return listening_; });
}

void ClusterRelay::stop()
{
    if (!server_thread_.joinable()) return;

    {
        std::lock_guard<std::mutex> lock(state_mutex_);
        listening_ = false;
    }

    beast::error_code ec;
    acceptor_.cancel(ec);
    ioc_.stop();

    server_thread_.join();
}

// ── RelaySession ──────────────────────────────────────────────────────────────

RelaySession::RelaySession(tcp::socket socket, ClusterRelay& relay)
    : ws_(std::move(socket))
    , relay_(relay)
{}

void RelaySession::start()
{
    do_accept();
}

void RelaySession::do_accept()
{
    beast::error_code ec;
    ws_.accept(ec);
    if (ec) {
        log_error("WebSocket accept error: " + ec.message());
        return;
    }
    do_read();
}

void RelaySession::do_read()
{
    for (;;) {
        beast::flat_buffer buf;
        beast::error_code ec;
        ws_.read(buf, ec);

        if (ec == ws::error::closed || ec == beast::error::timeout) {
            log_info("Node connection closed: " + node_name_);
            break;
        }
        if (ec) {
            log_error("Read error: " + ec.message());
            break;
        }

        try {
            auto j = nlohmann::json::parse(beast::buffers_to_string(buf.data()));
            handle_message(j);
        } catch (const std::exception& ex) {
            log_error("Failed to parse message: " + std::string(ex.what()));
        }
    }

    if (!node_name_.empty())
        relay_.unregister_node(node_name_);
}

void RelaySession::handle_message(const nlohmann::json& msg)
{
    switch (peek_message_type(msg)) {
    case MessageType::Register: {
        auto rm   = RegisterMessage::from_json(msg);
        node_name_ = rm.node_name;

        NodeInfo info;
        info.name         = rm.node_name;
        info.connected_at = now_iso8601();
        info.lan_port     = rm.lan_port;
        info.ble_enabled  = rm.ble_enabled;
        info.cluster      = rm.cluster.empty() ? relay_.cluster_name() : rm.cluster;

        // Send "registered" ack BEFORE broadcasting the node list so that
        // the connecting node always receives its ack as the first message
        // (ClusterNode::connect_to_relay() reads exactly one message and
        // expects "registered").
        RegisteredMessage ack;
        ack.node_name = node_name_;
        ack.cluster   = relay_.cluster_name();
        send(ack.to_json());

        // Now register (broadcasts updated node_list to all nodes).
        relay_.register_node(node_name_, info, shared_from_this());
        break;
    }
    case MessageType::Heartbeat: {
        HeartbeatAckMessage ack;
        ack.timestamp = now_iso8601();
        send(ack.to_json());
        break;
    }
    case MessageType::Message: {
        auto fm = ForwardMessage::from_json(msg);
        auto target_session = relay_.find_session(fm.target);
        if (target_session) {
            target_session->send(msg);
        } else {
            ErrorMessage err;
            err.message = "Target node '" + fm.target + "' not found";
            send(err.to_json());
        }
        break;
    }
    default:
        log_warn("Received unrecognised message type from '" + node_name_ + "'");
        break;
    }
}

void RelaySession::send(const nlohmann::json& msg)
{
    auto text = msg.dump();
    ws_.text(true);
    beast::error_code ec;
    ws_.write(asio::buffer(text), ec);
    if (ec)
        throw std::runtime_error("WebSocket write error: " + ec.message());
}

} // namespace nia
