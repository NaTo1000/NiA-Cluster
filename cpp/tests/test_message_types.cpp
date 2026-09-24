#include <gtest/gtest.h>
#include "nia/message_types.hpp"

namespace nia::test {

// ── MessageType string round-trip ──────────────────────────────────────────────

TEST(MessageTypeTest, ToStringKnownTypes)
{
    EXPECT_EQ(to_string(MessageType::Register),     "register");
    EXPECT_EQ(to_string(MessageType::Registered),   "registered");
    EXPECT_EQ(to_string(MessageType::Heartbeat),    "heartbeat");
    EXPECT_EQ(to_string(MessageType::HeartbeatAck), "heartbeat_ack");
    EXPECT_EQ(to_string(MessageType::Message),      "message");
    EXPECT_EQ(to_string(MessageType::Error),        "error");
    EXPECT_EQ(to_string(MessageType::NodeList),     "node_list");
    EXPECT_EQ(to_string(MessageType::Unknown),      "unknown");
}

TEST(MessageTypeTest, FromStringKnownTypes)
{
    EXPECT_EQ(message_type_from_string("register"),      MessageType::Register);
    EXPECT_EQ(message_type_from_string("registered"),    MessageType::Registered);
    EXPECT_EQ(message_type_from_string("heartbeat"),     MessageType::Heartbeat);
    EXPECT_EQ(message_type_from_string("heartbeat_ack"), MessageType::HeartbeatAck);
    EXPECT_EQ(message_type_from_string("message"),       MessageType::Message);
    EXPECT_EQ(message_type_from_string("error"),         MessageType::Error);
    EXPECT_EQ(message_type_from_string("node_list"),     MessageType::NodeList);
}

TEST(MessageTypeTest, FromStringUnknown)
{
    EXPECT_EQ(message_type_from_string(""),          MessageType::Unknown);
    EXPECT_EQ(message_type_from_string("REGISTER"),  MessageType::Unknown);
    EXPECT_EQ(message_type_from_string("garbage"),   MessageType::Unknown);
}

// ── RegisterMessage ───────────────────────────────────────────────────────────

TEST(RegisterMessageTest, SerialiseRoundTrip)
{
    RegisterMessage orig;
    orig.node_name   = "node1";
    orig.cluster     = "myfleet";
    orig.lan_port    = 5001;
    orig.ble_enabled = true;

    auto j    = orig.to_json();
    auto back = RegisterMessage::from_json(j);

    EXPECT_EQ(back.node_name,   orig.node_name);
    EXPECT_EQ(back.cluster,     orig.cluster);
    EXPECT_EQ(back.lan_port,    orig.lan_port);
    EXPECT_EQ(back.ble_enabled, orig.ble_enabled);
    EXPECT_EQ(j["type"].get<std::string>(), "register");
}

TEST(RegisterMessageTest, DefaultBleDisabled)
{
    RegisterMessage m;
    m.node_name = "node2";
    m.cluster   = "fleet";
    auto j = m.to_json();
    EXPECT_FALSE(j["ble_enabled"].get<bool>());
}

// ── RegisteredMessage ─────────────────────────────────────────────────────────

TEST(RegisteredMessageTest, SerialiseRoundTrip)
{
    RegisteredMessage orig;
    orig.node_name = "node1";
    orig.cluster   = "myfleet";

    auto j    = orig.to_json();
    auto back = RegisteredMessage::from_json(j);

    EXPECT_EQ(back.node_name, orig.node_name);
    EXPECT_EQ(back.cluster,   orig.cluster);
    EXPECT_EQ(j["type"].get<std::string>(), "registered");
}

// ── HeartbeatMessage ──────────────────────────────────────────────────────────

TEST(HeartbeatMessageTest, SerialiseRoundTrip)
{
    HeartbeatMessage orig;
    orig.node_name = "node1";

    auto j    = orig.to_json();
    auto back = HeartbeatMessage::from_json(j);

    EXPECT_EQ(back.node_name, orig.node_name);
    EXPECT_EQ(j["type"].get<std::string>(), "heartbeat");
}

// ── HeartbeatAckMessage ───────────────────────────────────────────────────────

TEST(HeartbeatAckMessageTest, SerialiseRoundTrip)
{
    HeartbeatAckMessage orig;
    orig.timestamp = "2026-01-01T00:00:00Z";

    auto j    = orig.to_json();
    auto back = HeartbeatAckMessage::from_json(j);

    EXPECT_EQ(back.timestamp, orig.timestamp);
    EXPECT_EQ(j["type"].get<std::string>(), "heartbeat_ack");
}

// ── ForwardMessage ────────────────────────────────────────────────────────────

TEST(ForwardMessageTest, SerialiseRoundTrip)
{
    ForwardMessage orig;
    orig.source  = "node1";
    orig.target  = "node2";
    orig.payload = {{"key", "value"}};

    auto j    = orig.to_json();
    auto back = ForwardMessage::from_json(j);

    EXPECT_EQ(back.source,           orig.source);
    EXPECT_EQ(back.target,           orig.target);
    EXPECT_EQ(back.payload["key"],   orig.payload["key"]);
    EXPECT_EQ(j["type"].get<std::string>(), "message");
}

TEST(ForwardMessageTest, MissingPayloadDefaultsToNull)
{
    nlohmann::json j = {
        {"type",   "message"},
        {"source", "node1"},
        {"target", "node2"}
    };
    auto m = ForwardMessage::from_json(j);
    EXPECT_TRUE(m.payload.is_null());
}

// ── ErrorMessage ──────────────────────────────────────────────────────────────

TEST(ErrorMessageTest, SerialiseRoundTrip)
{
    ErrorMessage orig;
    orig.message = "Target node not found";

    auto j    = orig.to_json();
    auto back = ErrorMessage::from_json(j);

    EXPECT_EQ(back.message, orig.message);
    EXPECT_EQ(j["type"].get<std::string>(), "error");
}

// ── NodeInfo ──────────────────────────────────────────────────────────────────

TEST(NodeInfoTest, SerialiseRoundTrip)
{
    NodeInfo orig;
    orig.name         = "node1";
    orig.connected_at = "2026-01-01T00:00:00Z";
    orig.lan_port     = 5001;
    orig.ble_enabled  = true;
    orig.cluster      = "myfleet";

    auto j    = orig.to_json();
    auto back = NodeInfo::from_json(j);

    EXPECT_EQ(back.name,         orig.name);
    EXPECT_EQ(back.connected_at, orig.connected_at);
    EXPECT_EQ(back.lan_port,     orig.lan_port);
    EXPECT_EQ(back.ble_enabled,  orig.ble_enabled);
    EXPECT_EQ(back.cluster,      orig.cluster);
}

// ── NodeListMessage ───────────────────────────────────────────────────────────

TEST(NodeListMessageTest, SerialiseRoundTrip)
{
    NodeListMessage orig;
    NodeInfo n1;
    n1.name         = "node1";
    n1.connected_at = "2026-01-01T00:00:00Z";
    n1.lan_port     = 5001;
    n1.ble_enabled  = false;
    n1.cluster      = "fleet";
    orig.nodes["node1"] = n1;

    auto j    = orig.to_json();
    auto back = NodeListMessage::from_json(j);

    EXPECT_EQ(back.nodes.size(), 1u);
    EXPECT_EQ(back.nodes.at("node1").lan_port, 5001);
    EXPECT_EQ(j["type"].get<std::string>(), "node_list");
}

TEST(NodeListMessageTest, EmptyNodes)
{
    NodeListMessage empty;
    auto j    = empty.to_json();
    auto back = NodeListMessage::from_json(j);

    EXPECT_TRUE(back.nodes.empty());
}

// ── peek_message_type ─────────────────────────────────────────────────────────

TEST(PeekMessageTypeTest, CorrectlyIdentifiesTypes)
{
    EXPECT_EQ(peek_message_type({{"type", "register"}}),    MessageType::Register);
    EXPECT_EQ(peek_message_type({{"type", "node_list"}}),   MessageType::NodeList);
    EXPECT_EQ(peek_message_type({{"type", "heartbeat"}}),   MessageType::Heartbeat);
}

TEST(PeekMessageTypeTest, UnknownWhenTypeMissing)
{
    EXPECT_EQ(peek_message_type({}),                 MessageType::Unknown);
    EXPECT_EQ(peek_message_type({{"other", "val"}}), MessageType::Unknown);
}

TEST(PeekMessageTypeTest, UnknownWhenTypeNotString)
{
    EXPECT_EQ(peek_message_type({{"type", 42}}),   MessageType::Unknown);
    EXPECT_EQ(peek_message_type({{"type", true}}), MessageType::Unknown);
}

} // namespace nia::test
