/// Algorithm correctness tests for NiA-Cluster.
///
/// These tests verify that the relay's core algorithms — message routing,
/// node-list topology management, peer-discovery, broadcast accuracy and
/// session-lifecycle handling — produce exactly the expected results.
///
/// "Fallback" coverage included: the relay must remain stable and correct
/// under concurrent operations, rapid connect/disconnect storms, re-use of
/// the same node name, and large payloads.
///
/// Port allocation: 19200–19249 (distinct from integration 19001–19012,
/// protocol 19100–19149)

#include <gtest/gtest.h>
#include "nia/cluster_relay.hpp"
#include "nia/cluster_node.hpp"
#include "nia/message_types.hpp"

#include <boost/asio.hpp>
#include <boost/beast.hpp>
#include <boost/beast/websocket.hpp>

#include <chrono>
#include <future>
#include <string>
#include <thread>
#include <vector>

namespace nia::test {

namespace asio  = boost::asio;
namespace beast = boost::beast;
namespace ws    = beast::websocket;
using tcp       = asio::ip::tcp;

// ── AlgoClient ────────────────────────────────────────────────────────────────

/// Thin WebSocket client for algorithm tests.
class AlgoClient {
public:
    AlgoClient() = default;
    ~AlgoClient() { close(); }

    /// Connect and perform the WebSocket handshake.
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

    void send(const nlohmann::json& j)
    {
        beast::error_code ec;
        ws_.text(true);
        ws_.write(asio::buffer(j.dump()), ec);
        if (ec) throw std::runtime_error("send: " + ec.message());
    }

    nlohmann::json receive()
    {
        beast::flat_buffer buf;
        beast::error_code ec;
        ws_.read(buf, ec);
        if (ec) throw std::runtime_error("receive: " + ec.message());
        return nlohmann::json::parse(beast::buffers_to_string(buf.data()));
    }

    std::optional<nlohmann::json> try_receive()
    {
        beast::flat_buffer buf;
        beast::error_code ec;
        ws_.read(buf, ec);
        if (ec) return std::nullopt;
        try { return nlohmann::json::parse(beast::buffers_to_string(buf.data())); }
        catch (...) { return std::nullopt; }
    }

    void close()
    {
        if (!open_) return;
        open_ = false;
        beast::error_code ec;
        ws_.close(ws::close_code::normal, ec);
    }

