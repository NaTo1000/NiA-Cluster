"""
ESP-32 device manager for hardware integration

Supports communication with ESP-32 devices over serial and WiFi.
"""

import logging
import serial
import serial.tools.list_ports
from typing import List, Dict, Optional
import time

logger = logging.getLogger(__name__)


class ESP32Manager:
    """Manages ESP-32 device connections and operations"""
    
    def __init__(self):
        self.connections: Dict[str, serial.Serial] = {}
        self.device_info: Dict[str, Dict] = {}
        
    def scan_devices(self) -> List[Dict[str, str]]:
        """
        Scan for connected ESP-32 devices
        
        Returns:
            List of detected ESP-32 devices with port information
        """
        logger.info("Scanning for ESP-32 devices...")
        devices = []
        
        try:
            ports = serial.tools.list_ports.comports()
            
            for port in ports:
                # ESP-32 common USB-to-Serial chips
                if any(chip in port.description.upper() for chip in 
                      ['CP210', 'CH340', 'FTDI', 'ESP32']):
                    device = {
                        "port": port.device,
                        "description": port.description,
                        "hwid": port.hwid,
                        "manufacturer": port.manufacturer or "Unknown"
                    }
                    devices.append(device)
                    logger.info(f"Found ESP-32 device: {device}")
            
            logger.info(f"Found {len(devices)} ESP-32 device(s)")
            
        except Exception as e:
            logger.error(f"Error scanning for devices: {e}")
        
        return devices
    
    def connect(self, port: str, baudrate: int = 115200, timeout: int = 2) -> bool:
        """
        Connect to ESP-32 device
        
        Args:
            port: Serial port (e.g., '/dev/ttyUSB0' or 'COM3')
            baudrate: Baud rate (default: 115200)
            timeout: Read timeout in seconds
        """
        logger.info(f"Connecting to ESP-32 on {port} at {baudrate} baud...")
        
        try:
            if port in self.connections:
                logger.warning(f"Already connected to {port}")
                return True
            
            ser = serial.Serial(
                port=port,
                baudrate=baudrate,
                timeout=timeout,
                write_timeout=timeout
            )
            
            # Wait for connection to stabilize
            time.sleep(0.5)
            
            self.connections[port] = ser
            logger.info(f"Successfully connected to {port}")
            
            # Get device info
            self._get_device_info(port)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to {port}: {e}")
            return False
    
    def _get_device_info(self, port: str):
        """Get information from ESP-32 device"""
        try:
            # Send command to get chip info (if running appropriate firmware)
            response = self.send_command(port, "SYS:INFO?")
            if response:
                self.device_info[port] = {"info": response}
        except Exception as e:
            logger.debug(f"Could not get device info: {e}")
    
    def disconnect(self, port: str) -> bool:
        """Disconnect from ESP-32 device"""
        logger.info(f"Disconnecting from {port}")
        
        try:
            ser = self.connections.get(port)
            if not ser:
                logger.warning(f"No connection to {port}")
                return False
            
            ser.close()
            del self.connections[port]
            
            if port in self.device_info:
                del self.device_info[port]
            
            logger.info(f"Disconnected from {port}")
            return True
            
        except Exception as e:
            logger.error(f"Error disconnecting: {e}")
            return False
    
    def send_command(self, port: str, command: str, wait_response: bool = True) -> Optional[str]:
        """
        Send command to ESP-32 device
        
        Args:
            port: Serial port
            command: Command string
            wait_response: Wait for response
            
        Returns:
            Response string if wait_response is True
        """
        ser = self.connections.get(port)
        if not ser:
            logger.error(f"No connection to {port}")
            return None
        
        try:
            # Clear input buffer
            ser.reset_input_buffer()
            
            # Send command
            cmd = command.strip() + "\n"
            ser.write(cmd.encode('utf-8'))
            logger.debug(f"Sent command to {port}: {command}")
            
            if wait_response:
                # Wait for response
                time.sleep(0.1)
                
                if ser.in_waiting > 0:
                    response = ser.read(ser.in_waiting).decode('utf-8', errors='ignore')
                    logger.debug(f"Received response: {response}")
                    return response.strip()
                else:
                    return ""
            
            return None
            
        except Exception as e:
            logger.error(f"Error sending command: {e}")
            return None
    
    def read_data(self, port: str, size: Optional[int] = None) -> Optional[bytes]:
        """
        Read data from ESP-32 device
        
        Args:
            port: Serial port
            size: Number of bytes to read (None for all available)
        """
        ser = self.connections.get(port)
        if not ser:
            logger.error(f"No connection to {port}")
            return None
        
        try:
            if size:
                data = ser.read(size)
            else:
                if ser.in_waiting > 0:
                    data = ser.read(ser.in_waiting)
                else:
                    return b''
            
            logger.debug(f"Read {len(data)} bytes from {port}")
            return data
            
        except Exception as e:
            logger.error(f"Error reading data: {e}")
            return None
    
    def write_data(self, port: str, data: bytes) -> bool:
        """Write raw data to ESP-32 device"""
        ser = self.connections.get(port)
        if not ser:
            logger.error(f"No connection to {port}")
            return False
        
        try:
            bytes_written = ser.write(data)
            logger.debug(f"Wrote {bytes_written} bytes to {port}")
            return bytes_written == len(data)
            
        except Exception as e:
            logger.error(f"Error writing data: {e}")
            return False
    
    def flash_firmware(self, port: str, firmware_path: str) -> bool:
        """
        Flash firmware to ESP-32 device using esptool
        
        Args:
            port: Serial port
            firmware_path: Path to firmware binary
        """
        logger.info(f"Flashing firmware to {port}: {firmware_path}")
        
        try:
            import esptool
            
            # Disconnect if connected
            if port in self.connections:
                self.disconnect(port)
            
            # Flash firmware
            command = [
                '--port', port,
                '--baud', '460800',
                'write_flash',
                '-z',
                '0x1000', firmware_path
            ]
            
            esptool.main(command)
            
            logger.info(f"Successfully flashed firmware to {port}")
            
            # Reconnect
            time.sleep(2)
            self.connect(port)
            
            return True
            
        except Exception as e:
            logger.error(f"Firmware flash failed: {e}")
            return False
    
    def reset_device(self, port: str) -> bool:
        """Reset ESP-32 device"""
        logger.info(f"Resetting device on {port}")
        
        try:
            ser = self.connections.get(port)
            if not ser:
                logger.error(f"No connection to {port}")
                return False
            
            # Toggle DTR to reset ESP-32
            ser.setDTR(False)
            time.sleep(0.1)
            ser.setDTR(True)
            time.sleep(0.5)
            
            logger.info(f"Device reset: {port}")
            return True
            
        except Exception as e:
            logger.error(f"Reset failed: {e}")
            return False
    
    def disconnect_all(self):
        """Disconnect from all ESP-32 devices"""
        ports = list(self.connections.keys())
        for port in ports:
            self.disconnect(port)
    
    def is_connected(self, port: str) -> bool:
        """Check if connected to a device"""
        return port in self.connections and self.connections[port].is_open
    
    def get_connected_devices(self) -> List[str]:
        """Get list of connected device ports"""
        return list(self.connections.keys())
