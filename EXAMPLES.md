# NiA-Cluster Examples

This directory contains example scripts demonstrating various features of NiA-Cluster.

## Basic Examples

### 1. Simple Network Scan

```python
import asyncio
from nia_cluster import ClusterManager

async def main():
    manager = ClusterManager()
    await manager.initialize()
    
    # Scan for network resources
    results = await manager.scan_network()
    
    print(f"WiFi Networks: {len(results['wifi_networks'])}")
    print(f"Bluetooth Devices: {len(results['bluetooth_devices'])}")
    print(f"ESP-32 Devices: {len(results['esp32_devices'])}")
    
    await manager.shutdown()

asyncio.run(main())
```

### 2. WiFi Connection with Auto-Reconnect

```python
import asyncio
from nia_cluster import WiFiManager

async def main():
    wifi = WiFiManager()
    
    # Connect to WiFi with auto-reconnect enabled
    success = await wifi.connect(
        ssid="MyNetwork",
        password="password123",
        auto_reconnect=True
    )
    
    if success:
        print(f"Connected to: {wifi.get_current_network()}")
    else:
        print("Connection failed")

asyncio.run(main())
```

### 3. Bluetooth Cluster Sharing

```python
import asyncio
from nia_cluster import BluetoothManager

async def main():
    bt = BluetoothManager()
    
    # Scan for devices
    devices = await bt.scan_devices(timeout=10)
    print(f"Found {len(devices)} devices")
    
    # Connect to a device with auto-reconnect
    if devices:
        device = devices[0]
        success = await bt.connect(device['address'], auto_reconnect=True)
        
        if success:
            print(f"Connected to {device['name']}")
            
            # Send data
            await bt.send_data(device['address'], b"Hello from NiA-Cluster")

asyncio.run(main())
```

### 4. PortmanAI Monitoring

```python
import asyncio
from nia_cluster import PortmanAI

async def main():
    portman = PortmanAI()
    
    # Start monitoring (non-blocking)
    asyncio.create_task(portman.start_monitoring())
    
    # Wait a bit for data collection
    await asyncio.sleep(10)
    
    # Get active ports
    ports = portman.get_all_active_ports()
    print(f"Active ports: {len(ports)}")
    
    # Analyze specific port
    health = portman.analyze_port_health(80)
    print(f"Port 80 health: {health['health_score']}")
    
    # Get recommendations
    recommendations = portman.get_switch_recommendations()
    for rec in recommendations:
        print(f"  - {rec}")
    
    portman.stop_monitoring()

asyncio.run(main())
```

### 5. JessicaAI Security

```python
import asyncio
from nia_cluster import JessicaAI

async def main():
    jessica = JessicaAI()
    jessica.initialize_voice_control()
    
    # Start security monitoring (non-blocking)
    asyncio.create_task(jessica.start_security_monitoring())
    
    # Run security scan
    print("Running security scan...")
    results = await jessica.run_security_scan()
    print(f"Threats found: {results['threats_found']}")
    
    # Process voice command
    result = await jessica.process_voice_command("status")
    print(f"Command result: {result}")
    
    # Get security status
    status = jessica.get_security_status()
    print(f"Threat level: {status['threat_level']}")
    
    jessica.stop_security_monitoring()

asyncio.run(main())
```

### 6. ESP-32 Communication

```python
import asyncio
from nia_cluster import ESP32Manager

def main():
    esp32 = ESP32Manager()
    
    # Scan for devices
    devices = esp32.scan_devices()
    print(f"Found {len(devices)} ESP-32 devices")
    
    if devices:
        port = devices[0]['port']
        
        # Connect
        if esp32.connect(port):
            print(f"Connected to {port}")
            
            # Send command
            response = esp32.send_command(port, "STATUS?")
            print(f"Response: {response}")
            
            # Disconnect
            esp32.disconnect(port)

if __name__ == "__main__":
    main()
```

### 7. Complete Cluster Setup

```python
import asyncio
from nia_cluster import ClusterManager

async def main():
    manager = ClusterManager()
    await manager.initialize()
    
    # Connect to WiFi
    print("Connecting to WiFi...")
    await manager.wifi.connect("MyNetwork", "password123", auto_reconnect=True)
    
    # Enable cluster mode
    print("Enabling cluster mode...")
    await manager.enable_cluster_mode("share")
    
    # Start monitoring
    print("Starting monitoring systems...")
    # (Already started during initialization)
    
    # Get status
    status = manager.get_status()
    print(f"\nCluster Status:")
    print(f"  Mode: {status['cluster_mode']}")
    print(f"  WiFi: {status['wifi']['current_network']}")
    print(f"  Threat Level: {status['jessica']['threat_level']}")
    
    # Keep running for a while
    await asyncio.sleep(30)
    
    # Shutdown
    await manager.shutdown()

asyncio.run(main())
```

### 8. SSH Key-Based Connection

```python
import asyncio
from nia_cluster import SSHManager

async def main():
    ssh = SSHManager()
    
    # Generate SSH key pair if needed
    ssh.generate_key_pair("nia_cluster_key")
    
    # Connect using key authentication
    success = await ssh.connect(
        host="192.168.1.100",
        username="admin",
        key_path="~/.ssh/nia_cluster_key"
    )
    
    if success:
        print("Connected via SSH")
        
        # Execute command
        result = ssh.execute_command("admin@192.168.1.100:22", "uptime")
        print(f"Output: {result['stdout']}")
        
        # Disconnect
        ssh.disconnect("admin@192.168.1.100:22")

asyncio.run(main())
```

### 9. VLAN Configuration

```python
from nia_cluster import VLANManager

def main():
    vlan = VLANManager()
    
    # Create VLAN
    if vlan.create_vlan(100, "eth0", "production"):
        print("VLAN 100 created")
        
        # Assign IP address
        if vlan.assign_ip(100, "192.168.100.1", "255.255.255.0"):
            print("IP assigned to VLAN 100")
    
    # List VLANs
    vlans = vlan.list_vlans()
    for v in vlans:
        print(f"VLAN {v['id']}: {v['name']} on {v['interface']}")

if __name__ == "__main__":
    main()
```

### 10. Custom Voice Commands

```python
import asyncio
from nia_cluster import JessicaAI

async def custom_command_handler(text: str) -> str:
    """Custom voice command handler"""
    return f"Custom command executed: {text}"

async def main():
    jessica = JessicaAI()
    jessica.initialize_voice_control()
    
    # Register custom command
    jessica.register_voice_command("custom", custom_command_handler)
    
    # Process custom command
    result = await jessica.process_voice_command("custom action")
    print(result)

asyncio.run(main())
```

## Advanced Examples

See the `examples/advanced/` directory for more complex usage scenarios including:
- Multi-node cluster setup
- Custom security policies
- Integration with external systems
- Advanced monitoring and alerting
