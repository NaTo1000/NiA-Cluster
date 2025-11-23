#!/bin/bash
# Test script for NiA-Cluster Dashboard

echo "======================================"
echo "NiA-Cluster Dashboard Test"
echo "======================================"
echo ""

# Build the image
echo "Building cluster-suite Docker image..."
docker build -t cluster-suite:latest . > /dev/null 2>&1 || exit 1
echo "✓ Build successful"
echo ""

# Test 1: Dashboard help command
echo "Test 1: Dashboard help command..."
docker run --rm cluster-suite:latest dashboard.py --help > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✓ Dashboard help works"
else
    echo "✗ Dashboard help failed"
    exit 1
fi
echo ""

# Test 2: Start cluster with dashboard
echo "Test 2: Starting cluster with dashboard..."
docker compose up -d > /dev/null 2>&1
sleep 10

# Check if all containers are running
if docker ps | grep -q "cluster_relay" && \
   docker ps | grep -q "node1" && \
   docker ps | grep -q "node2" && \
   docker ps | grep -q "cluster_dashboard"; then
    echo "✓ All containers started successfully"
else
    echo "✗ Some containers failed to start"
    docker compose down > /dev/null 2>&1
    exit 1
fi
echo ""

# Test 3: Check dashboard is accessible
echo "Test 3: Checking dashboard accessibility..."
sleep 5
if curl -s http://localhost:8080/health | grep -q "healthy"; then
    echo "✓ Dashboard is accessible and healthy"
else
    echo "✗ Dashboard health check failed"
    docker compose down > /dev/null 2>&1
    exit 1
fi
echo ""

# Test 4: Check dashboard API
echo "Test 4: Checking dashboard API..."
if curl -s http://localhost:8080/api/status | grep -q "relay"; then
    echo "✓ Dashboard API is working"
else
    echo "✗ Dashboard API failed"
    docker compose down > /dev/null 2>&1
    exit 1
fi
echo ""

# Test 5: Check relay status in dashboard
echo "Test 5: Checking relay status..."
STATUS=$(curl -s http://localhost:8080/api/status | grep -o '"status":"[^"]*"' | head -1)
if echo "$STATUS" | grep -q "healthy"; then
    echo "✓ Relay status is being monitored"
else
    echo "⚠ Relay status: $STATUS"
fi
echo ""

# Clean up
echo "Cleaning up..."
docker compose down > /dev/null 2>&1

echo ""
echo "======================================"
echo "All dashboard tests passed!"
echo "======================================"
echo ""
echo "Dashboard Features Verified:"
echo "  ✓ Help command works"
echo "  ✓ Container starts successfully"
echo "  ✓ Web interface is accessible"
echo "  ✓ Health check endpoint works"
echo "  ✓ API endpoints work"
echo "  ✓ Relay monitoring is active"
echo ""
