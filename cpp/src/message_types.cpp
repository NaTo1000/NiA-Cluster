#include "nia/message_types.hpp"

#include <stdexcept>

namespace nia {

// ── MessageType helpers ───────────────────────────────────────────────────────

std::string to_string(MessageType type)
{
    switch (type) {
    case MessageType::Register:     return "register";
    case MessageType::Registered:   return "registered";
    case MessageType::Heartbeat:    return "heartbeat";
    case MessageType::HeartbeatAck: return "heartbeat_ack";
    case MessageType::Message:      return "message";
    case MessageType::Error:        return "error";
    case MessageType::NodeList:     return "node_list";
    default:                        return "unknown";
    }
}

MessageType message_type_from_string(const std::string& s)
{
    if (s == "register")      return MessageType::Register;
    if (s == "registered")    return MessageType::Registered;
    if (s == "heartbeat")     return MessageType::Heartbeat;
    if (s == "heartbeat_ack") return MessageType::HeartbeatAck;
    if (s == "message")       return MessageType::Message;
    if (s == "error")         return MessageType::Error;
    if (s == "node_list")     return MessageType::NodeList;
    return MessageType::Unknown;
}

MessageType peek_message_type(const nlohmann::json& j)
{
    if (!j.contains("type") || !j["type"].is_string())
        return MessageType::Unknown;
    return message_type_from_string(j["type"].get<std::string>());
}

// ── RegisterMessage ───────────────────────────────────────────────────────────

nlohmann::json RegisterMessage::to_json() const
{
    return {
        {"type",        "register"},
        {"node_name",   node_name},
        {"cluster",     cluster},
        {"lan_port",    lan_port},
        {"ble_enabled", ble_enabled}
    };
}

RegisterMessage RegisterMessage::from_json(const nlohmann::json& j)
{
    RegisterMessage m;
    m.node_name   = j.value("node_name",   "");
    m.cluster     = j.value("cluster",     "");
    m.lan_port    = j.value("lan_port",    0);
    m.ble_enabled = j.value("ble_enabled", false);
    return m;
}

// ── RegisteredMessage ─────────────────────────────────────────────────────────

nlohmann::json RegisteredMessage::to_json() const
{
    return {
        {"type",      "registered"},
        {"node_name", node_name},
        {"cluster",   cluster}
    };
}

RegisteredMessage RegisteredMessage::from_json(const nlohmann::json& j)
{
    RegisteredMessage m;
    m.node_name = j.value("node_name", "");
    m.cluster   = j.value("cluster",   "");
    return m;
}

// ── HeartbeatMessage ──────────────────────────────────────────────────────────

nlohmann::json HeartbeatMessage::to_json() const
{
    return {
        {"type",      "heartbeat"},
        {"node_name", node_name}
    };
}

HeartbeatMessage HeartbeatMessage::from_json(const nlohmann::json& j)
{
    HeartbeatMessage m;
    m.node_name = j.value("node_name", "");
    return m;
}

// ── HeartbeatAckMessage ───────────────────────────────────────────────────────

nlohmann::json HeartbeatAckMessage::to_json() const
{
    return {
        {"type",      "heartbeat_ack"},
        {"timestamp", timestamp}
    };
}

HeartbeatAckMessage HeartbeatAckMessage::from_json(const nlohmann::json& j)
{
    HeartbeatAckMessage m;
    m.timestamp = j.value("timestamp", "");
    return m;
}

// ── ForwardMessage ────────────────────────────────────────────────────────────

nlohmann::json ForwardMessage::to_json() const
{
    return {
        {"type",    "message"},
        {"source",  source},
        {"target",  target},
        {"payload", payload}
    };
}

ForwardMessage ForwardMessage::from_json(const nlohmann::json& j)
{
    ForwardMessage m;
    m.source  = j.value("source", "");
    m.target  = j.value("target", "");
    m.payload = j.contains("payload") ? j["payload"] : nlohmann::json{};
    return m;
}

// ── ErrorMessage ──────────────────────────────────────────────────────────────

nlohmann::json ErrorMessage::to_json() const
{
    return {
        {"type",    "error"},
        {"message", message}
    };
}

ErrorMessage ErrorMessage::from_json(const nlohmann::json& j)
{
    ErrorMessage m;
    m.message = j.value("message", "");
    return m;
}

// ── NodeInfo ──────────────────────────────────────────────────────────────────

nlohmann::json NodeInfo::to_json() const
{
    return {
        {"name",         name},
        {"connected_at", connected_at},
        {"lan_port",     lan_port},
        {"ble_enabled",  ble_enabled},
        {"cluster",      cluster}
    };
}

NodeInfo NodeInfo::from_json(const nlohmann::json& j)
{
    NodeInfo ni;
    ni.name         = j.value("name",         "");
    ni.connected_at = j.value("connected_at", "");
    ni.lan_port     = j.value("lan_port",     0);
    ni.ble_enabled  = j.value("ble_enabled",  false);
    ni.cluster      = j.value("cluster",      "");
    return ni;
}

// ── NodeListMessage ───────────────────────────────────────────────────────────

nlohmann::json NodeListMessage::to_json() const
{
    nlohmann::json nodes_json = nlohmann::json::object();
    for (const auto& [name, info] : nodes)
        nodes_json[name] = info.to_json();

    return {
        {"type",  "node_list"},
        {"nodes", nodes_json}
    };
}

NodeListMessage NodeListMessage::from_json(const nlohmann::json& j)
{
    NodeListMessage m;
    if (j.contains("nodes") && j["nodes"].is_object()) {
        for (const auto& [name, val] : j["nodes"].items())
            m.nodes[name] = NodeInfo::from_json(val);
    }
    return m;
}

} // namespace nia
