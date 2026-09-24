/// Integration tests for NiA-Cluster relay + node.
///
/// These tests spin up a real ClusterRelay in a background thread and connect
/// raw WebSocket clients (RawWsClient) or ClusterNode instances to it, exercising
/// the full protocol round-trip without mocking.
///
/// Port allocation (19001–19009) avoids conflicts with other system services.

#include <gtest/gtest.h>
#include "nia/cluster_relay.hpp"
#include "nia/cluster_node.hpp"
#include "nia/message_types.hpp"
#include "nia/config.hpp"

#include <boost/asio.hpp>
#include <boost/beast.hpp>
#include <boost/beast/websocket.hpp>

#include <chrono>
#include <memory>
#include <string>
#include <thread>

namespace nia::test {

namespace asio  = boost::asio;
namespace beast = boost::beast;
namespace ws    = beast::websocket;
using tcp       = asio::ip::tcp;

// ── RawWsClient ───────────────────────────────────────────────────────────────

/// Minimal synchronous WebSocket client for use in integration tests.
/// It wraps Boost.Beast without depending on ClusterNode so tests can verify
/// the protocol independently.
class RawWsClient {
public:
    RawWsClient() = default;
    ~RawWsClient() { close(); }

    /// Connect and perform the WebSocket handshake.
    /// Throws std::runtime_error on resolve, connect, or handshake failure.
    void connect(const std::string& host, uint16_t port)
    {
        tcp::resolver resolver(ioc_);
        beast::error_code ec;
        auto results = resolver.resolve(host, std::to_string(port), ec);
        if (ec) throw std::runtime_error("resolve: " + ec.message());

        asio::connect(ws_.next_layer(), results, ec);
        if (ec) throw std::runtime_error("connect: " + ec.message());

        ws_.handshake(host, "/", ec);
        if (ec) throw std::runtime_error("handshake: " + ec.message());

        open_ = true;
    }

    /// Send a JSON message to the relay.
    /// Throws std::runtime_error on write failure.
    void send(const nlohmann::json& j)
    {
        beast::error_code ec;
        ws_.text(true);
        ws_.write(asio::buffer(j.dump()), ec);
        if (ec) throw std::runtime_error("send: " + ec.message());
    }

    /// Receive one JSON message from the relay (blocking).
    /// Throws std::runtime_error on read failure.
    nlohmann::json receive()
    {
        beast::flat_buffer buf;
        beast::error_code ec;
        ws_.read(buf, ec);
        if (ec) throw std::runtime_error("receive: " + ec.message());
        return nlohmann::json::parse(beast::buffers_to_string(buf.data()));
    }

    /// Close the WebSocket connection gracefully.
    void close()
    {
        if (!open_) return;
        open_ = false;
        beast::error_code ec;
        ws_.close(ws::close_code::normal, ec);
    }

    /// Register with the relay and return the "registered" acknowledgement.
    /// Also consumes the immediately-following "node_list" broadcast.
    /// Returns the registered ack as a RegisteredMessage.
    RegisteredMessage do_register(const std::string& node_name,
                                  const std::string& cluster,
                                  int                lan_port,
                                  bool               ble = false)
    {
        RegisterMessage reg;
        reg.node_name   = node_name;
        reg.cluster     = cluster;
        reg.lan_port    = lan_port;
        reg.ble_enabled = ble;
        send(reg.to_json());

        // 1st message: "registered"
        auto ack_json = receive();
        EXPECT_EQ(peek_message_type(ack_json), MessageType::Registered)
            << "Expected 'registered', got: " << ack_json.dump();

        // 2nd message: "node_list" broadcast
        auto nl_json = receive();
        EXPECT_EQ(peek_message_type(nl_json), MessageType::NodeList)
            << "Expected 'node_list', got: " << nl_json.dump();

        return RegisteredMessage::from_json(ack_json);
    }

