# NiA-Cluster

Advanced networking cluster tool with AI-powered monitoring and security features.

## Overview

NiA-Cluster is a comprehensive networking solution that provides:

- **Multi-Protocol Support**: WiFi, Bluetooth/BLE, Telnet, FTP, SSH
- **Hardware Integration**: ESP-32 device management
- **Network Segmentation**: VLAN configuration and management
- **Cross-Platform**: Windows, Linux, and macOS support
- **Cluster Sharing**: Seamless device clustering via Bluetooth/WiFi with automatic reconnection
- **SSH Key Authentication**: Secure passwordless connections
- **PortmanAI**: Intelligent port monitoring and switch management
- **JessicaAI**: Advanced security monitoring with voice command control
- **Communication Integration**: Email, SMS, and phone notifications

## Features

### Network Management
- **WiFi Manager**: Scan, connect, and manage WiFi networks across platforms
- **Bluetooth Manager**: BLE device discovery and communication with auto-reconnect
- **SSH Manager**: Secure connections with key-based authentication
- **Telnet Manager**: Legacy device support
- **FTP Manager**: File transfer operations
- **VLAN Manager**: Network segmentation and VLAN configuration

### Hardware Support
- **ESP-32 Integration**: Serial communication, firmware flashing, and device management
- **Cross-Platform**: Native support for Linux, Windows, and macOS

### AI Systems

#### PortmanAI
Intelligent port and switch monitoring system that provides:
- Real-time port monitoring
- Traffic pattern analysis
- Health scoring for ports
- Anomaly detection
- Configuration recommendations

#### JessicaAI
Advanced security and voice control system featuring:
- Continuous security monitoring
- Threat detection and alerting
- Voice command processing
- Email, SMS, and phone notifications
- Proximity-based device detection
- Automated security scans

### Cluster Mode
- **Share Mode**: Connect devices via Bluetooth/WiFi
- **Master/Node Architecture**: Hierarchical cluster organization
- **Auto-Reconnect**: Seamless reconnection without passwords using SSH keys
- **Multi-Device Coordination**: Manage multiple devices as a single cluster

## Installation

### From Source

```bash
git clone https://github.com/NaTo1000/NiA-Cluster.git
cd NiA-Cluster
pip install -e .
```

### Using pip

```bash
pip install nia-cluster
```

## Quick Start

### 1. Initialize the Cluster

```python
from nia_cluster import ClusterManager

# Create cluster manager
manager = ClusterManager()

# Initialize components
await manager.initialize()
```

### 2. Scan Network

```bash
# Using CLI
nia-cluster scan

# Using Python
results = await manager.scan_network()
print(f"Found {len(results['wifi_networks'])} WiFi networks")
print(f"Found {len(results['bluetooth_devices'])} Bluetooth devices")
```

### 3. Connect to WiFi

```bash
# Using CLI
nia-cluster wifi MyNetwork -p password123

# Using Python
await manager.wifi.connect("MyNetwork", "password123", auto_reconnect=True)
```

### 4. Enable Cluster Mode

```bash
# Using CLI
nia-cluster cluster enable share

# Using Python
await manager.enable_cluster_mode("share")
```

### 5. Monitor Ports with PortmanAI

```bash
# List active ports
nia-cluster portman ports

# Check port health
nia-cluster portman health --port 80

# Get recommendations
nia-cluster portman recommendations
```

### 6. Security with JessicaAI

```bash
# Run security scan
nia-cluster jessica scan

# Generate security report
nia-cluster jessica report

# Process voice command
nia-cluster jessica voice --command "status"
```

## Configuration

Create a configuration file at `~/.nia-cluster/config.yaml`:

```yaml
cluster:
  mode: standalone
  auto_reconnect: true

wifi:
  auto_connect: true
  preferred_networks:
    - ssid: "MyNetwork"
      password: "password123"

portman:
  monitoring_interval: 5
  alerts_enabled: true

jessica:
  voice_enabled: true
  security_monitoring: true
  threat_notification: true
```

See `config.example.yaml` for a complete configuration example.

## CLI Usage

### General Commands

