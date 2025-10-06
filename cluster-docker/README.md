# NiA-Cluster Docker Setup

This directory contains the Docker configuration for the NiA-Cluster Management Suite.

## Files

- **Dockerfile**: Container image definition for the cluster GUI application
- **docker-compose.yml**: Docker Compose orchestration configuration
- **cluster_gui_suite.py**: Main Python application for cluster management
- **requirements.txt**: Python dependencies

## Quick Start

### Build the Docker image

```bash
cd cluster-docker
docker compose build --progress=plain
```

### Run the application

```bash
docker compose up
```

The application will be available on the following ports:
- Port 8080: Control interface
- Port 8443: Secure interface  
- Port 5000: API interface

### Stop the application

```bash
docker compose down
```

## Features

The NiA-Cluster Management Suite provides:

- **Cluster Node Management**: Add, remove, and monitor WiFi, BLE, and ESP nodes
- **Real-time Monitoring**: Track node status and connectivity
- **Port Control**: Manage network ports for cluster communication
- **Security**: Built-in authentication and encryption support
- **GUI Interface**: User-friendly Tkinter-based management interface

## Configuration

Application data and logs are stored in the following directories:
- `./data/`: Configuration files and node data
- `./logs/`: Application logs

These directories are mounted as volumes and persist between container restarts.

## Requirements

- Docker Engine 20.10+
- Docker Compose 2.0+

## Architecture

The cluster manager supports three types of nodes:
- **WiFi**: Standard WiFi-based network nodes
- **BLE**: Bluetooth Low Energy devices
- **ESP**: ESP32/ESP8266 microcontroller nodes

Each node can be managed through the GUI interface, with support for:
- Connection management
- Status monitoring
- Security configuration
- Port control

## Development

To modify the application:

1. Edit `cluster_gui_suite.py` with your changes
2. Rebuild the container: `docker compose build`
3. Restart the application: `docker compose up`

## Troubleshooting

If you encounter issues:

1. Check the logs: `docker compose logs`
2. Verify ports are not in use: `netstat -an | grep -E '8080|8443|5000'`
3. Ensure Docker has necessary permissions for network operations
4. Review application logs in `./logs/` directory

## Security Notes

The container runs with elevated privileges (NET_ADMIN, SYS_ADMIN) to manage network interfaces. In production environments, consider:

- Using specific capabilities instead of privileged mode
- Implementing proper authentication mechanisms
- Enabling TLS/SSL for secure communication
- Regular security updates and monitoring
