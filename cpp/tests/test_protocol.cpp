/// Protocol conformance tests for NiA-Cluster.
///
/// These tests verify the relay's behaviour when receiving well-formed,
/// malformed, or edge-case protocol messages, and validate the fallback
/// measures that keep the relay running when clients misbehave.
///
/// All tests use a real relay in a background thread (same RawWsClient helper
/// pattern as the integration tests) so we exercise the full I/O path.
///
/// Port allocation: 19100–19149 (distinct from integration tests 19001–19012)

#include <gtest/gtest.h>
#include "nia/cluster_relay.hpp"
#include "nia/message_types.hpp"

#include <boost/asio.hpp>
#include <boost/beast.hpp>
#include <boost/beast/websocket.hpp>

#include <chrono>
#include <string>
#include <thread>

namespace nia::test {

namespace asio  = boost::asio;
namespace beast = boost::beast;
namespace ws    = beast::websocket;
using tcp       = asio::ip::tcp;

// ── ProtoClient ───────────────────────────────────────────────────────────────

/// Thin WebSocket client used exclusively in protocol tests.
/// Exposes raw send/receive so tests can inject any byte sequence.
class ProtoClient {
public:
    ProtoClient() = default;
    ~ProtoClient() { close(); }

    /// Connect and perform the WebSocket handshake.
    /// Throws std::runtime_error on failure.
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

    /// Send a raw text frame (any string content).
    void send_text(const std::string& raw)
    {
        beast::error_code ec;
        ws_.text(true);
        ws_.write(asio::buffer(raw), ec);
        if (ec) throw std::runtime_error("send_text: " + ec.message());
    }

    /// Send a JSON message.
    void send(const nlohmann::json& j) { send_text(j.dump()); }

    /// Receive one text frame; throws on error.
    nlohmann::json receive()
    {
        beast::flat_buffer buf;
        beast::error_code ec;
        ws_.read(buf, ec);
        if (ec) throw std::runtime_error("receive: " + ec.message());
        return nlohmann::json::parse(beast::buffers_to_string(buf.data()));
    }

    /// Try to receive one frame; returns nullopt on any error (incl. closed).
    std::optional<nlohmann::json> try_receive()
    {
        beast::flat_buffer buf;
        beast::error_code ec;
        ws_.read(buf, ec);
        if (ec) return std::nullopt;
        try {
            return nlohmann::json::parse(beast::buffers_to_string(buf.data()));
        } catch (...) {
            return std::nullopt;
        }
    }

    void close()
    {
        if (!open_) return;
        open_ = false;
        beast::error_code ec;
        ws_.close(ws::close_code::normal, ec);
    }

    /// Perform a full register + consume ack + consume node_list.
    void do_register(const std::string& name, const std::string& cluster,
                     int lan_port = 5001, bool ble = false)
    {
        RegisterMessage reg;
        reg.node_name   = name;
        reg.cluster     = cluster;
        reg.lan_port    = lan_port;
        reg.ble_enabled = ble;
        send(reg.to_json());
        receive();  // registered
        receive();  // node_list
    }

private:
    asio::io_context        ioc_;
    ws::stream<tcp::socket> ws_{ioc_};
    bool                    open_{false};
};

// ── Protocol test fixture ─────────────────────────────────────────────────────

class ProtocolTest : public ::testing::Test {
protected:
    void StartRelay(uint16_t port, const std::string& cluster = "proto-cluster")
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
        std::this_thread::sleep_for(std::chrono::milliseconds(50));
    }

    std::unique_ptr<ClusterRelay> relay_;
};

// ── Fallback: malformed JSON is logged and ignored; relay continues ───────────

TEST_F(ProtocolTest, MalformedJsonFallback_RelayKeepsRunning)
{
    StartRelay(19100);

    // Client A sends garbage JSON
    ProtoClient bad;
    bad.connect("127.0.0.1", 19100);
    bad.send_text("{not valid json!!!");
    // Relay should log the error and NOT close the connection on this frame alone.
    // We can confirm the relay is still alive by connecting a new, well-formed client.
    bad.close();

    // Client B can still connect and register normally.
    ProtoClient good;
    ASSERT_NO_THROW(good.connect("127.0.0.1", 19100));
    ASSERT_NO_THROW(good.do_register("node-b", "proto-cluster"));
    EXPECT_TRUE(relay_->has_node("node-b"));

    good.close();
}

