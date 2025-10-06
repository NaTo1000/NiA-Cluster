"""
Telnet connection manager for legacy device support
"""

import logging
import telnetlib
from typing import Optional, Dict

logger = logging.getLogger(__name__)


class TelnetManager:
    """Manages Telnet connections for legacy devices"""
    
    def __init__(self):
        self.connections: Dict[str, telnetlib.Telnet] = {}
        
    def connect(self, host: str, port: int = 23, timeout: int = 10) -> bool:
        """
        Connect to Telnet server
        
        Args:
            host: Hostname or IP address
            port: Telnet port (default: 23)
            timeout: Connection timeout in seconds
        """
        connection_id = f"{host}:{port}"
        logger.info(f"Connecting to Telnet server: {connection_id}")
        
        try:
            tn = telnetlib.Telnet(host, port, timeout)
            self.connections[connection_id] = tn
            logger.info(f"Connected to {connection_id}")
            return True
            
        except Exception as e:
            logger.error(f"Telnet connection failed: {e}")
            return False
    
    def login(self, connection_id: str, username: str, password: str) -> bool:
        """
        Login to Telnet server
        
        Args:
            connection_id: Connection identifier (host:port)
            username: Username
            password: Password
        """
        tn = self.connections.get(connection_id)
        if not tn:
            logger.error(f"No active connection: {connection_id}")
            return False
        
        try:
            # Wait for login prompt
            tn.read_until(b"login: ", timeout=5)
            tn.write(username.encode('ascii') + b"\n")
            
            # Wait for password prompt
            tn.read_until(b"Password: ", timeout=5)
            tn.write(password.encode('ascii') + b"\n")
            
            logger.info(f"Logged in to {connection_id}")
            return True
            
        except Exception as e:
            logger.error(f"Login failed: {e}")
            return False
    
    def send_command(self, connection_id: str, command: str, 
                    wait_for: str = "#", timeout: int = 10) -> Optional[str]:
        """
        Send command to Telnet server
        
        Args:
            connection_id: Connection identifier
            command: Command to execute
            wait_for: String to wait for after command
            timeout: Command timeout in seconds
        """
        tn = self.connections.get(connection_id)
        if not tn:
            logger.error(f"No active connection: {connection_id}")
            return None
        
        try:
            tn.write(command.encode('ascii') + b"\n")
            response = tn.read_until(wait_for.encode('ascii'), timeout=timeout)
            
            result = response.decode('ascii')
            logger.debug(f"Command executed on {connection_id}: {command}")
            return result
            
        except Exception as e:
            logger.error(f"Command execution failed: {e}")
            return None
    
    def disconnect(self, connection_id: str) -> bool:
        """Disconnect from Telnet server"""
        tn = self.connections.get(connection_id)
        if not tn:
            logger.warning(f"No connection to disconnect: {connection_id}")
            return False
        
        try:
            tn.close()
            del self.connections[connection_id]
            logger.info(f"Disconnected from {connection_id}")
            return True
            
        except Exception as e:
            logger.error(f"Disconnect error: {e}")
            return False
    
    def disconnect_all(self):
        """Disconnect from all Telnet servers"""
        connection_ids = list(self.connections.keys())
        for connection_id in connection_ids:
            self.disconnect(connection_id)
    
    def is_connected(self, connection_id: str) -> bool:
        """Check if connected to a Telnet server"""
        return connection_id in self.connections
