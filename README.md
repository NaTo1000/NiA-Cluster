# NiA-Cluster
internal wifi ble esp clustering manager with portcontroll and security

## Quick Start

### Using Docker Compose

Start the cluster with one relay server and two nodes:

```bash
docker compose up
```

This will start:
- **relay**: Relay server listening on port 4040
- **node1**: Cluster node in "myfleet" with BLE enabled
- **node2**: Cluster node in "myfleet"

### Manual Usage

Run relay server:
```bash
python main.py --mode relay-server --host 0.0.0.0 --port 4040
```

Run a cluster node:
```bash
python main.py --mode node --cluster myfleet --node node1 --relay-host localhost --relay-port 4040 --lan-port 5001 --enable-ble
```

## Configuration

The docker-compose.yml file defines:
- **relay**: Central relay server for cluster communication
- **node1**: Cluster node with BLE support enabled
- **node2**: Standard cluster node

All nodes connect to the relay server for coordinated operations.

