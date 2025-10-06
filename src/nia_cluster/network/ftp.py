"""
FTP connection manager for file transfers
"""

import logging
import ftplib
from typing import Optional, Dict, List
from pathlib import Path

logger = logging.getLogger(__name__)


class FTPManager:
    """Manages FTP connections for file transfers"""
    
    def __init__(self):
        self.connections: Dict[str, ftplib.FTP] = {}
        
    def connect(self, host: str, port: int = 21, username: str = "anonymous",
               password: str = "", timeout: int = 30) -> bool:
        """
        Connect to FTP server
        
        Args:
            host: Hostname or IP address
            port: FTP port (default: 21)
            username: FTP username
            password: FTP password
            timeout: Connection timeout in seconds
        """
        connection_id = f"{username}@{host}:{port}"
        logger.info(f"Connecting to FTP server: {connection_id}")
        
        try:
            ftp = ftplib.FTP(timeout=timeout)
            ftp.connect(host, port)
            ftp.login(username, password)
            
            self.connections[connection_id] = ftp
            logger.info(f"Connected to {connection_id}")
            return True
            
        except Exception as e:
            logger.error(f"FTP connection failed: {e}")
            return False
    
    def list_directory(self, connection_id: str, path: str = "/") -> Optional[List[str]]:
        """
        List files in directory
        
        Args:
            connection_id: Connection identifier
            path: Directory path
        """
        ftp = self.connections.get(connection_id)
        if not ftp:
            logger.error(f"No active connection: {connection_id}")
            return None
        
        try:
            files = []
            ftp.cwd(path)
            ftp.retrlines('LIST', lambda x: files.append(x))
            return files
            
        except Exception as e:
            logger.error(f"Failed to list directory: {e}")
            return None
    
    def upload_file(self, connection_id: str, local_path: str, 
                   remote_path: str) -> bool:
        """
        Upload file to FTP server
        
        Args:
            connection_id: Connection identifier
            local_path: Local file path
            remote_path: Remote file path
        """
        ftp = self.connections.get(connection_id)
        if not ftp:
            logger.error(f"No active connection: {connection_id}")
            return False
        
        try:
            with open(local_path, 'rb') as f:
                ftp.storbinary(f'STOR {remote_path}', f)
            
            logger.info(f"Uploaded {local_path} to {remote_path}")
            return True
            
        except Exception as e:
            logger.error(f"Upload failed: {e}")
            return False
    
    def download_file(self, connection_id: str, remote_path: str,
                     local_path: str) -> bool:
        """
        Download file from FTP server
        
        Args:
            connection_id: Connection identifier
            remote_path: Remote file path
            local_path: Local file path
        """
        ftp = self.connections.get(connection_id)
        if not ftp:
            logger.error(f"No active connection: {connection_id}")
            return False
        
        try:
            with open(local_path, 'wb') as f:
                ftp.retrbinary(f'RETR {remote_path}', f.write)
            
            logger.info(f"Downloaded {remote_path} to {local_path}")
            return True
            
        except Exception as e:
            logger.error(f"Download failed: {e}")
            return False
    
    def delete_file(self, connection_id: str, remote_path: str) -> bool:
        """Delete file on FTP server"""
        ftp = self.connections.get(connection_id)
        if not ftp:
            logger.error(f"No active connection: {connection_id}")
            return False
        
        try:
            ftp.delete(remote_path)
            logger.info(f"Deleted {remote_path}")
            return True
            
        except Exception as e:
            logger.error(f"Delete failed: {e}")
            return False
    
    def disconnect(self, connection_id: str) -> bool:
        """Disconnect from FTP server"""
        ftp = self.connections.get(connection_id)
        if not ftp:
            logger.warning(f"No connection to disconnect: {connection_id}")
            return False
        
        try:
            ftp.quit()
            del self.connections[connection_id]
            logger.info(f"Disconnected from {connection_id}")
            return True
            
        except Exception as e:
            logger.error(f"Disconnect error: {e}")
            return False
    
    def disconnect_all(self):
        """Disconnect from all FTP servers"""
        connection_ids = list(self.connections.keys())
        for connection_id in connection_ids:
            self.disconnect(connection_id)