// ── Fallback: empty JSON object is treated as unknown type ────────────────────

TEST_F(ProtocolTest, EmptyJsonObjectFallback_RelayKeepsRunning)
{
    StartRelay(19101);

    ProtoClient client;
    client.connect("127.0.0.1", 19101);
    client.send(nlohmann::json::object());  // {} — no "type" field

    // Relay silently ignores unknown type; session stays open.
    // Verify by sending a valid register afterwards.
    RegisterMessage reg;
    reg.node_name = "survivor";
    reg.cluster   = "proto-cluster";
    reg.lan_port  = 5001;
    client.send(reg.to_json());

    auto ack_json = client.receive();
    EXPECT_EQ(peek_message_type(ack_json), MessageType::Registered);
    EXPECT_EQ(relay_->node_count(), 1u);

    client.close();
}

// ── Fallback: unknown message type is silently ignored ────────────────────────

TEST_F(ProtocolTest, UnknownMessageTypeFallback_NoResponse)
{
    StartRelay(19102);

    ProtoClient client;
    client.connect("127.0.0.1", 19102);
    // First register so we know the session is alive
    client.do_register("n1", "proto-cluster");

    // Send a completely unknown message type
    client.send({{"type", "magic_unicorn"}, {"data", 42}});

    // Relay should not send any response to an unknown type; send another
    // known message and verify it is processed correctly (heartbeat → ack).
    HeartbeatMessage hb;
    hb.node_name = "n1";
    client.send(hb.to_json());

    auto ack = client.receive();
    ASSERT_EQ(peek_message_type(ack), MessageType::HeartbeatAck)
        << "Expected HeartbeatAck after unknown-type fallback, got: " << ack.dump();

    client.close();
}

// ── Protocol: register with empty cluster uses relay cluster name ─────────────

TEST_F(ProtocolTest, RegisterEmptyClusterDefaultsToRelayCluster)
{
    StartRelay(19103, "my-fleet");

    ProtoClient client;
    client.connect("127.0.0.1", 19103);

    RegisterMessage reg;
    reg.node_name = "node-x";
    reg.cluster   = "";       // <── intentionally empty
    reg.lan_port  = 5001;
    client.send(reg.to_json());

    auto ack_json = client.receive();
    ASSERT_EQ(peek_message_type(ack_json), MessageType::Registered);
    auto ack = RegisteredMessage::from_json(ack_json);

    // The registered ack should echo back the relay's cluster name.
    EXPECT_EQ(ack.cluster, "my-fleet");

    client.close();
}

// ── Protocol: heartbeat from unregistered session still receives ack ──────────

TEST_F(ProtocolTest, HeartbeatFromUnregisteredSessionReceivesAck)
{
    // The relay responds to heartbeats regardless of whether the sender has
    // registered: this is a deliberate protocol choice (heartbeat is stateless).
    StartRelay(19104);

    ProtoClient client;
    client.connect("127.0.0.1", 19104);
    // Do NOT register — send heartbeat directly.
    HeartbeatMessage hb;
    hb.node_name = "unregistered-node";
    client.send(hb.to_json());

    auto ack_json = client.receive();
    ASSERT_EQ(peek_message_type(ack_json), MessageType::HeartbeatAck);
    auto ack = HeartbeatAckMessage::from_json(ack_json);
    EXPECT_FALSE(ack.timestamp.empty())
        << "Heartbeat ack should include a non-empty ISO-8601 timestamp";

    client.close();
}

// ── Protocol: heartbeat ack timestamp matches ISO-8601 format ─────────────────

TEST_F(ProtocolTest, HeartbeatAckTimestampIsIso8601)
{
    StartRelay(19105);

    ProtoClient client;
    client.connect("127.0.0.1", 19105);
    client.do_register("ts-node", "proto-cluster");

    HeartbeatMessage hb;
    hb.node_name = "ts-node";
    client.send(hb.to_json());

    auto ack_json = client.receive();
    auto ack      = HeartbeatAckMessage::from_json(ack_json);
    // Timestamp must be at least 19 characters: "YYYY-MM-DDTHH:MM:SSZ"
    EXPECT_GE(ack.timestamp.size(), 19u);
    EXPECT_EQ(ack.timestamp.back(), 'Z');

    client.close();
}

// ── Protocol: forward message to missing target returns error with target name -

