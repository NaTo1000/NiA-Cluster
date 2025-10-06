# NiA-Cluster
internal wifi ble esp clustering manager with portcontroll and security

## Quick Start with Docker

The easiest way to run the NiA-Cluster management suite is using Docker:

```bash
cd cluster-docker
docker compose build --progress=plain
docker compose up
```

The cluster GUI will be available on:
- Port 8080: Control interface
- Port 8443: Secure interface
- Port 5000: API interface

For detailed Docker setup instructions, see [cluster-docker/README.md](cluster-docker/README.md).

## Features

- **Cluster Node Management**: Manage WiFi, BLE, and ESP nodes
- **Real-time Monitoring**: Track node status and connectivity
- **Port Control**: Network port management for cluster communication
- **Security**: Built-in authentication and encryption support
- **GUI Interface**: User-friendly management interface

## Repository Structure

```
.
├── cluster-docker/          # Docker setup for cluster management
│   ├── Dockerfile          # Container image definition
│   ├── docker-compose.yml  # Docker Compose configuration
│   ├── cluster_gui_suite.py # Main Python GUI application
│   ├── requirements.txt    # Python dependencies
│   └── README.md           # Docker setup documentation
└── setup.sh                # Quick setup script
```

## Development

To modify the cluster management application:

1. Edit files in the `cluster-docker/` directory
2. Rebuild the container: `docker compose build`
3. Restart the application: `docker compose up`

## License

This project is for internal use.

