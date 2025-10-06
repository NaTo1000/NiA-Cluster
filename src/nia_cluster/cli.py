"""
Command-line interface for NiA-Cluster
"""

import asyncio
import argparse
import logging
import sys
import json
from pathlib import Path

from .cluster.manager import ClusterManager


def setup_logging(level: str = "INFO"):
    """Configure logging"""
    log_level = getattr(logging, level.upper(), logging.INFO)
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


async def cmd_scan(manager: ClusterManager, args):
    """Scan for network resources"""
    print("Scanning network...")
    results = await manager.scan_network()
    
    print(f"\n=== Network Scan Results ===")
    print(f"WiFi Networks: {len(results['wifi_networks'])}")
    for net in results['wifi_networks'][:5]:  # Show first 5
        print(f"  - {net['ssid']} (Signal: {net['signal']})")
    
    print(f"\nBluetooth Devices: {len(results['bluetooth_devices'])}")
    for dev in results['bluetooth_devices'][:5]:
        print(f"  - {dev['name']} ({dev['address']})")
    
    print(f"\nESP-32 Devices: {len(results['esp32_devices'])}")
    for dev in results['esp32_devices']:
        print(f"  - {dev['port']}: {dev['description']}")


async def cmd_status(manager: ClusterManager, args):
    """Show cluster status"""
    status = manager.get_status()
    print("\n=== NiA-Cluster Status ===")
    print(f"Cluster Mode: {status['cluster_mode']}")
    print(f"Cluster Nodes: {status['cluster_nodes']}")
    print(f"WiFi Network: {status['wifi']['current_network'] or 'Not connected'}")
    print(f"Bluetooth Devices: {len(status['bluetooth']['connected_devices'])}")
    print(f"ESP-32 Devices: {len(status['esp32']['connected_devices'])}")
    print(f"SSH Connections: {len(status['ssh']['active_connections'])}")
    print(f"VLANs: {len(status['vlan']['configured_vlans'])}")
    print(f"\nPortmanAI: Monitoring {status['portman']['monitored_ports_count']} ports")
    print(f"JessicaAI: Threat Level - {status['jessica']['threat_level']}")


async def cmd_wifi_connect(manager: ClusterManager, args):
    """Connect to WiFi network"""
    print(f"Connecting to {args.ssid}...")
    success = await manager.wifi.connect(args.ssid, args.password, auto_reconnect=True)
    
    if success:
        print(f"Successfully connected to {args.ssid}")
    else:
        print(f"Failed to connect to {args.ssid}")


async def cmd_bluetooth_scan(manager: ClusterManager, args):
    """Scan for Bluetooth devices"""
    print("Scanning for Bluetooth devices...")
    devices = await manager.bluetooth.scan_devices(timeout=args.timeout)
    
    print(f"\nFound {len(devices)} device(s):")
    for dev in devices:
        print(f"  {dev['name']}: {dev['address']} (RSSI: {dev.get('rssi', 'N/A')})")


async def cmd_cluster_enable(manager: ClusterManager, args):
    """Enable cluster mode"""
    print(f"Enabling cluster mode: {args.mode}")
    await manager.enable_cluster_mode(args.mode)
    print("Cluster mode enabled")


async def cmd_cluster_join(manager: ClusterManager, args):
    """Join a cluster"""
    print(f"Joining cluster at {args.address}...")
    success = await manager.join_cluster(args.address)
    
    if success:
        print("Successfully joined cluster")
    else:
        print("Failed to join cluster")


async def cmd_portman(manager: ClusterManager, args):
    """PortmanAI operations"""
    if args.action == "ports":
        ports = manager.get_port_analysis()
        print(f"\n=== Active Ports ({len(ports)}) ===")
        for port in ports[:20]:  # Show first 20
            print(f"Port {port['port']}: {port['connections']} connections")
    
    elif args.action == "health":
        health = manager.portman.analyze_port_health(args.port)
        print(f"\n=== Port {args.port} Health ===")
        print(f"Health Score: {health.get('health_score', 'N/A')}")
        print(f"Status: {health.get('status', 'N/A')}")
        if health.get('issues'):
            print("Issues:")
            for issue in health['issues']:
                print(f"  - {issue}")
        if health.get('recommendations'):
            print("Recommendations:")
            for rec in health['recommendations']:
                print(f"  - {rec}")
    
    elif args.action == "recommendations":
        recommendations = manager.portman.get_switch_recommendations()
        print("\n=== Switch Recommendations ===")
        for rec in recommendations:
            print(f"  - {rec}")