TEST_F(ProtocolTest, ForwardToMissingTargetReturnsErrorWithName)
{
    StartRelay(19106);

    ProtoClient client;
    client.connect("127.0.0.1", 19106);
    client.do_register("lone-sender", "proto-cluster");

    ForwardMessage fwd;
    fwd.source  = "lone-sender";
    fwd.target  = "does-not-exist";
    fwd.payload = {{"cmd", "ping"}};
    client.send(fwd.to_json());

    auto err_json = client.receive();
    ASSERT_EQ(peek_message_type(err_json), MessageType::Error);
    auto err = ErrorMessage::from_json(err_json);
    EXPECT_FALSE(err.message.empty());
    EXPECT_NE(err.message.find("does-not-exist"), std::string::npos)
        << "Error message should name the missing target; got: " << err.message;

    client.close();
}

// ── Protocol: registered ack always precedes node_list broadcast ──────────────

TEST_F(ProtocolTest, RegisteredAckPrecedesNodeListBroadcast)
{
    // This is the critical ordering guarantee: the connecting node receives
    // "registered" BEFORE the "node_list" so that ClusterNode::connect_to_relay()
    // (which reads exactly one message expecting "registered") always succeeds.
    StartRelay(19107);

    ProtoClient client;
    client.connect("127.0.0.1", 19107);

    RegisterMessage reg;
    reg.node_name = "ordering-node";
    reg.cluster   = "proto-cluster";
    reg.lan_port  = 5001;
    client.send(reg.to_json());

    auto first  = client.receive();
    auto second = client.receive();

    EXPECT_EQ(peek_message_type(first),  MessageType::Registered)
        << "First message after register must be 'registered', got: " << first.dump();
    EXPECT_EQ(peek_message_type(second), MessageType::NodeList)
        << "Second message after register must be 'node_list', got: " << second.dump();

    client.close();
}

// ── Protocol: registered message contains correct node_name and cluster ────────

TEST_F(ProtocolTest, RegisteredMessageContainsCorrectFields)
{
    StartRelay(19108, "field-check-fleet");

    ProtoClient client;
    client.connect("127.0.0.1", 19108);

    RegisterMessage reg;
    reg.node_name = "exact-node";
    reg.cluster   = "field-check-fleet";
    reg.lan_port  = 6789;
    client.send(reg.to_json());

    auto ack_json = client.receive();
    ASSERT_EQ(peek_message_type(ack_json), MessageType::Registered);
    auto ack = RegisteredMessage::from_json(ack_json);
    EXPECT_EQ(ack.node_name, "exact-node");
    EXPECT_EQ(ack.cluster,   "field-check-fleet");

    client.close();
}

// ── Protocol: node_list message contains type + nodes fields ──────────────────

TEST_F(ProtocolTest, NodeListMessageContainsRequiredFields)
{
    StartRelay(19109);

    ProtoClient client;
    client.connect("127.0.0.1", 19109);

    RegisterMessage reg;
    reg.node_name = "fields-node";
    reg.cluster   = "proto-cluster";
    reg.lan_port  = 5001;
    client.send(reg.to_json());

    client.receive();  // registered

    auto nl_json = client.receive();  // node_list
    ASSERT_EQ(peek_message_type(nl_json), MessageType::NodeList);
    ASSERT_TRUE(nl_json.contains("type"));
    ASSERT_TRUE(nl_json.contains("nodes"));
    ASSERT_TRUE(nl_json["nodes"].is_object());
    ASSERT_TRUE(nl_json["nodes"].contains("fields-node"));

    // Verify the node's own NodeInfo fields
    const auto& ni = nl_json["nodes"]["fields-node"];
    EXPECT_TRUE(ni.contains("name"));
    EXPECT_TRUE(ni.contains("connected_at"));
    EXPECT_TRUE(ni.contains("lan_port"));
    EXPECT_TRUE(ni.contains("ble_enabled"));
    EXPECT_EQ(ni["name"].get<std::string>(),    "fields-node");
    EXPECT_EQ(ni["lan_port"].get<int>(),        5001);
    EXPECT_EQ(ni["ble_enabled"].get<bool>(),    false);

    client.close();
}

// ── Protocol: node_list includes accurate lan_port and ble_enabled fields ──────

