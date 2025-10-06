"""
Configuration Manager
Handles loading and managing cluster configuration
"""

import os
import yaml
import logging
from typing import Optional, Dict, Any
from pathlib import Path


logger = logging.getLogger(__name__)


class ConfigManager:
    """
    Manages configuration for the NiA-Cluster system.
    
    Supports loading from YAML files and environment variables.
    """
    
    DEFAULT_CONFIG = {
        "cluster": {
            "name": "NiA-Cluster",
            "auto_reconnect": True,
            "reconnect_timeout": 30
        },
        "network": {
            "wifi": {
                "enabled": True,
                "ssid": "",
                "interface": "wlan0"
            },
            "bluetooth": {
                "enabled": True,
                "discoverable": False
            },
            "ssh": {
                "enabled": True,
                "port": 22,
                "key_based_auth": True
            },
            "telnet": {
                "enabled": False,
                "port": 23
            },
            "ftp": {
                "enabled": False,
                "port": 21
            }
        },
        "esp32": {
            "enabled": True,
            "baudrate": 115200,
            "port": "/dev/ttyUSB0"
        },
        "vlan": {
            "enabled": False,
            "interfaces": []
        },
        "ai": {
            "portman": {
                "enabled": True,
                "monitoring_interval": 5
            },
            "jessica": {
                "enabled": True,
                "voice_control": False,
                "notifications": {
                    "email": False,
                    "sms": False
                }
            }
        },
        "security": {
            "encryption": True,
            "key_storage": "~/.nia-cluster/keys"
        }
    }
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize configuration manager.
        
        Args:
            config_path: Optional path to configuration file
        """
        self.config_path = config_path
        self.config = self.DEFAULT_CONFIG.copy()
        
        if config_path and os.path.exists(config_path):
            self.load_from_file(config_path)
        else:
            self.load_default_locations()
    
    def load_from_file(self, path: str):
        """Load configuration from a YAML file."""
        try:
            with open(path, 'r') as f:
                user_config = yaml.safe_load(f)
                if user_config:
                    self._deep_update(self.config, user_config)
                    logger.info(f"Configuration loaded from {path}")
        except Exception as e:
            logger.warning(f"Failed to load config from {path}: {e}")
    
    def load_default_locations(self):
        """Try to load configuration from default locations."""
        default_paths = [
            "config/cluster.yaml",
            os.path.expanduser("~/.nia-cluster/config.yaml"),
            "/etc/nia-cluster/config.yaml"
        ]
        
        for path in default_paths:
            if os.path.exists(path):
                self.load_from_file(path)
                break
    
    def _deep_update(self, base: Dict, update: Dict):
        """Recursively update nested dictionary."""
        for key, value in update.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_update(base[key], value)
            else:
                base[key] = value
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Get configuration value using dot notation.
        
        Args:
            key_path: Dot-separated path to config value (e.g., 'network.wifi.enabled')
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        keys = key_path.split('.')
        value = self.config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value
    
    def set(self, key_path: str, value: Any):
        """
        Set configuration value using dot notation.
        
        Args:
            key_path: Dot-separated path to config value
            value: Value to set
        """
        keys = key_path.split('.')
        config = self.config
        
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]
        
        config[keys[-1]] = value
    
    def save(self, path: Optional[str] = None):
        """
        Save current configuration to file.
        
        Args:
            path: Optional path to save to, defaults to loaded config path
        """
        save_path = path or self.config_path
        if not save_path:
            raise ValueError("No save path specified")
        
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        
        with open(save_path, 'w') as f:
            yaml.dump(self.config, f, default_flow_style=False)
        
        logger.info(f"Configuration saved to {save_path}")
