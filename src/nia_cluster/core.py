"""
Core Cluster Manager
Main entry point for NiA-Cluster functionality
"""

import logging
from typing import Optional, Dict, Any
from nia_cluster.config import ConfigManager
from nia_cluster.network import NetworkManager
from nia_cluster.ai import PortmanAI, JessicAI
from nia_cluster.security import SecurityManager


logger = logging.getLogger(__name__)


class ClusterManager:
    """
    Main cluster management class that coordinates all subsystems.
    
    Manages:
    - Network connections (WiFi, BLE, Telnet, FTP, SSH)
    - ESP-32 device integration
    - Port monitoring and management (PortmanAI)
    - Security and voice control (JessicAI)
    - Auto-reconnection and cluster sharing
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the cluster manager.
        
        Args:
            config_path: Path to configuration file
        """
        self.config = ConfigManager(config_path)
        self.network = NetworkManager(self.config)
        self.portman_ai = PortmanAI(self.config)
        self.jessica_ai = JessicAI(self.config)
        self.security = SecurityManager(self.config)
        
        logger.info("NiA-Cluster Manager initialized")
    
    def start(self):
        """Start all cluster services."""
        logger.info("Starting NiA-Cluster services...")
        self.security.initialize()
        self.network.start()
        self.portman_ai.start_monitoring()
        self.jessica_ai.start()
        logger.info("All services started successfully")
    
    def stop(self):
        """Stop all cluster services."""
        logger.info("Stopping NiA-Cluster services...")
        self.jessica_ai.stop()
        self.portman_ai.stop_monitoring()
        self.network.stop()
        logger.info("All services stopped")
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get current status of all cluster components.
        
        Returns:
            Dictionary with status information
        """
        return {
            "network": self.network.get_status(),
            "portman_ai": self.portman_ai.get_status(),
            "jessica_ai": self.jessica_ai.get_status(),
            "security": self.security.get_status()
        }
