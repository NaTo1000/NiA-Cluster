"""
SSH connection manager with key-based authentication

Supports passwordless connections using SSH keys.
"""

import logging
import os
from pathlib import Path
from typing import Optional, Dict, List
import paramiko
from paramiko import SSHClient, AutoAddPolicy

logger = logging.getLogger(__name__)


class SSHManager:
    """Manages SSH connections with key-based authentication"""
    
    def __init__(self, key_directory: Optional[str] = None):
        """
        Initialize SSH Manager
        
        Args:
            key_directory: Directory containing SSH keys (default: ~/.ssh)
        """
        self.connections: Dict[str, SSHClient] = {}
        self.key_directory = Path(key_directory or os.path.expanduser("~/.ssh"))
        
        # Ensure key directory exists
        self.key_directory.mkdir(parents=True, exist_ok=True)
        
    def load_key(self, key_path: Optional[str] = None) -> Optional[paramiko.RSAKey]:
        """
        Load SSH private key
        
        Args:
            key_path: Path to private key file (default: ~/.ssh/id_rsa)
        """
        if not key_path:
            key_path = self.key_directory / "id_rsa"
        else:
            key_path = Path(key_path)
            
        try:
            if not key_path.exists():
                logger.warning(f"Key file not found: {key_path}")
                return None
                
            # Try loading as RSA key first
            try:
                key = paramiko.RSAKey.from_private_key_file(str(key_path))
                logger.info(f"Loaded RSA key from {key_path}")
                return key
            except paramiko.ssh_exception.SSHException:
                pass
            
            # Try loading as Ed25519 key
            try:
                key = paramiko.Ed25519Key.from_private_key_file(str(key_path))
                logger.info(f"Loaded Ed25519 key from {key_path}")
                return key
            except paramiko.ssh_exception.SSHException:
                pass
            
            # Try loading as ECDSA key
            try:
                key = paramiko.ECDSAKey.from_private_key_file(str(key_path))
                logger.info(f"Loaded ECDSA key from {key_path}")
                return key
            except paramiko.ssh_exception.SSHException:
                pass
                
            logger.error(f"Could not load key from {key_path}")
            return None
            
        except Exception as e:
            logger.error(f"Error loading SSH key: {e}")
            return None
    
    def generate_key_pair(self, key_name: str = "id_rsa", key_size: int = 4096) -> bool:
        """
        Generate a new SSH key pair
        
        Args:
            key_name: Name of the key file
            key_size: Key size in bits (default: 4096)
        """
        try:
            key_path = self.key_directory / key_name
            pub_key_path = self.key_directory / f"{key_name}.pub"
            
            if key_path.exists():
                logger.warning(f"Key already exists: {key_path}")
                return False
            
            # Generate RSA key pair
            key = paramiko.RSAKey.generate(key_size)
            
            # Save private key
            key.write_private_key_file(str(key_path))
            os.chmod(key_path, 0o600)
            
            # Save public key
            with open(pub_key_path, 'w') as f:
                f.write(f"ssh-rsa {key.get_base64()} nia-cluster\n")
            
            logger.info(f"Generated SSH key pair: {key_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to generate key pair: {e}")
            return False
    
    async def connect(self, host: str, username: str, port: int = 22,
                     key_path: Optional[str] = None, password: Optional[str] = None) -> bool:
        """
        Connect to SSH server
        
        Args:
            host: Hostname or IP address
            username: SSH username
            port: SSH port (default: 22)
            key_path: Path to private key (optional, will use default if not provided)
            password: Password (used only if key auth fails)
        """
        connection_id = f"{username}@{host}:{port}"
        logger.info(f"Connecting to {connection_id}")
        
        try:
            client = SSHClient()
            client.set_missing_host_key_policy(AutoAddPolicy())
            
            # Try key-based authentication first
            key = self.load_key(key_path)
            
            if key:
                try:
                    client.connect(
                        hostname=host,
                        port=port,
                        username=username,
                        pkey=key,
                        timeout=10
                    )
                    self.connections[connection_id] = client
                    logger.info(f"Connected to {connection_id} using key authentication")
                    return True
                except Exception as e:
                    logger.warning(f"Key authentication failed: {e}")
            
            # Fall back to password authentication if provided
            if password:
                try:
                    client.connect(
                        hostname=host,
                        port=port,
                        username=username,
                        password=password,
                        timeout=10
                    )
                    self.connections[connection_id] = client
                    logger.info(f"Connected to {connection_id} using password authentication")
                    return True
                except Exception as e:
                    logger.error(f"Password authentication failed: {e}")
            
            logger.error(f"All authentication methods failed for {connection_id}")
            return False
            
        except Exception as e:
            logger.error(f"Connection error: {e}")
            return False
    
    def execute_command(self, connection_id: str, command: str) -> Optional[Dict[str, str]]:
        """
        Execute command on remote server
        
        Args:
            connection_id: Connection identifier (user@host:port)
            command: Command to execute
            
        Returns:
            Dictionary with stdout, stderr, and exit_code
        """
        client = self.connections.get(connection_id)
        if not client:
            logger.error(f"No active connection: {connection_id}")
            return None
        
        try:
            stdin, stdout, stderr = client.exec_command(command)
            
            result = {
                "stdout": stdout.read().decode('utf-8'),
                "stderr": stderr.read().decode('utf-8'),
                "exit_code": stdout.channel.recv_exit_status()
            }
            
            logger.debug(f"Command executed on {connection_id}: {command}")
            return result
            
        except Exception as e:
            logger.error(f"Command execution failed: {e}")
            return None
    
    def disconnect(self, connection_id: str) -> bool:
        """Disconnect from SSH server"""
        client = self.connections.get(connection_id)
        if not client:
            logger.warning(f"No connection to disconnect: {connection_id}")
            return False
        
        try:
            client.close()
            del self.connections[connection_id]
            logger.info(f"Disconnected from {connection_id}")
            return True
            
        except Exception as e:
            logger.error(f"Disconnect error: {e}")
            return False
    
    def disconnect_all(self):
        """Disconnect from all SSH servers"""
        connection_ids = list(self.connections.keys())
        for connection_id in connection_ids:
            self.disconnect(connection_id)
    
    def get_active_connections(self) -> List[str]:
        """Get list of active SSH connections"""
        return list(self.connections.keys())
    
    def is_connected(self, connection_id: str) -> bool:
        """Check if connected to a specific server"""
        return connection_id in self.connections
