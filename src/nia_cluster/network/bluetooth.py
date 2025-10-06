"""
Bluetooth/BLE management module for NiA-Cluster

Handles Bluetooth Low Energy connections for cluster sharing.
"""

import asyncio
import logging
from typing import List, Dict, Optional, Callable
from bleak import BleakScanner, BleakClient

logger = logging.getLogger(__name__)


class BluetoothManager:
    """Manages Bluetooth/BLE connections for cluster sharing"""
    
    # NiA-Cluster custom UUIDs
    CLUSTER_SERVICE_UUID = "6e400001-b5a3-f393-e0a9-e50e24dcca9e"
    CLUSTER_TX_CHAR_UUID = "6e400002-b5a3-f393-e0a9-e50e24dcca9e"
    CLUSTER_RX_CHAR_UUID = "6e400003-b5a3-f393-e0a9-e50e24dcca9e"
    
    def __init__(self):
        self.connected_devices: Dict[str, BleakClient] = {}
        self.discovered_devices: List[Dict] = []
        self.reconnect_enabled = True
        self._notification_callbacks: Dict[str, Callable] = {}
        
    async def scan_devices(self, timeout: float = 10.0) -> List[Dict[str, str]]:
        """
        Scan for nearby Bluetooth devices
        
        Args:
            timeout: Scan duration in seconds
        """
        logger.info(f"Scanning for Bluetooth devices (timeout: {timeout}s)...")
        self.discovered_devices = []
        
        try:
            devices = await BleakScanner.discover(timeout=timeout)
            
            for device in devices:
                device_info = {
                    "address": device.address,
                    "name": device.name or "Unknown",
                    "rssi": device.rssi if hasattr(device, 'rssi') else None,
                }
                self.discovered_devices.append(device_info)
                logger.debug(f"Found device: {device_info}")
                
            logger.info(f"Found {len(self.discovered_devices)} devices")
            
        except Exception as e:
            logger.error(f"Bluetooth scan failed: {e}")
            
        return self.discovered_devices
    
    async def connect(self, address: str, auto_reconnect: bool = True) -> bool:
        """
        Connect to a Bluetooth device
        
        Args:
            address: Device MAC address
            auto_reconnect: Enable automatic reconnection on disconnect
        """
        logger.info(f"Connecting to Bluetooth device: {address}")
        
        try:
            client = BleakClient(address, disconnected_callback=self._on_disconnect)
            await client.connect()
            
            if client.is_connected:
                self.connected_devices[address] = client
                logger.info(f"Successfully connected to {address}")
                
                # Enable notifications for cluster communication
                await self._setup_notifications(address)
                return True
            else:
                logger.error(f"Failed to connect to {address}")
                return False
                
        except Exception as e:
            logger.error(f"Connection error: {e}")
            return False
    
    async def _setup_notifications(self, address: str):
        """Setup BLE notifications for data transfer"""
        try:
            client = self.connected_devices.get(address)
            if not client:
                return
                
            # Try to start notifications on the RX characteristic
            try:
                await client.start_notify(
                    self.CLUSTER_RX_CHAR_UUID,
                    lambda sender, data: self._handle_notification(address, sender, data)
                )
                logger.debug(f"Notifications enabled for {address}")
            except Exception as e:
                logger.debug(f"Could not enable notifications: {e}")
                
        except Exception as e:
            logger.error(f"Failed to setup notifications: {e}")
    
    def _handle_notification(self, address: str, sender, data: bytearray):
        """Handle incoming BLE notifications"""
        logger.debug(f"Received notification from {address}: {data}")
        
        # Call registered callback if exists
        callback = self._notification_callbacks.get(address)
        if callback:
            callback(data)
    
    def register_notification_callback(self, address: str, callback: Callable):
        """Register a callback for notifications from a device"""
        self._notification_callbacks[address] = callback
    
    async def disconnect(self, address: str) -> bool:
        """Disconnect from a Bluetooth device"""
        logger.info(f"Disconnecting from {address}")
        
        try:
            client = self.connected_devices.get(address)
            if not client:
                logger.warning(f"No connection to {address}")
                return False
            
            await client.disconnect()
            del self.connected_devices[address]
            logger.info(f"Disconnected from {address}")
            return True
            
        except Exception as e:
            logger.error(f"Disconnect error: {e}")
            return False
    
    def _on_disconnect(self, client: BleakClient):
        """Handle unexpected disconnection"""
        address = client.address
        logger.warning(f"Device {address} disconnected unexpectedly")
        
        # Remove from connected devices
        if address in self.connected_devices:
            del self.connected_devices[address]
        
        # Auto-reconnect if enabled
        if self.reconnect_enabled:
            logger.info(f"Auto-reconnect enabled, attempting to reconnect to {address}")
            asyncio.create_task(self._reconnect(address))
    
    async def _reconnect(self, address: str, max_attempts: int = 5):
        """Attempt to reconnect to a device"""
        for attempt in range(1, max_attempts + 1):
            logger.info(f"Reconnection attempt {attempt}/{max_attempts} for {address}")
            
            try:
                success = await self.connect(address, auto_reconnect=True)
                if success:
                    logger.info(f"Successfully reconnected to {address}")
                    return
                    
            except Exception as e:
                logger.error(f"Reconnection attempt {attempt} failed: {e}")
            
            # Wait before next attempt (exponential backoff)
            await asyncio.sleep(2 ** attempt)
        
        logger.error(f"Failed to reconnect to {address} after {max_attempts} attempts")
    
    async def send_data(self, address: str, data: bytes) -> bool:
        """
        Send data to a connected device
        
        Args:
            address: Device MAC address
            data: Data to send
        """
        try:
            client = self.connected_devices.get(address)
            if not client or not client.is_connected:
                logger.error(f"No active connection to {address}")
                return False
            
            # Write data to TX characteristic
            await client.write_gatt_char(self.CLUSTER_TX_CHAR_UUID, data)
            logger.debug(f"Sent {len(data)} bytes to {address}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send data: {e}")
            return False
    
    def is_connected(self, address: str) -> bool:
        """Check if a device is connected"""
        client = self.connected_devices.get(address)
        return client is not None and client.is_connected
    
    def get_connected_devices(self) -> List[str]:
        """Get list of connected device addresses"""
        return list(self.connected_devices.keys())
    
    async def disconnect_all(self):
        """Disconnect from all connected devices"""
        logger.info("Disconnecting from all devices")
        
        addresses = list(self.connected_devices.keys())
        for address in addresses:
            await self.disconnect(address)
    
    def set_auto_reconnect(self, enabled: bool):
        """Enable or disable automatic reconnection"""
        self.reconnect_enabled = enabled
        logger.info(f"Auto-reconnect {'enabled' if enabled else 'disabled'}")