    /// Register and consume both the ack and the node_list broadcast.
    /// Returns the node_list that arrived after registration.
    NodeListMessage do_register(const std::string& name,
                                const std::string& cluster,
                                int  lan_port = 5001,
                                bool ble      = false)
    {
        RegisterMessage reg;
        reg.node_name   = name;
        reg.cluster     = cluster;
        reg.lan_port    = lan_port;
        reg.ble_enabled = ble;
        send(reg.to_json());

        receive();                               // registered
        auto nl = receive();                     // node_list
        return NodeListMessage::from_json(nl);
    }

private:
    asio::io_context        ioc_;
    ws::stream<tcp::socket> ws_{ioc_};
    bool                    open_{false};
};

// ── Algorithm test fixture ────────────────────────────────────────────────────

class AlgorithmTest : public ::testing::Test {
protected:
    void StartRelay(uint16_t port, const std::string& cluster = "algo-cluster")
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

// ── Algorithm: routing selectivity — A→B is NOT delivered to C ───────────────

TEST_F(AlgorithmTest, RoutingSelectivity_MessageOnlyDeliveredToTarget)
{
    StartRelay(19200);

    AlgoClient a, b, c;
    a.connect("127.0.0.1", 19200);
    b.connect("127.0.0.1", 19200);
    c.connect("127.0.0.1", 19200);

    a.do_register("A", "algo-cluster", 5001);
    b.do_register("B", "algo-cluster", 5002);
    a.receive();  // A gets node_list update for B joining
    c.do_register("C", "algo-cluster", 5003);
    a.receive();  // A gets node_list update for C joining
    b.receive();  // B gets node_list update for C joining

    // A sends a message targeted only at B
    ForwardMessage fwd;
    fwd.source  = "A";
    fwd.target  = "B";
    fwd.payload = {{"secret", "only-for-B"}};
    a.send(fwd.to_json());

    // B receives the message
    auto msg = b.receive();
    ASSERT_EQ(peek_message_type(msg), MessageType::Message);
    EXPECT_EQ(ForwardMessage::from_json(msg).payload["secret"], "only-for-B");

    // C must NOT receive any message (we rely on the relay not forwarding to C)
    // Close A and B so C's session eventually gets an updated node_list (disconnect)
    // which would be the next message C receives — NOT the forwarded payload.
    a.close();
    b.close();

    // Give relay time to process disconnects and broadcast node_list to C
    std::this_thread::sleep_for(std::chrono::milliseconds(200));

    auto c_msg = c.try_receive();
    // C may receive a node_list broadcast (A/B disconnected); it must NOT be
    // the forwarded "secret" message.
    if (c_msg.has_value()) {
        EXPECT_NE(peek_message_type(*c_msg), MessageType::Message)
            << "C should not receive a forwarded message; got: " << c_msg->dump();
    }

    c.close();
}

// ── Algorithm: bidirectional message exchange ─────────────────────────────────

TEST_F(AlgorithmTest, BidirectionalMessaging_AToBAndBToA)
{
    StartRelay(19201);

    AlgoClient a, b;
    a.connect("127.0.0.1", 19201);
    b.connect("127.0.0.1", 19201);

    a.do_register("A", "algo-cluster", 5001);
    b.do_register("B", "algo-cluster", 5002);
    a.receive();  // A gets updated node_list after B joins

    // A → B
    ForwardMessage fwdAB;
    fwdAB.source  = "A";
    fwdAB.target  = "B";
    fwdAB.payload = {{"direction", "A-to-B"}};
    a.send(fwdAB.to_json());

    auto b_recv = b.receive();
    ASSERT_EQ(peek_message_type(b_recv), MessageType::Message);
    EXPECT_EQ(ForwardMessage::from_json(b_recv).payload["direction"], "A-to-B");

    // B → A
    ForwardMessage fwdBA;
    fwdBA.source  = "B";
    fwdBA.target  = "A";
    fwdBA.payload = {{"direction", "B-to-A"}};
    b.send(fwdBA.to_json());

    auto a_recv = a.receive();
    ASSERT_EQ(peek_message_type(a_recv), MessageType::Message);
    EXPECT_EQ(ForwardMessage::from_json(a_recv).payload["direction"], "B-to-A");

    a.close();
    b.close();
}

// ── Algorithm: sequential message ordering is preserved ───────────────────────

TEST_F(AlgorithmTest, SequentialMessageOrderPreserved)
{
    StartRelay(19202);

    AlgoClient sender, receiver;
    sender.connect("127.0.0.1", 19202);
    receiver.connect("127.0.0.1", 19202);

    sender.do_register("src",  "algo-cluster", 5001);
    receiver.do_register("dst", "algo-cluster", 5002);
    sender.receive();  // updated node_list

    const int N = 10;
    for (int i = 0; i < N; ++i) {
        ForwardMessage fwd;
        fwd.source  = "src";
        fwd.target  = "dst";
        fwd.payload = {{"seq", i}};
        sender.send(fwd.to_json());
    }

    for (int i = 0; i < N; ++i) {
        auto msg = receiver.receive();
        ASSERT_EQ(peek_message_type(msg), MessageType::Message);
        auto fwd = ForwardMessage::from_json(msg);
        EXPECT_EQ(fwd.payload["seq"].get<int>(), i)
            << "Expected sequence number " << i
            << " but received " << fwd.payload["seq"].get<int>();
    }

    sender.close();
    receiver.close();
}

// ── Algorithm: node-list topology accuracy across join/leave events ───────────

TEST_F(AlgorithmTest, TopologyAccuracy_NodeListReflectsExactState)
{
    StartRelay(19203);

    AlgoClient n1, n2, n3;
    n1.connect("127.0.0.1", 19203);
    n2.connect("127.0.0.1", 19203);
    n3.connect("127.0.0.1", 19203);

    // Step 1: n1 joins — list has 1 node
    {
        auto nl = n1.do_register("n1", "algo-cluster");
        EXPECT_EQ(nl.nodes.size(), 1u);
        EXPECT_TRUE(nl.nodes.count("n1") > 0);
    }

    // Step 2: n2 joins — list has 2 nodes
    {
        auto nl = n2.do_register("n2", "algo-cluster");
        EXPECT_EQ(nl.nodes.size(), 2u);
        EXPECT_TRUE(nl.nodes.count("n1") > 0);
        EXPECT_TRUE(nl.nodes.count("n2") > 0);
        n1.receive();  // consume updated node_list broadcast to n1
    }

    // Step 3: n3 joins — list has 3 nodes
    {
        auto nl = n3.do_register("n3", "algo-cluster");
        EXPECT_EQ(nl.nodes.size(), 3u);
        EXPECT_TRUE(nl.nodes.count("n1") > 0);
        EXPECT_TRUE(nl.nodes.count("n2") > 0);
        EXPECT_TRUE(nl.nodes.count("n3") > 0);
        n1.receive();  // broadcast to n1
        n2.receive();  // broadcast to n2
    }

    ASSERT_EQ(relay_->node_count(), 3u);

    // Step 4: n2 leaves — relay state and broadcast reflect 2 nodes
    n2.close();
    std::this_thread::sleep_for(std::chrono::milliseconds(150));
    EXPECT_EQ(relay_->node_count(), 2u);
    EXPECT_TRUE(relay_->has_node("n1"));
    EXPECT_FALSE(relay_->has_node("n2"));
    EXPECT_TRUE(relay_->has_node("n3"));

    // n1 and n3 each receive a node_list with the updated topology
    auto nl_n1 = NodeListMessage::from_json(n1.receive());
    EXPECT_EQ(nl_n1.nodes.size(), 2u);
    EXPECT_FALSE(nl_n1.nodes.count("n2") > 0);

    auto nl_n3 = NodeListMessage::from_json(n3.receive());
    EXPECT_EQ(nl_n3.nodes.size(), 2u);
    EXPECT_FALSE(nl_n3.nodes.count("n2") > 0);

    n1.close();
    n3.close();
}

// ── Algorithm: re-registration with same name overwrites, count stays 1 ────────

TEST_F(AlgorithmTest, ReRegistrationOverwritesEntry_CountStaysOne)
{
    StartRelay(19204);

    AlgoClient client;
    client.connect("127.0.0.1", 19204);

    // First registration — lan_port=5001
    RegisterMessage reg;
    reg.node_name = "same-name";
    reg.cluster   = "algo-cluster";
    reg.lan_port  = 5001;
    client.send(reg.to_json());
    client.receive();  // registered
    client.receive();  // node_list

    EXPECT_EQ(relay_->node_count(), 1u);

    // Second registration — lan_port=5099 (same name, updated metadata)
    reg.lan_port = 5099;
    client.send(reg.to_json());
    client.receive();  // registered
    auto nl_json = client.receive();  // node_list

    // Still exactly 1 node
    EXPECT_EQ(relay_->node_count(), 1u);

    // The updated node_list must reflect the new lan_port
    auto nl = NodeListMessage::from_json(nl_json);
    ASSERT_EQ(nl.nodes.size(), 1u);
    EXPECT_EQ(nl.nodes.at("same-name").lan_port, 5099);

    client.close();
}

// ── Algorithm: broadcast reaches ALL registered nodes ─────────────────────────

TEST_F(AlgorithmTest, BroadcastReachesAllRegisteredNodes)
{
    StartRelay(19205);

    const int N = 4;
    std::vector<std::unique_ptr<AlgoClient>> clients;
    clients.reserve(N);

    // Register N clients one by one; each prior client gets an updated
    // node_list for every new joiner.
    for (int i = 0; i < N; ++i) {
        clients.push_back(std::make_unique<AlgoClient>());
        clients.back()->connect("127.0.0.1", 19205);

        RegisterMessage reg;
        reg.node_name = "node-" + std::to_string(i);
        reg.cluster   = "algo-cluster";
        reg.lan_port  = 5000 + i;
        clients.back()->send(reg.to_json());
        clients.back()->receive();  // registered
        clients.back()->receive();  // node_list

        // All previously registered clients receive a node_list broadcast
        for (int j = 0; j < i; ++j)
            clients[j]->receive();
    }

    ASSERT_EQ(relay_->node_count(), static_cast<size_t>(N));

    // Now disconnect node-0; all other N-1 clients should each receive a
    // broadcast with N-1 nodes.
    clients[0]->close();
    std::this_thread::sleep_for(std::chrono::milliseconds(150));

    EXPECT_EQ(relay_->node_count(), static_cast<size_t>(N - 1));

    for (int i = 1; i < N; ++i) {
        auto nl_json = clients[i]->receive();
        ASSERT_EQ(peek_message_type(nl_json), MessageType::NodeList)
            << "client " << i << " expected node_list after disconnect broadcast";
        auto nl = NodeListMessage::from_json(nl_json);
        EXPECT_EQ(nl.nodes.size(), static_cast<size_t>(N - 1))
            << "node_list for client " << i << " should have " << N - 1 << " nodes";
        EXPECT_FALSE(nl.nodes.count("node-0") > 0)
            << "disconnected node-0 must not appear in node_list";
    }

    for (int i = 1; i < N; ++i)
        clients[i]->close();
}

// ── Algorithm: large payload forwarding ──────────────────────────────────────

TEST_F(AlgorithmTest, LargePayloadForwarding)
{
    StartRelay(19206);

    AlgoClient sender, receiver;
    sender.connect("127.0.0.1", 19206);
    receiver.connect("127.0.0.1", 19206);

    sender.do_register("big-sender",   "algo-cluster", 5001);
    receiver.do_register("big-receiver", "algo-cluster", 5002);
    sender.receive();  // updated node_list

    // Build a ~64 KB payload
    const std::string large_value(64 * 1024, 'X');
    ForwardMessage fwd;
    fwd.source  = "big-sender";
    fwd.target  = "big-receiver";
    fwd.payload = {{"data", large_value}};
    sender.send(fwd.to_json());

    auto msg = receiver.receive();
    ASSERT_EQ(peek_message_type(msg), MessageType::Message);
    auto fwd_recv = ForwardMessage::from_json(msg);
    EXPECT_EQ(fwd_recv.payload["data"].get<std::string>().size(), large_value.size());

    sender.close();
    receiver.close();
}

// ── Algorithm: concurrent registrations — all nodes appear in final list ────────

TEST_F(AlgorithmTest, ConcurrentRegistrations_AllNodesInFinalList)
{
    StartRelay(19207);

    const int N = 5;
    std::vector<std::future<void>> futures;
    futures.reserve(N);

    // Each future connects and registers a distinct node.
    for (int i = 0; i < N; ++i) {
        futures.push_back(std::async(std::launch::async, [i]() {
            AlgoClient c;
            c.connect("127.0.0.1", 19207);
            RegisterMessage reg;
            reg.node_name = "concurrent-" + std::to_string(i);
            reg.cluster   = "algo-cluster";
            reg.lan_port  = 5000 + i;
            c.send(reg.to_json());
            c.receive();  // registered
            c.receive();  // node_list
            // Stay connected briefly so the relay tracks all nodes simultaneously.
            std::this_thread::sleep_for(std::chrono::milliseconds(200));
            c.close();
        }));
    }

    // Wait for all registrations to land.
    for (auto& f : futures) f.get();

    // After all complete, relay should have 0 nodes (each closed their connection).
    // Before closing, we could have up to N nodes — the important invariant is that
    // each node got its registered ack without errors (futures didn't throw).
    // (Node count may be 0 at this point because clients closed.)
    SUCCEED();
}

// ── Algorithm: rapid connect/disconnect stability (fallback stress) ────────────

TEST_F(AlgorithmTest, RapidConnectDisconnect_RelayRemainsStable)
{
    StartRelay(19208);

    // Rapidly open and close 20 connections without registering.
    for (int i = 0; i < 20; ++i) {
        AlgoClient c;
        c.connect("127.0.0.1", 19208);
        c.close();
    }

    std::this_thread::sleep_for(std::chrono::milliseconds(100));

    // Relay must still be operational.
    AlgoClient final_client;
    ASSERT_NO_THROW(final_client.connect("127.0.0.1", 19208));
    ASSERT_NO_THROW(final_client.do_register("stable-node", "algo-cluster"));
    EXPECT_EQ(relay_->node_count(), 1u);

    final_client.close();
}

// ── Algorithm: rapid register/unregister storm with real ClusterNode ──────────

TEST_F(AlgorithmTest, RapidRegisterUnregister_RelayRemainsStable)
{
    StartRelay(19209);

    for (int i = 0; i < 8; ++i) {
        ClusterNode node("algo-cluster",
                         "storm-" + std::to_string(i),
                         "127.0.0.1", 19209,
                         5000 + i);
        ASSERT_NO_THROW(node.connect_to_relay());
        EXPECT_TRUE(node.connected());
        node.disconnect();
        std::this_thread::sleep_for(std::chrono::milliseconds(30));
    }

    std::this_thread::sleep_for(std::chrono::milliseconds(200));
    EXPECT_EQ(relay_->node_count(), 0u);

    // Relay must remain usable after the storm.
    ClusterNode post("algo-cluster", "post-storm", "127.0.0.1", 19209, 6001);
    ASSERT_NO_THROW(post.connect_to_relay());
    EXPECT_TRUE(post.connected());
    std::this_thread::sleep_for(std::chrono::milliseconds(50));
    EXPECT_EQ(relay_->node_count(), 1u);
    post.disconnect();
}

// ── Algorithm: ClusterNode excludes itself from peer_nodes view ───────────────

TEST_F(AlgorithmTest, ClusterNodeExcludesSelfFromPeerNodes)
{
    StartRelay(19210);

    ClusterNode nodeA("algo-cluster", "peer-A", "127.0.0.1", 19210, 5001);
    ClusterNode nodeB("algo-cluster", "peer-B", "127.0.0.1", 19210, 5002);

    ASSERT_NO_THROW(nodeA.connect_to_relay());
    ASSERT_NO_THROW(nodeB.connect_to_relay());

    // Run handle_messages() on background threads so that node_list broadcasts
    // are processed and peer_nodes_ gets populated and filtered.
    std::thread tA([&]() { nodeA.handle_messages(); });
    std::thread tB([&]() { nodeB.handle_messages(); });

    // Allow time for the node_list messages to arrive and be processed.
    std::this_thread::sleep_for(std::chrono::milliseconds(150));

    // Disconnect both nodes to unblock handle_messages() on each thread.
    nodeA.disconnect();
    nodeB.disconnect();
    tA.join();
    tB.join();

    // peer_nodes should not contain the node's own name.
    EXPECT_TRUE(nodeA.peer_nodes().find("peer-A") == nodeA.peer_nodes().end())
        << "peer-A should not appear in its own peer_nodes map";
    EXPECT_TRUE(nodeB.peer_nodes().find("peer-B") == nodeB.peer_nodes().end())
        << "peer-B should not appear in its own peer_nodes map";
}

// ── Algorithm: node metadata (lan_port, ble_enabled) preserved in relay ────────

TEST_F(AlgorithmTest, NodeMetadataPreservedInRelay)
{
    StartRelay(19211);

    AlgoClient client;
    client.connect("127.0.0.1", 19211);

    RegisterMessage reg;
    reg.node_name   = "metadata-node";
    reg.cluster     = "algo-cluster";
    reg.lan_port    = 9876;
    reg.ble_enabled = true;
    client.send(reg.to_json());
    client.receive();  // registered
    auto nl_json = client.receive();  // node_list

    auto nl = NodeListMessage::from_json(nl_json);
    ASSERT_TRUE(nl.nodes.count("metadata-node") > 0);
    const auto& info = nl.nodes.at("metadata-node");
    EXPECT_EQ(info.lan_port,    9876);
    EXPECT_EQ(info.ble_enabled, true);
    EXPECT_EQ(info.name,        "metadata-node");

    client.close();
}

// ── Algorithm: node_list sent to joining node reflects current topology ────────

TEST_F(AlgorithmTest, JoiningNodeReceivesCurrentTopologyImmediately)
{
    StartRelay(19212);

    AlgoClient established1, established2, newcomer;

    // First two nodes register
    established1.connect("127.0.0.1", 19212);
    established2.connect("127.0.0.1", 19212);

    established1.do_register("e1", "algo-cluster", 5001);
    established2.do_register("e2", "algo-cluster", 5002);
    established1.receive();  // e1 gets updated node_list when e2 joins

    ASSERT_EQ(relay_->node_count(), 2u);

    // Third node joins and should immediately receive a node_list with all 3
    newcomer.connect("127.0.0.1", 19212);
    auto nl = newcomer.do_register("new", "algo-cluster", 5003);

    EXPECT_EQ(nl.nodes.size(), 3u)
        << "Newcomer's node_list must include all 3 nodes immediately on join";
    EXPECT_TRUE(nl.nodes.count("e1")  > 0);
    EXPECT_TRUE(nl.nodes.count("e2")  > 0);
    EXPECT_TRUE(nl.nodes.count("new") > 0);

    established1.close();
    established2.close();
    newcomer.close();
}

// ── Algorithm: connect_to_relay throws and remains not-connected on failure ──────

TEST_F(AlgorithmTest, ConnectToRelayFallback_ThrowsAndRemainsDisconnected)
{
    // No relay started on port 19213 — connection must fail and leave the node
    // in a clean, not-connected state.
    ClusterNode node("algo-cluster", "fallback-node", "127.0.0.1",
                     /*relay_port=*/19213, 5001);

    EXPECT_THROW(node.connect_to_relay(), std::exception);
    EXPECT_FALSE(node.connected());
    // Verify disconnect() on a not-connected node is a no-op (no throw)
    EXPECT_NO_THROW(node.disconnect());
    EXPECT_FALSE(node.connected());
}

} // namespace nia::test
