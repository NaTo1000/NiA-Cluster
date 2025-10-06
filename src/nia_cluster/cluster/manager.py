"""
Cluster Manager - Orchestrates all NiA-Cluster components

Manages WiFi, Bluetooth, ESP-32 devices, security, and AI systems.
"""

import logging
import asyncio
from typing import Dict, Optional, List
from datetime import datetime

from ..network.wifi import WiFiManager
from ..network.bluetooth import BluetoothManager
from ..network.ssh import SSHManager
from ..network.telnet import TelnetManager
from ..network.ftp import FTPManager
from ..network.vlan import VLANManager
from ..esp32.manager import ESP32Manager
from ..ai.portman import PortmanAI
from ..ai.jessica import JessicaAI

logger = logging.getLogger(__name__)


class ClusterManager:
    """
    Main cluster management system
    
    Coordinates all networking, hardware, and AI components.
    """
    
    def __init__(self):
        # Network managers
        self.wifi = WiFiManager()
        self.bluetooth = BluetoothManager()
        self.ssh = SSHManager()
        self.telnet = TelnetManager()
        self.ftp = FTPManager()
        self.vlan = VLANManager()
        
        # Hardware manager
        self.esp32 = ESP32Manager()
        
        # AI systems
        self.portman = PortmanAI()
        self.jessica = JessicaAI()
        
        # Cluster state
        self.cluster_nodes: Dict[str, Dict] = {}
        self.cluster_mode = "standalone"  # standalone, master, node
        self.auto_reconnect = True
        
        logger.info("NiA-Cluster Manager initialized")
    
    async def initialize(self):
        """Initialize all cluster components"""
        logger.info("Initializing cluster components...")
        
        try:
            # Initialize voice control
            self.jessica.initialize_voice_control()
            
            # Start monitoring systems
            asyncio.create_task(self.portman.start_monitoring())
            asyncio.create_task(self.jessica.start_security_monitoring())
            
            logger.info("Cluster initialization complete")
            return True
            
        except Exception as e:
            logger.error(f"Initialization failed: {e}")
            return False
    
    async def enable_cluster_mode(self, mode: str = "share"):
        """
        Enable cluster sharing mode
        
        Args:
            mode: Cluster mode (share, master, node)
        """
        logger.info(f"Enabling cluster mode: {mode}")
        
        try:
            if mode == "share":
                # Enable Bluetooth and WiFi for cluster sharing
                await self._setup_cluster_sharing()
                self.cluster_mode = "share"
                
            elif mode == "master":
                self.cluster_mode = "master"
                await self._setup_master_node()
                
            elif mode == "node":
                self.cluster_mode = "node"
                await self._setup_cluster_node()
            
            logger.info(f"Cluster mode enabled: {mode}")
            
        except Exception as e:
            logger.error(f"Failed to enable cluster mode: {e}")
    
    async def _setup_cluster_sharing(self):
        """Setup cluster sharing via Bluetooth/WiFi"""
        # Scan for nearby cluster nodes
        devices = await self.bluetooth.scan_devices()
        logger.info(f"Found {len(devices)} nearby devices")
        
        # Enable auto-reconnect
        self.bluetooth.set_auto_reconnect(True)
    
    async def _setup_master_node(self):
        """Setup as cluster master node"""
        logger.info("Configuring as master node...")
        # Master node coordination logic
    
    async def _setup_cluster_node(self):
        """Setup as cluster node"""
        logger.info("Configuring as cluster node...")
        # Node joining logic
    
    async def join_cluster(self, master_address: str):
        """
        Join an existing cluster
        
        Args:
            master_address: Master node address (Bluetooth or WiFi)
        """
        logger.info(f"Joining cluster at {master_address}")
        
        try:
            # Try Bluetooth first
            if self._is_bluetooth_address(master_address):
                success = await self.bluetooth.connect(master_address, auto_reconnect=True)
                if success:
                    self.cluster_nodes[master_address] = {
                        "type": "bluetooth",
                        "role": "master",
                        "connected": True,
                        "joined": datetime.now()
                    }
                    logger.info(f"Successfully joined cluster via Bluetooth")
                    return True
            
            # Try WiFi/network connection
            else:
                # Connect via SSH with key authentication
                parts = master_address.split("@")
                if len(parts) == 2:
                    username, host = parts
                    success = await self.ssh.connect(host, username)
                    if success:
                        logger.info(f"Successfully joined cluster via SSH")
                        return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to join cluster: {e}")
            return False
    
    def _is_bluetooth_address(self, address: str) -> bool:
        """Check if address is a Bluetooth MAC address"""
        # Bluetooth addresses are in format XX:XX:XX:XX:XX:XX
        parts = address.split(":")
        return len(parts) == 6 and all(len(p) == 2 for p in parts)
    
    async def scan_network(self) -> Dict:
        """Scan for all network resources"""
        logger.info("Scanning network...")
        
        results = {
            "wifi_networks": [],
            "bluetooth_devices": [],
            "esp32_devices": [],
            "timestamp": datetime.now()
        }
        
        try:
            # Scan WiFi networks
            results["wifi_networks"] = await self.wifi.scan_networks()
            
            # Scan Bluetooth devices
            results["bluetooth_devices"] = await self.bluetooth.scan_devices()
            
            # Scan ESP-32 devices
            results["esp32_devices"] = self.esp32.scan_devices()
            
            logger.info(f"Network scan complete: {len(results['wifi_networks'])} WiFi, "
                       f"{len(results['bluetooth_devices'])} BLE, "
                       f"{len(results['esp32_devices'])} ESP-32")
            
        except Exception as e:
            logger.error(f"Network scan failed: {e}")
            results["error"] = str(e)
        
        return results
    
    def get_status(self) -> Dict:
        """Get complete cluster status"""
        return {
            "cluster_mode": self.cluster_mode,
            "cluster_nodes": len(self.cluster_nodes),
            "wifi": {
                "current_network": self.wifi.get_current_network(),
            },
            "bluetooth": {
                "connected_devices": self.bluetooth.get_connected_devices(),
            },
            "esp32": {
                "connected_devices": self.esp32.get_connected_devices(),
            },
            "ssh": {
                "active_connections": self.ssh.get_active_connections(),
            },
            "vlan": {
                "configured_vlans": self.vlan.list_vlans(),
            },
            "portman": self.portman.get_monitoring_summary(),
            "jessica": self.jessica.get_security_status(),
            "auto_reconnect": self.auto_reconnect,
        }
    
    async def shutdown(self):
        """Shutdown cluster and cleanup resources"""
        logger.info("Shutting down NiA-Cluster...")
        
        try:
            # Stop monitoring
            self.portman.stop_monitoring()
            self.jessica.stop_security_monitoring()
            
            # Disconnect all connections
            await self.bluetooth.disconnect_all()
            self.ssh.disconnect_all()
            self.telnet.disconnect_all()
            self.ftp.disconnect_all()
            self.esp32.disconnect_all()
            
            logger.info("Cluster shutdown complete")
            
        except Exception as e:
            logger.error(f"Shutdown error: {e}")
    
    async def process_voice_command(self, command: str) -> Dict:
        """Process voice command through JessicaAI"""
        return await self.jessica.process_voice_command(command)
    
    def get_security_report(self) -> Dict:
        """Get security report from JessicaAI"""
        return self.jessica.generate_security_report()
    
    def get_port_analysis(self) -> List[Dict]:
        """Get port analysis from PortmanAI"""
        return self.portman.get_all_active_ports()