TEST_F(ProtocolTest, NodeListLanPortAndBleFieldsAreAccurate)
{
    StartRelay(19110);

    ProtoClient client;
    client.connect("127.0.0.1", 19110);

    RegisterMessage reg;
    reg.node_name   = "meta-node";
    reg.cluster     = "proto-cluster";
    reg.lan_port    = 7777;
    reg.ble_enabled = true;
    client.send(reg.to_json());

    client.receive();  // registered
    auto nl_json = client.receive();  // node_list
    auto nl = NodeListMessage::from_json(nl_json);
    ASSERT_TRUE(nl.nodes.count("meta-node") > 0);

    const auto& info = nl.nodes.at("meta-node");
    EXPECT_EQ(info.lan_port,    7777);
    EXPECT_EQ(info.ble_enabled, true);

    client.close();
}

// ── Fallback: relay recovers and accepts new connections after bad input ────────

TEST_F(ProtocolTest, RelayRecoveryAfterMultipleMalformedMessages)
{
    StartRelay(19111);

    // Bombard the relay with 5 malformed frames
    for (int i = 0; i < 5; ++i) {
        ProtoClient bad;
        bad.connect("127.0.0.1", 19111);
        bad.send_text("}{broken_json}{");
        bad.close();
        std::this_thread::sleep_for(std::chrono::milliseconds(10));
    }

    // Relay must still be fully operational.
    ProtoClient good;
    ASSERT_NO_THROW(good.connect("127.0.0.1", 19111));
    ASSERT_NO_THROW(good.do_register("after-recovery", "proto-cluster"));
    EXPECT_TRUE(relay_->has_node("after-recovery"));

    good.close();
}

// ── Protocol: forward message with empty payload is valid ─────────────────────

TEST_F(ProtocolTest, ForwardMessageWithEmptyPayloadIsValid)
{
    StartRelay(19112);

    ProtoClient sender, receiver;
    sender.connect("127.0.0.1", 19112);
    receiver.connect("127.0.0.1", 19112);

    sender.do_register("s", "proto-cluster", 5001);
    receiver.do_register("r", "proto-cluster", 5002);
    sender.receive();  // consume updated node_list from receiver joining

    ForwardMessage fwd;
    fwd.source  = "s";
    fwd.target  = "r";
    fwd.payload = nlohmann::json::object();  // empty object — valid
    sender.send(fwd.to_json());

    auto msg = receiver.receive();
    ASSERT_EQ(peek_message_type(msg), MessageType::Message);
    auto recv = ForwardMessage::from_json(msg);
    EXPECT_TRUE(recv.payload.is_object());

    sender.close();
    receiver.close();
}

// ── Protocol: multiple heartbeats from same session each receive an ack ────────

TEST_F(ProtocolTest, MultipleHeartbeatsEachReceiveAck)
{
    StartRelay(19113);

    ProtoClient client;
    client.connect("127.0.0.1", 19113);
    client.do_register("hb-multi", "proto-cluster");

    for (int i = 0; i < 3; ++i) {
        HeartbeatMessage hb;
        hb.node_name = "hb-multi";
        client.send(hb.to_json());

        auto ack = client.receive();
        ASSERT_EQ(peek_message_type(ack), MessageType::HeartbeatAck)
            << "Expected HeartbeatAck for heartbeat #" << (i + 1);
    }

    client.close();
}

// ── Protocol: re-registration by same client gets a new registered ack ─────────

TEST_F(ProtocolTest, ReRegistrationReceivesNewAck)
{
    StartRelay(19114);

    ProtoClient client;
    client.connect("127.0.0.1", 19114);

    // First registration
    RegisterMessage reg;
    reg.node_name = "re-reg-node";
    reg.cluster   = "proto-cluster";
    reg.lan_port  = 5001;
    client.send(reg.to_json());
    auto ack1 = client.receive();
    client.receive();  // node_list

    ASSERT_EQ(peek_message_type(ack1), MessageType::Registered);

    // Second registration on the same connection
    reg.lan_port = 5099;
    client.send(reg.to_json());
    auto ack2 = client.receive();
    client.receive();  // node_list

    ASSERT_EQ(peek_message_type(ack2), MessageType::Registered);
    // Node count should still be 1 (overwritten, not duplicated)
    std::this_thread::sleep_for(std::chrono::milliseconds(30));
    EXPECT_EQ(relay_->node_count(), 1u);

    client.close();
}

} // namespace nia::test
