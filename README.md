# NiA-Cluster

Advanced internal WiFi BLE ESP clustering manager with port control and security features.

## Overview

NiA-Cluster is a comprehensive networking cluster management tool that provides:

- **Multi-Protocol Support**: WiFi, Bluetooth LE, SSH, Telnet, FTP
- **ESP-32 Integration**: Direct communication with ESP32 devices
- **VLAN Management**: Advanced network segmentation
- **Cross-Platform**: Works on Windows, Linux, and macOS
- **Auto-Reconnect**: Seamless reconnection without password re-entry using SSH keys
- **AI-Powered Monitoring**: 
  - **PortmanAI**: Intelligent port monitoring and management
  - **JessicAI**: Security monitoring and voice command control
- **Multi-Channel Communication**: Email, SMS, and phone notifications

## Features

### Network Management
- WiFi connectivity with automatic reconnection
- Bluetooth Low Energy (BLE) for cluster sharing
- SSH with key-based authentication (no password required after setup)
- Optional Telnet and FTP services
- VLAN support for network segmentation

### ESP-32 Integration
- Serial communication with ESP32 devices
- Device configuration and management
- Firmware flashing support
- Multi-device cluster coordination

### AI Services

#### PortmanAI
- Real-time port monitoring
- Switch and router management
- Traffic pattern analysis
- Anomaly detection
- Performance optimization recommendations

#### JessicAI
- Security threat detection and monitoring
- Voice command recognition and control
- Near-device voice activation
- Multi-channel notifications (email, SMS, phone)
- Automated security responses

### Security
- End-to-end encryption
- SSH key-based authentication
- Secure key storage
- Access control management
- Automated security monitoring

## Installation

### Requirements
- Python 3.8 or higher
- pip (Python package manager)

### Install from source

```bash
git clone https://github.com/NaTo1000/NiA-Cluster.git
cd NiA-Cluster
pip install -e .
```

### Install dependencies

```bash
pip install -r requirements.txt
```

For voice control features:
```bash
pip install -e ".[voice]"
```

## Quick Start

### 1. Initialize Configuration

```bash
nia-cluster config --init
```

This creates a default configuration file at `config/cluster.yaml`.

### 2. Edit Configuration

Edit `config/cluster.yaml` to match your environment:

```yaml
network:
  wifi:
    ssid: "YourNetworkName"
    interface: "wlan0"  # or "Wi-Fi" on Windows
  
esp32:
  port: "/dev/ttyUSB0"  # or "COM3" on Windows
```

### 3. Start the Cluster

```bash
nia-cluster start --config config/cluster.yaml
```

### 4. Check Status

In another terminal:

```bash
nia-cluster status
```

## Configuration

See [config/cluster.example.yaml](config/cluster.example.yaml) for a complete configuration example.

### Key Configuration Sections

- **cluster**: General cluster settings and auto-reconnect behavior
- **network**: WiFi, Bluetooth, SSH, Telnet, FTP configuration
- **esp32**: ESP32 device connection settings
- **vlan**: VLAN interface configuration
- **ai**: PortmanAI and JessicAI settings
- **security**: Encryption and key management

## Usage Examples

### Start with Custom Configuration

```bash
nia-cluster start --config /path/to/config.yaml
```

### View Current Configuration

```bash
nia-cluster config --show
```

### Enable Verbose Logging

```bash
nia-cluster start --verbose
```

## Platform-Specific Notes

### Linux
- May require sudo for network operations
- Default WiFi interface: `wlan0`
- Default ESP32 port: `/dev/ttyUSB0`

### Windows
- WiFi interface names vary by adapter
- ESP32 port typically: `COM3` or similar
- Some features may require administrator privileges

### macOS
- WiFi interface usually: `en0`
- ESP32 port typically: `/dev/tty.usbserial-*`
- May require granting terminal permissions

## Development

### Project Structure

```
NiA-Cluster/
├── src/nia_cluster/
│   ├── __init__.py
│   ├── core.py           # Main cluster manager
│   ├── cli.py            # Command-line interface
│   ├── network/          # Network management
│   ├── ai/               # PortmanAI and JessicAI
│   ├── security/         # Security and encryption
│   ├── esp32/            # ESP32 integration
│   └── config/           # Configuration management
├── config/               # Configuration files
├── docs/                 # Documentation
├── setup.py              # Package setup
└── requirements.txt      # Dependencies
```

### Running Tests

```bash
pip install -e ".[dev]"
pytest
```

## Security Considerations

1. **SSH Keys**: Store private keys securely (default: `~/.nia-cluster/keys/`)
2. **Configuration Files**: Protect config files containing sensitive data
3. **Network Security**: Use encryption for all network communications
4. **Access Control**: Limit authorized users and devices

## Troubleshooting

### Cannot connect to WiFi
- Check interface name in configuration
- Verify WiFi credentials
- Ensure proper permissions

### ESP32 not detected
- Verify USB connection
- Check port name in configuration
- Install appropriate USB drivers

### Voice control not working
- Install voice dependencies: `pip install -e ".[voice]"`
- Check microphone permissions
- Enable voice control in configuration

## Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues.

## License

MIT License - See LICENSE file for details

## Contact

For questions or support, please open an issue on GitHub.
