#include <gtest/gtest.h>
#include "nia/cluster_relay.hpp"
#include "nia/message_types.hpp"

namespace nia::test {

// ── ClusterRelay construction ─────────────────────────────────────────────────

TEST(ClusterRelayTest, ConstructorStoresConfig)
{
    ClusterRelay relay(4040, "myfleet");
    EXPECT_EQ(relay.port(),         4040u);
    EXPECT_EQ(relay.cluster_name(), "myfleet");
}

TEST(ClusterRelayTest, FindSessionReturnNullWhenEmpty)
{
    ClusterRelay relay(4040, "myfleet");
    EXPECT_EQ(relay.find_session("nonexistent"), nullptr);
}

TEST(ClusterRelayTest, NodeCountZeroWhenEmpty)
{
    ClusterRelay relay(4040, "myfleet");
    EXPECT_EQ(relay.node_count(), 0u);
}

TEST(ClusterRelayTest, HasNodeFalseWhenEmpty)
{
    ClusterRelay relay(4040, "myfleet");
    EXPECT_FALSE(relay.has_node("anything"));
}

// ── Registration / unregistration ────────────────────────────────────────────

TEST(ClusterRelayTest, RegisterAndUnregisterNode)
{
    ClusterRelay relay(4040, "myfleet");

    NodeInfo info;
    info.name         = "node1";
    info.connected_at = "2026-01-01T00:00:00Z";
    info.lan_port     = 5001;
    info.ble_enabled  = false;
    info.cluster      = "myfleet";

    // Registering with nullptr session is valid for unit-testing map management
    // (broadcast_node_list skips null sessions).
    relay.register_node("node1", info, nullptr);
    EXPECT_EQ(relay.node_count(), 1u);
    EXPECT_TRUE(relay.has_node("node1"));

    relay.unregister_node("node1");
    EXPECT_EQ(relay.node_count(), 0u);
    EXPECT_FALSE(relay.has_node("node1"));
    EXPECT_EQ(relay.find_session("node1"), nullptr);
}

TEST(ClusterRelayTest, RegisterMultipleNodes)
{
    ClusterRelay relay(4040, "myfleet");

    for (int i = 1; i <= 3; ++i) {
        NodeInfo info;
        info.name    = "node" + std::to_string(i);
        info.cluster = "myfleet";
        relay.register_node(info.name, info, nullptr);
    }
    EXPECT_EQ(relay.node_count(), 3u);

    relay.unregister_node("node2");
    EXPECT_EQ(relay.node_count(), 2u);
    EXPECT_FALSE(relay.has_node("node2"));
    EXPECT_TRUE(relay.has_node("node1"));
    EXPECT_TRUE(relay.has_node("node3"));
}

TEST(ClusterRelayTest, RegisterSameNodeTwiceOverwrites)
{
    ClusterRelay relay(4040, "myfleet");

    NodeInfo info1;
    info1.name     = "node1";
    info1.lan_port = 5001;
    relay.register_node("node1", info1, nullptr);

    NodeInfo info2;
    info2.name     = "node1";
    info2.lan_port = 5099;
    relay.register_node("node1", info2, nullptr);

    EXPECT_EQ(relay.node_count(), 1u);  // Still just one node
}

TEST(ClusterRelayTest, UnregisterNonExistentNodeNoThrow)
{
    ClusterRelay relay(4040, "myfleet");
    EXPECT_NO_THROW(relay.unregister_node("ghost"));
}

// ── broadcast with no sessions ────────────────────────────────────────────────

TEST(ClusterRelayTest, BroadcastEmptyNodeListNoThrow)
{
    ClusterRelay relay(4040, "myfleet");
    EXPECT_NO_THROW(relay.broadcast_node_list());
}

TEST(ClusterRelayTest, BroadcastWithNullSessionsNoThrow)
{
    ClusterRelay relay(4040, "myfleet");

    NodeInfo info;
    info.name    = "node1";
    info.cluster = "myfleet";
    relay.register_node("node1", info, nullptr);

    // broadcast_node_list skips null sessions — must not crash.
    EXPECT_NO_THROW(relay.broadcast_node_list());
}

// ── Accessors ─────────────────────────────────────────────────────────────────

TEST(ClusterRelayTest, ClusterNameAccessor)
{
    ClusterRelay relay(9999, "fleet-alpha");
    EXPECT_EQ(relay.cluster_name(), "fleet-alpha");
}

TEST(ClusterRelayTest, PortAccessor)
{
    ClusterRelay relay(12345, "test");
    EXPECT_EQ(relay.port(), 12345u);
}

} // namespace nia::test
