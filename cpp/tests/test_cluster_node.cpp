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

} // namespace nia::test
