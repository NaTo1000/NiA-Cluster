#!/bin/bash
# Setup script for NiA-Cluster Docker environment
# This script matches the commands from the problem statement

set -e

echo "Setting up NiA-Cluster Docker environment..."

# Create directory (already exists in this case)
mkdir -p cluster-docker
cd cluster-docker

echo "Directory structure created."
echo ""
echo "Files present:"
ls -la

echo ""
echo "To build and run the cluster:"
echo "  cd cluster-docker"
echo "  docker compose build --progress=plain"
echo "  docker compose up"
echo ""
echo "The cluster GUI will be available on ports 8080, 8443, and 5000"
