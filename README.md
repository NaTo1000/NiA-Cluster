# NiA-Cluster
Internal WiFi/BLE ESP clustering manager with port control and security

## Overview
NiA-Cluster is a distributed clustering system that allows multiple nodes to communicate through a central relay server. It supports optional BLE (Bluetooth Low Energy) capabilities and provides port control for node communication.

## Features
- **Relay Mode**: Central coordination server for cluster management
- **Node Mode**: Distributed nodes that can join clusters
- **BLE Support**: Optional Bluetooth Low Energy support for nodes
- **WebSocket Communication**: Real-time communication between relay and nodes
- **Auto-discovery**: Nodes automatically discover peers through the relay

## Quick Start

> **Note:** For deploying to Google Cloud Platform (GCR + Cloud Run), see [docs/DEPLOYMENT_GCP.md](docs/DEPLOYMENT_GCP.md). Remember: **never commit secrets to the repository**.

### Option 1: Using the Startup Script (Easiest)
```bash
./start-cluster.sh
```

This will automatically build the image and start the relay + 2 nodes.

### Option 1b: Using Google Cloud Build (For Cloud Deployments)
```bash
# Build with Cloud Build for fast, containerized builds
./submit-cloud-build.sh root YOUR_PROJECT_ID

# Or build both cluster-suite and nia-enterprise
./submit-cloud-build.sh both YOUR_PROJECT_ID
```

See [CLOUD_BUILD.md](CLOUD_BUILD.md) for detailed Cloud Build integration documentation.

### Option 2: Using Docker Compose (Recommended for Development)
```bash
# Build and start the entire cluster
docker compose up --build

# Stop the cluster
docker compose down
```

### Option 3: Using Docker Run Commands (Manual)

#### 1. Start the Relay Server
```bash
docker build -t cluster-suite:latest .

docker run --rm --name cluster_relay cluster-suite:latest \
  --mode relay --cluster myfleet --relay-port 4040
```

#### 2. Start Nodes

**Node 1 with BLE enabled:**
```bash
docker run --rm --name node1 --link cluster_relay:relay cluster-suite:latest \
  --mode node --cluster myfleet --node node1 --relay-host relay --relay-port 4040 --lan-port 5001 --enable-ble
```

**Node 2 without BLE:**
```bash
docker run --rm --name node2 --link cluster_relay:relay cluster-suite:latest \
  --mode node --cluster myfleet --node node2 --relay-host relay --relay-port 4040 --lan-port 5002
```

## Command-Line Options

### Common Options
- `--mode`: Operation mode (`relay` or `node`) - **Required**
- `--cluster`: Cluster name - **Required**
- `--relay-port`: Relay server port (default: 4040)
- `--debug`: Enable debug logging

### Relay Mode Options
No additional options required. The relay will listen on the specified port.

### Node Mode Options
- `--node`: Node name - **Required**
- `--relay-host`: Relay server hostname - **Required**
- `--lan-port`: Node LAN port - **Required**
- `--enable-ble`: Enable BLE support (optional flag)

## Architecture
```
                    ┌─────────────────┐
                    │  Cluster Relay  │
                    │   (Port 4040)   │
                    └────────┬────────┘
                             │
                  ┌──────────┴──────────┐
                  │                     │
          ┌───────▼────────┐    ┌──────▼────────┐
          │     Node1      │    │     Node2     │
          │  (Port 5001)   │    │  (Port 5002)  │
          │  BLE Enabled   │    │               │
          └────────────────┘    └───────────────┘
```

## Development

### Local Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Run relay
python3 cluster_manager.py --mode relay --cluster myfleet --relay-port 4040

# Run node (in another terminal)
python3 cluster_manager.py --mode node --cluster myfleet --node node1 \
  --relay-host localhost --relay-port 4040 --lan-port 5001 --enable-ble
```

### Building the Docker Image
```bash
docker build -t cluster-suite:latest .
```

## Testing

Run the test suite:
```bash
./test.sh
```

Verify the exact commands from the problem statement work:
```bash
./verify-problem-statement.sh
```

## Scripts

- `start-cluster.sh` - Quick start script that builds and launches a complete cluster
- `test.sh` - Runs basic validation tests on the Docker image
- `verify-problem-statement.sh` - Verifies that the exact commands from requirements work correctly
- `submit-cloud-build.sh` - Submit builds to Google Cloud Build for containerized VM builds
- `build-cloud-local.sh` - Test Cloud Build configurations locally before submission

## License
MIT License
