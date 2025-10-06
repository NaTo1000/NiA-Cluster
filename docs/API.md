# API Documentation

## Core API

### ClusterManager

Main entry point for the NiA-Cluster system.

```python
from nia_cluster import ClusterManager

# Initialize
manager = ClusterManager(config_path="/path/to/config.yaml")

# Start all services
manager.start()

# Get status
status = manager.get_status()

# Stop all services
manager.stop()
```

#### Methods

**`__init__(config_path: Optional[str] = None)`**
- Initialize the cluster manager
- Loads configuration from specified path or default locations

**`start()`**
- Start all enabled cluster services
- Initializes network, AI, and security components

**`stop()`**
- Stop all running services
- Performs cleanup and resource release

**`get_status() -> Dict[str, Any]`**
- Returns current status of all components
- Includes network, AI, and security status

---

## Configuration API

### ConfigManager

Manages system configuration.

```python
from nia_cluster.config import ConfigManager

# Initialize
config = ConfigManager("/path/to/config.yaml")

# Get value
wifi_enabled = config.get('network.wifi.enabled', True)

# Set value
config.set('network.wifi.ssid', 'MyNetwork')

# Save configuration
config.save()
```

#### Methods

**`get(key_path: str, default: Any = None) -> Any`**
- Get configuration value using dot notation
- Returns default if key not found

**`set(key_path: str, value: Any)`**
- Set configuration value using dot notation

**`save(path: Optional[str] = None)`**
- Save current configuration to file

---

## Network API

### NetworkManager

Manages network connections.

```python
from nia_cluster.config import ConfigManager
from nia_cluster.network import NetworkManager

config = ConfigManager()
network = NetworkManager(config)

# Start network services
network.start()

# Get status
status = network.get_status()

# Reconnect specific service
network.reconnect("wifi")

# Stop services
network.stop()
```

#### Methods

**`start()`**
- Start all enabled network services

**`stop()`**
- Stop all network services

**`get_status() -> Dict[str, Any]`**
- Get status of all network services

**`reconnect(service: str)`**
- Reconnect a specific network service

---

## AI API

### PortmanAI

Port monitoring and management.

```python
from nia_cluster.config import ConfigManager
from nia_cluster.ai import PortmanAI

config = ConfigManager()
portman = PortmanAI(config)

# Start monitoring
portman.start_monitoring()

# Get status
status = portman.get_status()

# Get port info
port_info = portman.get_port_info("eth0")

# Analyze traffic
analysis = portman.analyze_traffic("eth0")

# Stop monitoring
portman.stop_monitoring()
```

#### Methods

**`start_monitoring()`**
- Start port monitoring in background thread

**`stop_monitoring()`**
- Stop port monitoring

**`get_status() -> Dict[str, Any]`**
- Get current monitoring status

**`get_port_info(port_id: str) -> Dict[str, Any]`**
- Get information about specific port

**`list_ports() -> List[str]`**
- List all monitored ports

**`analyze_traffic(port_id: str) -> Dict[str, Any]`**
- Analyze traffic patterns for a port

### JessicAI

Security and voice control.

```python
from nia_cluster.config import ConfigManager
from nia_cluster.ai import JessicAI

config = ConfigManager()
jessica = JessicAI(config)

# Start services
jessica.start()

# Get status
status = jessica.get_status()

# Send notification
jessica.send_notification("Alert message", channel="email")

# Process voice command
response = jessica.process_voice_command("status")

# Handle security event
jessica.handle_security_event({"type": "intrusion", "source": "192.168.1.100"})

# Stop services
jessica.stop()
```

#### Methods

**`start()`**
- Start JessicAI services including voice control

**`stop()`**
- Stop all services

**`get_status() -> Dict[str, Any]`**
- Get current status

**`send_notification(message: str, channel: str = "email")`**
- Send notification through specified channel

**`process_voice_command(command: str) -> Optional[str]`**
- Process voice command and return response

**`detect_security_threat(event: Dict[str, Any]) -> bool`**
- Analyze event for security threats

**`handle_security_event(event: Dict[str, Any])`**
- Handle detected security event

---

## Security API

### SecurityManager

Security and encryption management.

```python
from nia_cluster.config import ConfigManager
from nia_cluster.security import SecurityManager

config = ConfigManager()
security = SecurityManager(config)

# Initialize security
security.initialize()

# Get status
status = security.get_status()

# Encrypt data
encrypted = security.encrypt_data(b"sensitive data")

# Decrypt data
decrypted = security.decrypt_data(encrypted)

# Verify SSH key
is_valid = security.verify_ssh_key("ssh-rsa AAAAB3...")

# Authorize key for user
security.authorize_key("ssh-rsa AAAAB3...", "username")
```

#### Methods

**`initialize()`**
- Initialize security components and keys

**`get_status() -> Dict[str, Any]`**
- Get security status

**`encrypt_data(data: bytes) -> bytes`**
- Encrypt data

**`decrypt_data(data: bytes) -> bytes`**
- Decrypt data

**`verify_ssh_key(public_key: str) -> bool`**
- Verify SSH public key

**`authorize_key(public_key: str, user: str)`**
- Authorize SSH key for user

---

## ESP32 API

### ESP32Manager

ESP32 device management.

```python
from nia_cluster.config import ConfigManager
from nia_cluster.esp32 import ESP32Manager

config = ConfigManager()
esp32 = ESP32Manager(config)

# Connect to device
if esp32.connect():
    # Send command
    response = esp32.send_command("AT+VERSION")
    
    # Get status
    status = esp32.get_status()
    
    # Configure device
    esp32.configure_device("esp32-01", {"mode": "station"})
    
    # Flash firmware
    esp32.flash_firmware("/path/to/firmware.bin")
    
    # Disconnect
    esp32.disconnect()
```

#### Methods

**`connect() -> bool`**
- Connect to ESP32 device

**`disconnect()`**
- Disconnect from device

**`send_command(command: str) -> Optional[str]`**
- Send command to device

**`get_status() -> Dict[str, Any]`**
- Get device status

**`list_devices() -> List[str]`**
- List connected devices

**`configure_device(device_id: str, config: Dict[str, Any])`**
- Configure device

**`flash_firmware(firmware_path: str) -> bool`**
- Flash firmware to device

---

## CLI Reference

### Commands

**`nia-cluster start [OPTIONS]`**
- Start cluster services
- Options:
  - `--config PATH`: Configuration file path
  - `--verbose`: Enable verbose logging

**`nia-cluster stop`**
- Stop running cluster instance

**`nia-cluster status [OPTIONS]`**
- Get cluster status
- Options:
  - `--config PATH`: Configuration file path

**`nia-cluster config [OPTIONS]`**
- Manage configuration
- Options:
  - `--init`: Initialize default configuration
  - `--show`: Display current configuration
  - `--config PATH`: Configuration file path

### Examples

```bash
# Start with default configuration
nia-cluster start

# Start with custom configuration
nia-cluster start --config /etc/nia-cluster/config.yaml

# Initialize configuration
nia-cluster config --init

# Show current configuration
nia-cluster config --show

# Check status
nia-cluster status --verbose
```
