#pragma once

#include <nlohmann/json.hpp>

#include <optional>
#include <string>

namespace nia {

// ── Message type enum ──────────────────────────────────────────────────────────

enum class MessageType {
    Register,
    Registered,
    Heartbeat,
    HeartbeatAck,
    Message,
    Error,
    NodeList,
    Unknown
};

/// Convert a MessageType to its JSON wire-format string ("register", "node_list", …).
std::string to_string(MessageType type);

/// Parse a JSON wire-format string into a MessageType.
/// Returns MessageType::Unknown for unrecognised strings.
MessageType message_type_from_string(const std::string& s);

// ── Per-message structs ────────────────────────────────────────────────────────

struct RegisterMessage {
    std::string node_name;
    std::string cluster;
    int         lan_port   = 0;
    bool        ble_enabled = false;

    nlohmann::json to_json() const;
    static RegisterMessage from_json(const nlohmann::json& j);
};

struct RegisteredMessage {
    std::string node_name;
    std::string cluster;

    nlohmann::json to_json() const;
    static RegisteredMessage from_json(const nlohmann::json& j);
};

struct HeartbeatMessage {
    std::string node_name;

    nlohmann::json to_json() const;
    static HeartbeatMessage from_json(const nlohmann::json& j);
};

struct HeartbeatAckMessage {
    std::string timestamp;

    nlohmann::json to_json() const;
    static HeartbeatAckMessage from_json(const nlohmann::json& j);
};

struct ForwardMessage {
    std::string source;
    std::string target;
    nlohmann::json payload;

    nlohmann::json to_json() const;
    static ForwardMessage from_json(const nlohmann::json& j);
};

struct ErrorMessage {
    std::string message;

    nlohmann::json to_json() const;
    static ErrorMessage from_json(const nlohmann::json& j);
};

struct NodeInfo {
    std::string name;
    std::string connected_at;
    int         lan_port    = 0;
    bool        ble_enabled = false;
    std::string cluster;

    nlohmann::json to_json() const;
    static NodeInfo from_json(const nlohmann::json& j);
};

struct NodeListMessage {
    /// Map from node_name to its metadata, as received from / sent to the relay.
    std::unordered_map<std::string, NodeInfo> nodes;

    nlohmann::json to_json() const;
    static NodeListMessage from_json(const nlohmann::json& j);
};

// ── Parsing helper ─────────────────────────────────────────────────────────────

/// Determine the MessageType of a raw JSON object without fully parsing it.
MessageType peek_message_type(const nlohmann::json& j);

} // namespace nia
