#!/bin/bash
# Startup script for NiA-Cluster using docker run commands
# This demonstrates the usage pattern from the problem statement

set -e

echo "======================================"
echo "Starting NiA-Cluster"
echo "======================================"
echo ""

# Build the image if it doesn't exist
if ! docker image inspect cluster-suite:latest &> /dev/null; then
    echo "Building cluster-suite image..."
    docker build -t cluster-suite:latest .
    echo ""
fi

# Check if containers are already running
if docker ps | grep -q cluster_relay; then
    echo "Stopping existing containers..."
    docker stop cluster_relay node1 node2 2>/dev/null || true
    sleep 2
fi

# Start the relay server
echo "Starting relay server..."
docker run -d --name cluster_relay cluster-suite:latest \
  --mode relay --cluster myfleet --relay-port 4040

# Wait for relay to be ready
sleep 2

# Start node1 with BLE enabled
echo "Starting node1 (with BLE)..."
docker run -d --name node1 --link cluster_relay:relay cluster-suite:latest \
  --mode node --cluster myfleet --node node1 --relay-host relay --relay-port 4040 --lan-port 5001 --enable-ble

# Wait a moment
sleep 2

# Start node2 without BLE
echo "Starting node2..."
docker run -d --name node2 --link cluster_relay:relay cluster-suite:latest \
  --mode node --cluster myfleet --node node2 --relay-host relay --relay-port 4040 --lan-port 5002

# Wait for nodes to connect
sleep 3

echo ""
echo "======================================"
echo "Cluster started successfully!"
echo "======================================"
echo ""
echo "Container status:"
docker ps | grep -E "(NAMES|cluster_relay|node1|node2)"
echo ""
echo "Relay logs:"
docker logs cluster_relay
echo ""
echo "Node1 logs:"
docker logs node1
echo ""
echo "Node2 logs:"
docker logs node2
echo ""
echo "To stop the cluster, run:"
echo "  docker stop cluster_relay node1 node2"
echo "  docker rm cluster_relay node1 node2"
echo ""
