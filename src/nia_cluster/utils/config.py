"""
Configuration management for NiA-Cluster
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional


class Config:
    """Configuration manager"""
    
    DEFAULT_CONFIG = {
        "cluster": {
            "mode": "standalone",
            "auto_reconnect": True,
            "reconnect_timeout": 30,
        },
        "wifi": {
            "auto_connect": False,
            "preferred_networks": [],
        },
        "bluetooth": {
            "scan_timeout": 10,
            "auto_reconnect": True,
        },
        "esp32": {
            "default_baudrate": 115200,
            "auto_detect": True,
        },
        "ssh": {
            "key_directory": "~/.ssh",
            "default_port": 22,
        },
        "portman": {
            "monitoring_interval": 5,
            "anomaly_threshold": 0.8,
        },
        "jessica": {
            "voice_enabled": False,
            "security_monitoring": True,
            "threat_notification": True,
        },
        "logging": {
            "level": "INFO",
            "file": None,
        }
    }
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize configuration
        
        Args:
            config_path: Path to configuration file (YAML)
        """
        self.config_path = config_path
        self.config = self.DEFAULT_CONFIG.copy()
        
        if config_path:
            self.load(config_path)
    
    def load(self, path: str):
        """Load configuration from file"""
        config_file = Path(path).expanduser()
        
        if not config_file.exists():
            raise FileNotFoundError(f"Configuration file not found: {path}")
        
        with open(config_file, 'r') as f:
            user_config = yaml.safe_load(f)
        
        # Merge with default config
        self._deep_merge(self.config, user_config)
    
    def save(self, path: str):
        """Save configuration to file"""
        config_file = Path(path).expanduser()
        config_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(config_file, 'w') as f:
            yaml.dump(self.config, f, default_flow_style=False)
    
    def _deep_merge(self, base: Dict, update: Dict):
        """Deep merge two dictionaries"""
        for key, value in update.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value using dot notation
        
        Example: config.get("cluster.mode")
        """
        keys = key.split(".")
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any):
        """
        Set configuration value using dot notation
        
        Example: config.set("cluster.mode", "master")
        """
        keys = key.split(".")
        config = self.config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
    
    def to_dict(self) -> Dict:
        """Get configuration as dictionary"""
        return self.config.copy()
