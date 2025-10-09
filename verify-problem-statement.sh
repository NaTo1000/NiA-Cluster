#!/bin/bash
# Verify that the exact commands from the problem statement work

set -e

echo "======================================"
echo "Verifying Problem Statement Commands"
echo "======================================"
echo ""

# Ensure image is built
if ! docker image inspect cluster-suite:latest &> /dev/null; then
    echo "Building cluster-suite image..."
    docker build -t cluster-suite:latest .
fi

# Clean up any existing containers
docker stop cluster_relay node1 node2 2>/dev/null || true
docker rm cluster_relay node1 node2 2>/dev/null || true

echo "Starting relay server (in background)..."
docker run -d --name cluster_relay cluster-suite:latest \
  --mode relay --cluster myfleet --relay-port 4040
sleep 2

echo "Starting node1 with --enable-ble (exact command from problem statement)..."
docker run -d --name node1 --link cluster_relay:relay cluster-suite:latest \
  --mode node --cluster myfleet --node node1 --relay-host relay --relay-port 4040 --lan-port 5001 --enable-ble
sleep 2

echo "Starting node2 without BLE (exact command from problem statement)..."
docker run -d --name node2 --link cluster_relay:relay cluster-suite:latest \
  --mode node --cluster myfleet --node node2 --relay-host relay --relay-port 4040 --lan-port 5002
sleep 3

echo ""
echo "======================================"
echo "Verification Results"
echo "======================================"
echo ""
echo "All containers running:"
docker ps --filter name=cluster_relay --filter name=node1 --filter name=node2 --format "table {{.Names}}\t{{.Status}}"
echo ""

echo "Relay logs (checking node registrations):"
docker logs cluster_relay 2>&1 | grep -E "(Starting relay|Node .* registered)" || echo "No registration logs yet"
echo ""

echo "Node1 logs (checking BLE enabled):"
docker logs node1 2>&1 | grep -E "(Starting node|BLE:|connected to relay)" || echo "No connection logs yet"
echo ""

echo "Node2 logs (checking BLE disabled):"
docker logs node2 2>&1 | grep -E "(Starting node|BLE:|connected to relay)" || echo "No connection logs yet"
echo ""

# Verify specific requirements
echo "Checking requirements:"
echo -n "  ✓ Relay listening: "
docker logs cluster_relay 2>&1 | grep -q "Relay server running" && echo "YES" || echo "NO"

echo -n "  ✓ Node1 BLE enabled: "
docker logs node1 2>&1 | grep -q "BLE: enabled" && echo "YES" || echo "NO"

echo -n "  ✓ Node2 BLE disabled: "
docker logs node2 2>&1 | grep -q "BLE: disabled" && echo "YES" || echo "NO"

echo -n "  ✓ Node1 connected: "
docker logs node1 2>&1 | grep -q "connected to relay" && echo "YES" || echo "NO"

echo -n "  ✓ Node2 connected: "
docker logs node2 2>&1 | grep -q "connected to relay" && echo "YES" || echo "NO"

echo -n "  ✓ Node1 registered on relay: "
docker logs cluster_relay 2>&1 | grep -q "Node 'node1' registered" && echo "YES" || echo "NO"

echo -n "  ✓ Node2 registered on relay: "
docker logs cluster_relay 2>&1 | grep -q "Node 'node2' registered" && echo "YES" || echo "NO"

echo ""
echo "======================================"
echo "Verification Complete!"
echo "======================================"
echo ""
echo "To clean up, run:"
echo "  docker stop cluster_relay node1 node2"
echo "  docker rm cluster_relay node1 node2"
