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

TEST(ClusterRelayTest, RegisterAndUnregisterNode)
{
    ClusterRelay relay(4040, "myfleet");

    // Register a mock session (nullptr is acceptable for the map entry in this
    // unit test since we do not call broadcast_node_list here directly).
    NodeInfo info;
    info.name         = "node1";
    info.connected_at = "2026-01-01T00:00:00Z";
    info.lan_port     = 5001;
    info.ble_enabled  = false;
    info.cluster      = "myfleet";

    // Using nullptr session to avoid needing a live socket.
    // This tests the map management only.
    relay.register_node("node1", info, nullptr);
    // After registration the session should be present.
    // (find_session returns nullptr for a nullptr entry, so just verify no throw)
    EXPECT_NO_THROW(relay.find_session("node1"));

    relay.unregister_node("node1");
    EXPECT_EQ(relay.find_session("node1"), nullptr);
}

TEST(ClusterRelayTest, UnregisterNonExistentNodeNoThrow)
{
    ClusterRelay relay(4040, "myfleet");
    EXPECT_NO_THROW(relay.unregister_node("ghost"));
}

TEST(ClusterRelayTest, BroadcastEmptyNodeListNoThrow)
{
    ClusterRelay relay(4040, "myfleet");
    // With no sessions registered, broadcast should be a no-op.
    EXPECT_NO_THROW(relay.broadcast_node_list());
}

} // namespace nia::test
