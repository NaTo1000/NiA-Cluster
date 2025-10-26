"""Configuration management for NiA-Cluster."""
import copy
import os
import yaml


class ConfigManager:
    """Manages cluster configuration with support for loading and saving."""
    
    DEFAULT_CONFIG = {
        'cluster': {
            'name': 'default',
            'relay_port': 4040,
            'nodes': []
        },
        'security': {
            'enable_ssl': False,
            'password': None
        },
        'features': {
            'enable_ble': False,
            'auto_discovery': True
        }
    }
    
    def __init__(self, config_path=None):
        """Initialize configuration manager.
        
        Args:
            config_path: Optional path to configuration file to load.
        """
        # Use deep copy to avoid sharing nested mutable defaults across instances
        self.config = copy.deepcopy(self.DEFAULT_CONFIG)
        
        if config_path:
            self.load(config_path)
    
    def load(self, config_path):
        """Load configuration from YAML file.
        
        Args:
            config_path: Path to YAML configuration file.
        """
        with open(config_path, 'r') as f:
            loaded_config = yaml.safe_load(f)
            if loaded_config:
                self.config.update(loaded_config)
    
    def save(self, save_path):
        """Save configuration to YAML file.
        
        Args:
            save_path: Path where configuration should be saved.
        """
        # Create directory only if path includes a directory component
        dirpath = os.path.dirname(save_path)
        if dirpath:
            os.makedirs(dirpath, exist_ok=True)
        
        with open(save_path, 'w') as f:
            yaml.dump(self.config, f, default_flow_style=False)
    
    def get(self, key, default=None):
        """Get configuration value by key.
        
        Args:
            key: Configuration key (supports dot notation).
            default: Default value if key not found.
            
        Returns:
            Configuration value or default.
        """
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
                
            if value is None:
                return default
        
        return value
    
    def set(self, key, value):
        """Set configuration value by key.
        
        Args:
            key: Configuration key (supports dot notation).
            value: Value to set.
        """
        keys = key.split('.')
        config = self.config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
