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
- **Buster Cluster**: Autonomous AI-driven distribution across cloud networks

## Buster Cluster - Autonomous Distribution System

The Buster Cluster is an advanced autonomous distribution system that can distribute workloads across multiple cloud networks. It features:

### Key Features
- **Autonomous Decision-Making**: AI-driven decisions for optimal workload distribution
- **Security Assessments**: Evaluates cloud network security levels automatically
- **Network Speed Monitoring**: Measures latency and bandwidth for performance optimization
- **Self-Optimization**: Runs optimization cycles every 15 seconds with on-the-fly adjustments
- **Self-Coding**: Dynamically generates optimization rules based on historical patterns
- **Multi-Cloud Support**: Works across GCP, AWS, Azure, and private data centers

### Quick Start - Buster Cluster

```bash
# Run with sample networks
python3 buster_cluster.py --cluster myfleet --node-id buster1 --use-sample-networks

# Run with custom networks
python3 buster_cluster.py --cluster myfleet --node-id buster1 \
  --add-network gcp1 us-central1 gcp gcp-relay.example.com \
  --add-network aws1 us-east-1 aws aws-relay.example.com

# View status only
python3 buster_cluster.py --cluster myfleet --node-id buster1 --status-only

# Disable autonomous mode
python3 buster_cluster.py --cluster myfleet --node-id buster1 --no-autonomous

# Custom security/performance weights
python3 buster_cluster.py --cluster myfleet --node-id buster1 \
  --security-weight 0.7 --performance-weight 0.3
```

### Buster Cluster Architecture
```
                    ┌─────────────────────────────────┐
                    │      Buster Cluster Brain       │
                    │  (Autonomous Decision Engine)   │
                    └─────────────┬───────────────────┘
                                  │
          ┌───────────────────────┼───────────────────────┐
          │                       │                       │
          ▼                       ▼                       ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   GCP Network   │     │   AWS Network   │     │  Azure Network  │
│   us-central1   │     │    us-east-1    │     │     westus      │
│ Security: HIGH  │     │ Security: HIGH  │     │ Security: HIGH  │
└────────┬────────┘     └────────┬────────┘     └────────┬────────┘
         │                       │                       │
         ▼                       ▼                       ▼
    ┌─────────┐             ┌─────────┐             ┌─────────┐
    │  Relay  │             │  Relay  │             │  Relay  │
    │ Server  │             │ Server  │             │ Server  │
    └─────────┘             └─────────┘             └─────────┘
```

### How It Works

1. **Network Registration**: Cloud networks are registered with the Buster Cluster
2. **Security Assessment**: Each network is evaluated for security posture (TLS, provider, region)
3. **Performance Measurement**: Latency and bandwidth are measured to each network
4. **Autonomous Decision**: The AI engine selects the optimal network based on weighted scores
5. **Self-Optimization**: Every 15 seconds, the system reassesses and may migrate workloads
6. **Self-Coding**: Optimization rules are dynamically generated based on patterns

## Quick Start

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

### Buster Cluster Options
- `--cluster`: Cluster name - **Required**
- `--node-id`: Node identifier - **Required**
- `--autonomous`: Enable autonomous mode (default: true)
- `--no-autonomous`: Disable autonomous mode
- `--security-weight`: Weight for security in decisions (0.0-1.0, default: 0.5)
- `--performance-weight`: Weight for performance in decisions (0.0-1.0, default: 0.5)
- `--add-network ID REGION PROVIDER ENDPOINT`: Add a cloud network
- `--use-sample-networks`: Use sample networks for testing
- `--status-only`: Show status and exit
- `--debug`: Enable debug logging

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

Test the Buster Cluster:
```bash
./test_buster_cluster.sh
```

Verify the exact commands from the problem statement work:
```bash
./verify-problem-statement.sh
```

## Scripts

- `start-cluster.sh` - Quick start script that builds and launches a complete cluster
- `test.sh` - Runs basic validation tests on the Docker image
- `test_buster_cluster.sh` - Runs tests for the Buster Cluster autonomous distribution system
- `verify-problem-statement.sh` - Verifies that the exact commands from requirements work correctly
- `submit-cloud-build.sh` - Submit builds to Google Cloud Build for containerized VM builds
- `build-cloud-local.sh` - Test Cloud Build configurations locally before submission

## License
MIT License
