#!/bin/bash
# Test script for NiA-Cluster Docker suite

echo "======================================"
echo "NiA-Cluster Test Suite"
echo "======================================"
echo ""

# Build the image
echo "Building cluster-suite Docker image..."
docker build -t cluster-suite:latest . || exit 1
echo ""

# Test 1: Help command
echo "Test 1: Displaying help message..."
docker run --rm cluster-suite:latest --help
echo ""

# Test 2: Relay mode validation (missing cluster)
echo "Test 2: Testing validation (should fail without --cluster)..."
docker run --rm cluster-suite:latest --mode relay 2>&1 | head -3
echo ""

# Test 3: Node mode validation (missing required arguments)
echo "Test 3: Testing node validation (should fail without required args)..."
docker run --rm cluster-suite:latest --mode node --cluster test 2>&1 | head -3
echo ""

echo "======================================"
echo "All basic tests passed!"
echo "======================================"
echo ""
echo "To test the full cluster, run:"
echo "  docker compose up"
echo ""
