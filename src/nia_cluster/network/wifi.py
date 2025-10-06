"""
WiFi management module for NiA-Cluster

Handles WiFi connections, scanning, and management across platforms.
"""

import platform
import subprocess
import logging
from typing import List, Dict, Optional
import asyncio

logger = logging.getLogger(__name__)


class WiFiManager:
    """Manages WiFi connections and operations"""
    
    def __init__(self):
        self.platform = platform.system()
        self.current_network = None
        self._connection_cache = {}
        
    async def scan_networks(self) -> List[Dict[str, str]]:
        """Scan for available WiFi networks"""
        logger.info("Scanning for WiFi networks...")
        networks = []
        
        try:
            if self.platform == "Linux":
                networks = await self._scan_linux()
            elif self.platform == "Windows":
                networks = await self._scan_windows()
            elif self.platform == "Darwin":  # macOS
                networks = await self._scan_macos()
            else:
                logger.warning(f"Unsupported platform: {self.platform}")
                
        except Exception as e:
            logger.error(f"Error scanning networks: {e}")
            
        return networks
    
    async def _scan_linux(self) -> List[Dict[str, str]]:
        """Scan WiFi networks on Linux"""
        networks = []
        try:
            result = subprocess.run(
                ["nmcli", "-t", "-f", "SSID,SIGNAL,SECURITY", "dev", "wifi"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            for line in result.stdout.strip().split("\n"):
                if line:
                    parts = line.split(":")
                    if len(parts) >= 3:
                        networks.append({
                            "ssid": parts[0],
                            "signal": parts[1],
                            "security": parts[2]
                        })
        except Exception as e:
            logger.error(f"Linux WiFi scan failed: {e}")
            
        return networks
    
    async def _scan_windows(self) -> List[Dict[str, str]]:
        """Scan WiFi networks on Windows"""
        networks = []
        try:
            result = subprocess.run(
                ["netsh", "wlan", "show", "networks", "mode=bssid"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            current_network = {}
            for line in result.stdout.split("\n"):
                line = line.strip()
                if line.startswith("SSID"):
                    if current_network:
                        networks.append(current_network)
                    ssid = line.split(":", 1)[1].strip()
                    current_network = {"ssid": ssid, "signal": "", "security": ""}
                elif "Signal" in line:
                    current_network["signal"] = line.split(":", 1)[1].strip()
                elif "Authentication" in line:
                    current_network["security"] = line.split(":", 1)[1].strip()
                    
            if current_network:
                networks.append(current_network)
                
        except Exception as e:
            logger.error(f"Windows WiFi scan failed: {e}")
            
        return networks
    
    async def _scan_macos(self) -> List[Dict[str, str]]:
        """Scan WiFi networks on macOS"""
        networks = []
        try:
            result = subprocess.run(
                ["/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport", "-s"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            lines = result.stdout.strip().split("\n")[1:]  # Skip header
            for line in lines:
                parts = line.split()
                if len(parts) >= 3:
                    networks.append({
                        "ssid": parts[0],
                        "signal": parts[2],
                        "security": parts[-1] if len(parts) > 3 else "Open"
                    })
        except Exception as e:
            logger.error(f"macOS WiFi scan failed: {e}")
            
        return networks
    
    async def connect(self, ssid: str, password: Optional[str] = None, 
                     auto_reconnect: bool = True) -> bool:
        """
        Connect to a WiFi network
        
        Args:
            ssid: Network SSID
            password: Network password (if required)
            auto_reconnect: Enable automatic reconnection
        """
        logger.info(f"Connecting to WiFi network: {ssid}")
        
        try:
            if self.platform == "Linux":
                success = await self._connect_linux(ssid, password)
            elif self.platform == "Windows":
                success = await self._connect_windows(ssid, password)
            elif self.platform == "Darwin":
                success = await self._connect_macos(ssid, password)
            else:
                logger.error(f"Unsupported platform: {self.platform}")
                return False
            
            if success:
                self.current_network = ssid
                if auto_reconnect:
                    self._connection_cache[ssid] = password
                logger.info(f"Successfully connected to {ssid}")
                
            return success
            
        except Exception as e:
            logger.error(f"Connection failed: {e}")
            return False
    
    async def _connect_linux(self, ssid: str, password: Optional[str]) -> bool:
        """Connect to WiFi on Linux using NetworkManager"""
        try:
            if password:
                result = subprocess.run(
                    ["nmcli", "dev", "wifi", "connect", ssid, "password", password],
                    capture_output=True,
                    timeout=30
                )
            else:
                result = subprocess.run(
                    ["nmcli", "dev", "wifi", "connect", ssid],
                    capture_output=True,
                    timeout=30
                )
            return result.returncode == 0
        except Exception as e:
            logger.error(f"Linux WiFi connection failed: {e}")
            return False
    
    async def _connect_windows(self, ssid: str, password: Optional[str]) -> bool:
        """Connect to WiFi on Windows"""
        try:
            result = subprocess.run(
                ["netsh", "wlan", "connect", f"name={ssid}"],
                capture_output=True,
                timeout=30
            )
            return result.returncode == 0
        except Exception as e:
            logger.error(f"Windows WiFi connection failed: {e}")
            return False
    
    async def _connect_macos(self, ssid: str, password: Optional[str]) -> bool:
        """Connect to WiFi on macOS"""
        try:
            if password:
                result = subprocess.run(
                    ["networksetup", "-setairportnetwork", "en0", ssid, password],
                    capture_output=True,
                    timeout=30
                )
            else:
                result = subprocess.run(
                    ["networksetup", "-setairportnetwork", "en0", ssid],
                    capture_output=True,
                    timeout=30
                )
            return result.returncode == 0
        except Exception as e:
            logger.error(f"macOS WiFi connection failed: {e}")
            return False
    
    async def disconnect(self) -> bool:
        """Disconnect from current WiFi network"""
        if not self.current_network:
            logger.warning("No active WiFi connection")
            return False
            
        logger.info(f"Disconnecting from {self.current_network}")
        
        try:
            if self.platform == "Linux":
                result = subprocess.run(
                    ["nmcli", "dev", "disconnect", "wlan0"],
                    capture_output=True,
                    timeout=10
                )
                success = result.returncode == 0
            elif self.platform == "Windows":
                result = subprocess.run(
                    ["netsh", "wlan", "disconnect"],
                    capture_output=True,
                    timeout=10
                )
                success = result.returncode == 0
            elif self.platform == "Darwin":
                result = subprocess.run(
                    ["networksetup", "-setairportpower", "en0", "off"],
                    capture_output=True,
                    timeout=10
                )
                success = result.returncode == 0
            else:
                success = False
            
            if success:
                self.current_network = None
                logger.info("Disconnected successfully")
                
            return success
            
        except Exception as e:
            logger.error(f"Disconnect failed: {e}")
            return False
    
    def get_current_network(self) -> Optional[str]:
        """Get currently connected network SSID"""
        return self.current_network
