# NiA-Cluster
internal wifi ble esp clustering manager with portcontroll and security

## Docker Cluster Management

The `dockerfile-cluster.py` script provides an easy way to manage Docker containers for the NiA-Cluster system.

### Quick Start

1. **Initialize the cluster configuration:**
   ```bash
   python3 dockerfile-cluster.py init
   ```

2. **Generate Docker files:**
   ```bash
   python3 dockerfile-cluster.py generate
   ```
   This creates:
   - `Dockerfile.manager` - Container for the cluster manager
   - `Dockerfile.esp-controller` - Container for ESP WiFi/BLE controller
   - `docker-compose.yml` - Orchestration configuration
   - `cluster-config.json` - Cluster configuration

3. **Build and start the cluster:**
   ```bash
   python3 dockerfile-cluster.py build
   python3 dockerfile-cluster.py start
   ```

### Available Commands

- `init` - Initialize cluster configuration
- `generate` - Generate Docker files (Dockerfiles and docker-compose.yml)
- `build` - Build Docker images
- `start` - Start the cluster
- `stop` - Stop the cluster
- `restart` - Restart the cluster
- `status` - Show cluster status
- `logs` - Show service logs (use `-f` to follow)

### Configuration

Edit `cluster-config.json` to customize:
- Network settings (subnet, driver)
- Service ports
- Environment variables
- Volumes

### Architecture

The cluster consists of two main services:

1. **Manager Service** (port 8080, 1883)
   - HTTP API for cluster management
   - MQTT broker for device communication
   - Security and authentication

2. **ESP Controller Service** (port 9000)
   - WiFi/BLE communication with ESP devices
   - Port control management
   - Device discovery and registration

### Requirements

- Python 3.7+
- Docker
- Docker Compose

