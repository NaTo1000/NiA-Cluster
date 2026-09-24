#include <gtest/gtest.h>
#include "nia/cluster_node.hpp"
#include "nia/config.hpp"

namespace nia::test {

// ── ClusterNode construction ──────────────────────────────────────────────────

TEST(ClusterNodeTest, ConstructorStoresConfig)
{
    ClusterNode node("myfleet", "node1", "localhost",
                     DEFAULT_RELAY_PORT, 5001, /*enable_ble=*/true);

    EXPECT_EQ(node.cluster_name(), "myfleet");
    EXPECT_EQ(node.node_name(),    "node1");
    EXPECT_FALSE(node.connected()); // Not connected yet
}

TEST(ClusterNodeTest, InitiallyNotConnected)
{
    ClusterNode node("myfleet", "node2", "127.0.0.1",
                     DEFAULT_RELAY_PORT, 5002);
    EXPECT_FALSE(node.connected());
}

TEST(ClusterNodeTest, InitialPeerNodesEmpty)
{
    ClusterNode node("myfleet", "node3", "127.0.0.1",
                     DEFAULT_RELAY_PORT, 5003, false);
    EXPECT_TRUE(node.peer_nodes().empty());
}

TEST(ClusterNodeTest, ConnectToRelayThrowsWhenNoRelay)
{
    // Connecting to a port where nothing is listening should throw.
    ClusterNode node("myfleet", "node4", "127.0.0.1",
                     /*relay_port=*/19999, 5004);

    EXPECT_THROW(node.connect_to_relay(), std::exception);
    EXPECT_FALSE(node.connected());
}

// ── disconnect() on an unconnected node must be a no-op ──────────────────────

TEST(ClusterNodeTest, DisconnectWhenNotConnectedNoThrow)
{
    ClusterNode node("myfleet", "node5", "127.0.0.1",
                     DEFAULT_RELAY_PORT, 5005);
    EXPECT_NO_THROW(node.disconnect());
    EXPECT_FALSE(node.connected());
}

// ── Multiple disconnect() calls are safe ─────────────────────────────────────

TEST(ClusterNodeTest, DoubleDisconnectNoThrow)
{
    ClusterNode node("myfleet", "node6", "127.0.0.1",
                     DEFAULT_RELAY_PORT, 5006);
    EXPECT_NO_THROW(node.disconnect());
    EXPECT_NO_THROW(node.disconnect());
}

// ── Node name and cluster name must be preserved ──────────────────────────────

TEST(ClusterNodeTest, NodeNameNotEmpty)
{
    ClusterNode node("fleet", "alpha-node", "localhost",
                     DEFAULT_RELAY_PORT, 5007);
    EXPECT_EQ(node.node_name(), "alpha-node");
}

TEST(ClusterNodeTest, ClusterNameNotEmpty)
{
    ClusterNode node("fleet-beta", "n1", "localhost",
                     DEFAULT_RELAY_PORT, 5008);
    EXPECT_EQ(node.cluster_name(), "fleet-beta");
}

} // namespace nia::test