async def cmd_jessica(manager: ClusterManager, args):
    """JessicaAI operations"""
    if args.action == "scan":
        print("Running security scan...")
        results = await manager.jessica.run_security_scan()
        print(f"\nScan completed at {results['timestamp']}")
        print(f"Threats found: {results['threats_found']}")
        if results.get('recommendations'):
            print("\nRecommendations:")
            for rec in results['recommendations']:
                print(f"  - {rec}")
    
    elif args.action == "report":
        report = manager.get_security_report()
        print(f"\n=== Security Report ===")
        print(f"Generated: {report['generated']}")
        print(f"Threat Level: {report['threat_level']}")
        print(f"Total Events: {len(report['events'])}")
        print(f"\nRecent Events:")
        for event in report['events'][-5:]:
            print(f"  [{event['severity']}] {event['type']}: {event['description']}")
    
    elif args.action == "voice":
        result = await manager.process_voice_command(args.command)
        print(f"\nCommand Result: {result}")


async def cmd_esp32(manager: ClusterManager, args):
    """ESP-32 operations"""
    if args.action == "scan":
        devices = manager.esp32.scan_devices()
        print(f"\n=== ESP-32 Devices ({len(devices)}) ===")
        for dev in devices:
            print(f"  {dev['port']}: {dev['description']}")
    
    elif args.action == "connect":
        success = manager.esp32.connect(args.port, args.baudrate)
        if success:
            print(f"Connected to {args.port}")
        else:
            print(f"Failed to connect to {args.port}")


def create_parser():
    """Create argument parser"""
    parser = argparse.ArgumentParser(
        description="NiA-Cluster - Advanced networking cluster tool",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # Scan command
    scan_parser = subparsers.add_parser("scan", help="Scan for network resources")
    
    # Status command
    status_parser = subparsers.add_parser("status", help="Show cluster status")
    
    # WiFi commands
    wifi_parser = subparsers.add_parser("wifi", help="WiFi operations")
    wifi_parser.add_argument("ssid", help="Network SSID")
    wifi_parser.add_argument("-p", "--password", help="Network password")
    
    # Bluetooth commands
    bt_parser = subparsers.add_parser("bluetooth", help="Bluetooth operations")
    bt_parser.add_argument("-t", "--timeout", type=float, default=10.0, help="Scan timeout")
    
    # Cluster commands
    cluster_parser = subparsers.add_parser("cluster", help="Cluster operations")
    cluster_sub = cluster_parser.add_subparsers(dest="cluster_cmd")
    
    enable_parser = cluster_sub.add_parser("enable", help="Enable cluster mode")
    enable_parser.add_argument("mode", choices=["share", "master", "node"], 
                              help="Cluster mode")
    
    join_parser = cluster_sub.add_parser("join", help="Join cluster")
    join_parser.add_argument("address", help="Master node address")
    
    # PortmanAI commands
    portman_parser = subparsers.add_parser("portman", help="PortmanAI operations")
    portman_parser.add_argument("action", 
                               choices=["ports", "health", "recommendations"],
                               help="Action to perform")
    portman_parser.add_argument("--port", type=int, help="Port number for health check")
    
    # JessicaAI commands
    jessica_parser = subparsers.add_parser("jessica", help="JessicaAI operations")
    jessica_parser.add_argument("action", choices=["scan", "report", "voice"],
                               help="Action to perform")
    jessica_parser.add_argument("--command", help="Voice command")
    
    # ESP-32 commands
    esp32_parser = subparsers.add_parser("esp32", help="ESP-32 operations")
    esp32_parser.add_argument("action", choices=["scan", "connect"],
                             help="Action to perform")
    esp32_parser.add_argument("--port", help="Serial port")
    esp32_parser.add_argument("--baudrate", type=int, default=115200,
                             help="Baud rate")
    
    return parser


async def async_main():
    """Async main function"""
    parser = create_parser()
    args = parser.parse_args()
    
    # Setup logging
    log_level = "DEBUG" if args.verbose else "INFO"
    setup_logging(log_level)
    
    # Create cluster manager
    manager = ClusterManager()
    await manager.initialize()
    
    try:
        # Route commands
        if args.command == "scan":
            await cmd_scan(manager, args)
        elif args.command == "status":
            await cmd_status(manager, args)
        elif args.command == "wifi":
            await cmd_wifi_connect(manager, args)
        elif args.command == "bluetooth":
            await cmd_bluetooth_scan(manager, args)
        elif args.command == "cluster":
            if args.cluster_cmd == "enable":
                await cmd_cluster_enable(manager, args)
            elif args.cluster_cmd == "join":
                await cmd_cluster_join(manager, args)
        elif args.command == "portman":
            await cmd_portman(manager, args)
        elif args.command == "jessica":
            await cmd_jessica(manager, args)
        elif args.command == "esp32":
            await cmd_esp32(manager, args)
        else:
            parser.print_help()
    
    finally:
        await manager.shutdown()


def main():
    """Main entry point"""
    try:
        asyncio.run(async_main())
    except KeyboardInterrupt:
        print("\nInterrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
