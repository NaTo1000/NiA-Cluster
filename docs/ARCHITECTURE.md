# NiA-Cluster Architecture

## System Overview

NiA-Cluster is designed as a modular, extensible networking cluster management system. The architecture follows a layered approach with clear separation of concerns.

## Core Components

### 1. ClusterManager (core.py)
The central orchestration component that:
- Coordinates all subsystems
- Manages lifecycle of services
- Provides unified status interface
- Handles inter-component communication

### 2. ConfigManager (config/)
Configuration management system that:
- Loads configuration from YAML files
- Supports multiple configuration sources
- Provides dot-notation access to settings
- Handles configuration persistence

### 3. NetworkManager (network/)
Handles all network protocols:
- WiFi connectivity and management
- Bluetooth Low Energy (BLE) operations
- SSH server with key-based auth
- Optional Telnet and FTP services
- VLAN configuration and management
- Auto-reconnection logic

### 4. PortmanAI (ai/portman.py)
Intelligent port monitoring system:
- Background monitoring thread
- Port status tracking
- Traffic analysis
- Performance metrics
- Anomaly detection (ML-ready)

### 5. JessicAI (ai/jessica.py)
Security and voice control system:
- Security threat detection
- Voice command processing
- Multi-channel notifications
- Near-device activation
- Event handling and response

### 6. SecurityManager (security/)
Security infrastructure:
- SSH key generation and management
- Encryption/decryption services
- Key storage with proper permissions
- Authentication and authorization

### 7. ESP32Manager (esp32/)
ESP32 device integration:
- Serial communication
- Device configuration
- Firmware flashing
- Multi-device coordination

## Data Flow

```
User Commands (CLI)
        ↓
   ClusterManager
        ↓
   ┌────┴────┬────────┬──────────┬──────────┐
   ↓         ↓        ↓          ↓          ↓
Network   PortmanAI  JessicAI  Security  ESP32
Manager              
   ↓         ↓        ↓          ↓          ↓
WiFi/BLE   Ports   Voice/Sec  Keys/Enc   Serial
```

## Threading Model

- **Main Thread**: CLI and user interaction
- **Network Thread**: Connection management and auto-reconnect
- **PortmanAI Thread**: Continuous port monitoring
- **JessicAI Thread**: Voice processing and security monitoring

## Configuration System

Configuration is hierarchical and supports:
- Default values (in code)
- System-wide config (/etc/nia-cluster/config.yaml)
- User config (~/.nia-cluster/config.yaml)
- Project config (./config/cluster.yaml)
- Command-line overrides

## Security Model

1. **Key-Based Authentication**: SSH keys stored securely
2. **Encryption**: All network traffic encrypted by default
3. **Least Privilege**: Minimal permissions required
4. **Secure Storage**: Keys stored with 700/600 permissions

## Extensibility Points

### Adding New Protocols
Extend NetworkManager with new protocol handlers:
```python
def _start_new_protocol(self):
    # Implementation
    pass
```

### Adding AI Features
Extend AI modules with new capabilities:
```python
class CustomAI:
    def analyze(self, data):
        # ML/AI processing
        pass
```

### Custom Security Policies
Implement SecurityPolicy interface:
```python
class CustomPolicy(SecurityPolicy):
    def evaluate(self, event):
        # Policy logic
        pass
```

## Performance Considerations

1. **Background Processing**: Heavy operations run in threads
2. **Lazy Loading**: Components initialized on demand
3. **Resource Cleanup**: Proper shutdown handling
4. **Efficient Polling**: Configurable monitoring intervals

## Platform Abstraction

Platform-specific code is isolated:
- Network interface detection
- Serial port naming
- File permissions
- Process management

## Error Handling

- Graceful degradation when services fail
- Comprehensive logging at all levels
- Exception handling with recovery
- User-friendly error messages

## Future Enhancements

1. **Distributed Clustering**: Multi-node coordination
2. **Machine Learning**: Advanced anomaly detection
3. **Web Interface**: Browser-based management
4. **Plugin System**: Third-party extensions
5. **Cloud Integration**: Remote management