    /// Try to receive one message, returning nullopt if the connection is closed
    /// or an error occurs (useful for optional / trailing messages in tests).
    std::optional<nlohmann::json> try_receive()
    {
        beast::flat_buffer buf;
        beast::error_code ec;
        ws_.read(buf, ec);

        if (ec)
            return std::nullopt;

        return nlohmann::json::parse(beast::buffers_to_string(buf.data()));
    }

private:
    asio::io_context        ioc_;
    ws::stream<tcp::socket> ws_{ioc_};
    bool                    open_{false};
};

// ── Integration test fixture ──────────────────────────────────────────────────

class IntegrationTest : public ::testing::Test {
protected:
    void StartRelay(uint16_t port, const std::string& cluster = "test-cluster")
    {
        relay_ = std::make_unique<ClusterRelay>(port, cluster);
        relay_->start_async();
    }

    void TearDown() override
    {
        if (relay_) {
            relay_->stop();
            relay_.reset();
        }
        // Brief pause to allow any detached session threads to exit cleanly.
        std::this_thread::sleep_for(std::chrono::milliseconds(50));
    }

    std::unique_ptr<ClusterRelay> relay_;
};

// ── Test: relay starts and accepts connections ────────────────────────────────

TEST_F(IntegrationTest, RelayStartsAndStops)
{
    StartRelay(19001);
    EXPECT_EQ(relay_->node_count(), 0u);
    EXPECT_EQ(relay_->cluster_name(), "test-cluster");
    // Relay stops cleanly in TearDown.
}

// ── Test: relay accepts a TCP connection without crashing ─────────────────────

TEST_F(IntegrationTest, RelayAcceptsRawTcpConnection)
{
    StartRelay(19002);

    asio::io_context ioc;
    tcp::socket      sock(ioc);
    tcp::resolver    resolver(ioc);

    beast::error_code ec;
    auto results = resolver.resolve("127.0.0.1", "19002", ec);
    ASSERT_FALSE(ec) << ec.message();
    asio::connect(sock, results, ec);
    ASSERT_FALSE(ec) << ec.message();

    sock.close();
}

// ── Test: single node registration ────────────────────────────────────────────

TEST_F(IntegrationTest, SingleNodeRegistration)
{
    StartRelay(19003, "fleet-A");

    RawWsClient client;
    client.connect("127.0.0.1", 19003);

    auto ack = client.do_register("alpha", "fleet-A", 5001, /*ble=*/false);
    EXPECT_EQ(ack.node_name, "alpha");
    EXPECT_EQ(ack.cluster,   "fleet-A");

    // Give the relay a moment to update state before asserting.
    std::this_thread::sleep_for(std::chrono::milliseconds(50));
    EXPECT_EQ(relay_->node_count(), 1u);
    EXPECT_TRUE(relay_->has_node("alpha"));

    client.close();
}

// ── Test: BLE flag is correctly forwarded ────────────────────────────────────

TEST_F(IntegrationTest, NodeRegistrationWithBLE)
{
    StartRelay(19004, "fleet-B");

    RawWsClient client;
    client.connect("127.0.0.1", 19004);
    auto ack = client.do_register("ble-node", "fleet-B", 5002, /*ble=*/true);

    EXPECT_EQ(ack.node_name, "ble-node");

    client.close();
}

// ── Test: two nodes see each other in the node list ──────────────────────────

TEST_F(IntegrationTest, TwoNodesSeeEachOther)
{
    StartRelay(19005, "fleet-C");

    RawWsClient node1, node2;
    node1.connect("127.0.0.1", 19005);
    node2.connect("127.0.0.1", 19005);

    // Register node1 (receives: registered + node_list with 1 node)
    auto ack1 = node1.do_register("node1", "fleet-C", 5001);
    EXPECT_EQ(ack1.node_name, "node1");

    // Register node2 (receives: registered + node_list with 2 nodes)
    RegisterMessage reg2;
    reg2.node_name = "node2";
    reg2.cluster   = "fleet-C";
    reg2.lan_port  = 5002;
    node2.send(reg2.to_json());

    auto ack2_json = node2.receive();
    ASSERT_EQ(peek_message_type(ack2_json), MessageType::Registered);
    auto ack2 = RegisteredMessage::from_json(ack2_json);
    EXPECT_EQ(ack2.node_name, "node2");

    // node2's node_list should contain both nodes
    auto nl2_json = node2.receive();
    ASSERT_EQ(peek_message_type(nl2_json), MessageType::NodeList);
    auto nl2 = NodeListMessage::from_json(nl2_json);
    EXPECT_EQ(nl2.nodes.size(), 2u);
    EXPECT_TRUE(nl2.nodes.count("node1") > 0);
    EXPECT_TRUE(nl2.nodes.count("node2") > 0);

    // node1 should also receive an updated node_list with both nodes
    auto nl1_update_json = node1.receive();
    ASSERT_EQ(peek_message_type(nl1_update_json), MessageType::NodeList);
    auto nl1_update = NodeListMessage::from_json(nl1_update_json);
    EXPECT_EQ(nl1_update.nodes.size(), 2u);

    std::this_thread::sleep_for(std::chrono::milliseconds(50));
    EXPECT_EQ(relay_->node_count(), 2u);

    node1.close();
    node2.close();
}

// ── Test: heartbeat / ack round-trip ─────────────────────────────────────────

TEST_F(IntegrationTest, HeartbeatAck)
{
    StartRelay(19006, "fleet-D");

    RawWsClient client;
    client.connect("127.0.0.1", 19006);
    client.do_register("hb-node", "fleet-D", 5001);

    // Send heartbeat
    HeartbeatMessage hb;
    hb.node_name = "hb-node";
    client.send(hb.to_json());

    // Expect heartbeat_ack
    auto ack_json = client.receive();
    ASSERT_EQ(peek_message_type(ack_json), MessageType::HeartbeatAck);
    auto ack = HeartbeatAckMessage::from_json(ack_json);
    EXPECT_FALSE(ack.timestamp.empty());

    client.close();
}

// ── Test: message forwarding between two nodes ────────────────────────────────

TEST_F(IntegrationTest, MessageForwarding)
{
    StartRelay(19007, "fleet-E");

    RawWsClient sender, receiver;
    sender.connect("127.0.0.1", 19007);
    receiver.connect("127.0.0.1", 19007);

    sender.do_register("sender",   "fleet-E", 5001);
    // Register receiver (receives: registered + node_list; sender gets updated node_list)
    RegisterMessage reg;
    reg.node_name = "receiver";
    reg.cluster   = "fleet-E";
    reg.lan_port  = 5002;
    receiver.send(reg.to_json());
    receiver.receive();  // registered
    receiver.receive();  // node_list

    // sender gets the updated node_list broadcast (receiver just joined)
    sender.receive();

    // sender forwards a message to receiver
    ForwardMessage fwd;
    fwd.source  = "sender";
    fwd.target  = "receiver";
    fwd.payload = {{"greeting", "hello from sender"}};
    sender.send(fwd.to_json());

    // receiver reads the forwarded message
    auto msg_json = receiver.receive();
    ASSERT_EQ(peek_message_type(msg_json), MessageType::Message);
    auto fwd_recv = ForwardMessage::from_json(msg_json);
    EXPECT_EQ(fwd_recv.target,               "receiver");
    EXPECT_EQ(fwd_recv.payload["greeting"],  "hello from sender");

    sender.close();
    receiver.close();
}

// ── Test: message to unknown target returns error ─────────────────────────────

TEST_F(IntegrationTest, MessageToUnknownTargetReturnsError)
{
    StartRelay(19008, "fleet-F");

    RawWsClient client;
    client.connect("127.0.0.1", 19008);
    client.do_register("lonely-node", "fleet-F", 5001);

    ForwardMessage fwd;
    fwd.source  = "lonely-node";
    fwd.target  = "ghost-node";
    fwd.payload = {{"key", "value"}};
    client.send(fwd.to_json());

    auto err_json = client.receive();
    ASSERT_EQ(peek_message_type(err_json), MessageType::Error);
    auto err = ErrorMessage::from_json(err_json);
    EXPECT_FALSE(err.message.empty());
    EXPECT_NE(err.message.find("ghost-node"), std::string::npos);

    client.close();
}

// ── Test: disconnect triggers updated node list for peers ─────────────────────

TEST_F(IntegrationTest, NodeDisconnectUpdatesNodeList)
{
    StartRelay(19009, "fleet-G");

    RawWsClient node1, node2;
    node1.connect("127.0.0.1", 19009);
    node2.connect("127.0.0.1", 19009);

    node1.do_register("stay",   "fleet-G", 5001);
    // Register node2
    RegisterMessage reg2;
    reg2.node_name = "leave";
    reg2.cluster   = "fleet-G";
    reg2.lan_port  = 5002;
    node2.send(reg2.to_json());
    node2.receive();  // registered
    node2.receive();  // node_list (2 nodes)
    node1.receive();  // updated node_list (2 nodes) broadcast to node1

    std::this_thread::sleep_for(std::chrono::milliseconds(30));
    ASSERT_EQ(relay_->node_count(), 2u);

    // node2 disconnects
    node2.close();

    // Allow the relay session thread to process the disconnect.
    std::this_thread::sleep_for(std::chrono::milliseconds(200));
    EXPECT_EQ(relay_->node_count(), 1u);
    EXPECT_TRUE(relay_->has_node("stay"));
    EXPECT_FALSE(relay_->has_node("leave"));

    // node1 should have received an updated node_list with only itself.
    auto nl_json = node1.receive();
    ASSERT_EQ(peek_message_type(nl_json), MessageType::NodeList);
    auto nl = NodeListMessage::from_json(nl_json);
    EXPECT_EQ(nl.nodes.size(), 1u);
    EXPECT_TRUE(nl.nodes.count("stay") > 0);

    node1.close();
}

// ── Test: ClusterNode::connect_to_relay + disconnect round-trip ───────────────

TEST_F(IntegrationTest, ClusterNodeConnectAndDisconnect)
{
    StartRelay(19010, "fleet-H");

    ClusterNode node("fleet-H", "cpp-node", "127.0.0.1", 19010, 6001, false);
    ASSERT_NO_THROW(node.connect_to_relay());
    EXPECT_TRUE(node.connected());

    std::this_thread::sleep_for(std::chrono::milliseconds(50));
    EXPECT_EQ(relay_->node_count(), 1u);
    EXPECT_TRUE(relay_->has_node("cpp-node"));

    node.disconnect();
    EXPECT_FALSE(node.connected());

    std::this_thread::sleep_for(std::chrono::milliseconds(150));
    EXPECT_EQ(relay_->node_count(), 0u);
}

// ── Test: ClusterNode with BLE ────────────────────────────────────────────────

TEST_F(IntegrationTest, ClusterNodeBLEConnect)
{
    StartRelay(19011, "fleet-I");

    ClusterNode node("fleet-I", "ble-cpp-node", "127.0.0.1", 19011, 6002, /*ble=*/true);
    ASSERT_NO_THROW(node.connect_to_relay());
    EXPECT_TRUE(node.connected());

    std::this_thread::sleep_for(std::chrono::milliseconds(50));
    EXPECT_TRUE(relay_->has_node("ble-cpp-node"));

    node.disconnect();
}

// ── Test: multiple ClusterNodes in the same cluster ──────────────────────────

TEST_F(IntegrationTest, MultipleClusterNodesInSameCluster)
{
    StartRelay(19012, "fleet-J");

    ClusterNode n1("fleet-J", "n1", "127.0.0.1", 19012, 6001);
    ClusterNode n2("fleet-J", "n2", "127.0.0.1", 19012, 6002);
    ClusterNode n3("fleet-J", "n3", "127.0.0.1", 19012, 6003);

    ASSERT_NO_THROW(n1.connect_to_relay());
    ASSERT_NO_THROW(n2.connect_to_relay());
    ASSERT_NO_THROW(n3.connect_to_relay());

    std::this_thread::sleep_for(std::chrono::milliseconds(100));
    EXPECT_EQ(relay_->node_count(), 3u);

    n1.disconnect();
    n2.disconnect();
    n3.disconnect();
}

} // namespace nia::test