```bash
# Show cluster status
nia-cluster status

# Scan for all network resources
nia-cluster scan

# Enable verbose logging
nia-cluster -v status
```

### WiFi Operations

```bash
# Connect to WiFi network
nia-cluster wifi MyNetwork -p password123
```

### Bluetooth Operations

```bash
# Scan for Bluetooth devices
nia-cluster bluetooth -t 15
```

### Cluster Operations

```bash
# Enable cluster sharing mode
nia-cluster cluster enable share

# Join existing cluster
nia-cluster cluster join AA:BB:CC:DD:EE:FF
```

### ESP-32 Operations

```bash
# Scan for ESP-32 devices
nia-cluster esp32 scan

# Connect to ESP-32
nia-cluster esp32 connect --port /dev/ttyUSB0
```

### PortmanAI Commands

```bash
# List all active ports
nia-cluster portman ports

# Analyze port health
nia-cluster portman health --port 8080

# Get switch recommendations
nia-cluster portman recommendations
```

### JessicaAI Commands

```bash
# Run security scan
nia-cluster jessica scan

# Generate security report
nia-cluster jessica report

# Process voice command
nia-cluster jessica voice --command "run security scan"
```

## Python API

### Basic Usage

```python
import asyncio
from nia_cluster import ClusterManager

async def main():
    # Create and initialize cluster
    manager = ClusterManager()
    await manager.initialize()
    
    # Scan network
    results = await manager.scan_network()
    
    # Connect to WiFi
    await manager.wifi.connect("MyNetwork", "password123")
    
    # Enable cluster mode
    await manager.enable_cluster_mode("share")
    
    # Get status
    status = manager.get_status()
    print(f"Cluster mode: {status['cluster_mode']}")
    
    # Shutdown
    await manager.shutdown()

asyncio.run(main())
```

### Advanced Examples

#### Port Monitoring

```python
# Start port monitoring
await manager.portman.start_monitoring()

# Get port information
port_info = manager.portman.get_port_info(80)

# Analyze port health
health = manager.portman.analyze_port_health(8080)
print(f"Health score: {health['health_score']}")
```

#### Security Monitoring

```python
# Initialize voice control
manager.jessica.initialize_voice_control()

# Start security monitoring
await manager.jessica.start_security_monitoring()

# Run security scan
results = await manager.jessica.run_security_scan()

# Process voice command
result = await manager.jessica.process_voice_command("status")
```

#### ESP-32 Integration

```python
# Scan for ESP-32 devices
devices = manager.esp32.scan_devices()

# Connect to device
manager.esp32.connect("/dev/ttyUSB0", baudrate=115200)

# Send command
response = manager.esp32.send_command("/dev/ttyUSB0", "GET:STATUS")

# Flash firmware
manager.esp32.flash_firmware("/dev/ttyUSB0", "firmware.bin")
```

## Architecture

```
NiA-Cluster
├── Network Layer
│   ├── WiFi Manager (cross-platform)
│   ├── Bluetooth Manager (BLE with auto-reconnect)
│   ├── SSH Manager (key-based auth)
│   ├── Telnet Manager
│   ├── FTP Manager
│   └── VLAN Manager
├── Hardware Layer
│   └── ESP-32 Manager (serial communication & flashing)
├── AI Layer
│   ├── PortmanAI (port monitoring & analysis)
│   └── JessicaAI (security & voice control)
└── Cluster Layer
    └── Cluster Manager (orchestration)
```

## Security

- **SSH Key Authentication**: Passwordless secure connections
- **Encrypted Communication**: All cluster communication is encrypted
- **Threat Detection**: Real-time security monitoring with JessicaAI
- **Access Control**: Device whitelisting and authentication
- **Audit Logging**: Comprehensive security event logging

## Requirements

- Python 3.8 or higher
- Platform-specific network tools:
  - Linux: NetworkManager, iproute2
  - Windows: netsh, PowerShell
  - macOS: networksetup

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License - see LICENSE file for details.

## Support

For issues, questions, or contributions, please visit:
https://github.com/NaTo1000/NiA-Cluster

## Acknowledgments

Developed by NiA for advanced network clustering and management.
