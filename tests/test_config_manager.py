"""Tests for ConfigManager class."""
import os
import sys
import tempfile
import unittest
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from nia_cluster.config.manager import ConfigManager


class TestConfigManager(unittest.TestCase):
    """Test cases for ConfigManager."""
    
    def test_deep_copy_prevents_shared_mutable_defaults(self):
        """Test that nested config changes in one instance don't affect another."""
        # Create two separate config managers
        config1 = ConfigManager()
        config2 = ConfigManager()
        
        # Modify nested config in config1
        config1.config['cluster']['name'] = 'modified'
        config1.config['cluster']['nodes'].append({'name': 'test_node'})
        
        # Verify config2 is not affected
        self.assertEqual(config2.config['cluster']['name'], 'default',
                        "Nested config should not be shared between instances")
        self.assertEqual(len(config2.config['cluster']['nodes']), 0,
                        "Nested lists should not be shared between instances")
    
    def test_save_to_current_directory(self):
        """Test saving config to a file in the current working directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Change to temp directory
            original_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                
                # Create config and save to filename without path
                config = ConfigManager()
                config.config['cluster']['name'] = 'test_cluster'
                
                # This should work without error (no directory creation needed)
                config.save('test_config.yaml')
                
                # Verify file was created
                self.assertTrue(os.path.exists('test_config.yaml'),
                               "Config file should be created in current directory")
                
                # Verify content
                config2 = ConfigManager('test_config.yaml')
                self.assertEqual(config2.config['cluster']['name'], 'test_cluster')
                
            finally:
                os.chdir(original_cwd)
    
    def test_save_to_subdirectory(self):
        """Test saving config to a subdirectory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Save to a subdirectory path
            config = ConfigManager()
            config.config['cluster']['name'] = 'subdir_cluster'
            
            save_path = os.path.join(tmpdir, 'configs', 'test.yaml')
            config.save(save_path)
            
            # Verify file was created
            self.assertTrue(os.path.exists(save_path),
                           "Config file should be created with subdirectories")
            
            # Verify content
            config2 = ConfigManager(save_path)
            self.assertEqual(config2.config['cluster']['name'], 'subdir_cluster')
    
    def test_get_with_dot_notation(self):
        """Test getting config values with dot notation."""
        config = ConfigManager()
        
        # Test existing nested value
        self.assertEqual(config.get('cluster.name'), 'default')
        self.assertEqual(config.get('cluster.relay_port'), 4040)
        
        # Test non-existing value with default
        self.assertIsNone(config.get('nonexistent.key'))
        self.assertEqual(config.get('nonexistent.key', 'default_value'), 'default_value')
    
    def test_set_with_dot_notation(self):
        """Test setting config values with dot notation."""
        config = ConfigManager()
        
        # Set existing value
        config.set('cluster.name', 'new_name')
        self.assertEqual(config.get('cluster.name'), 'new_name')
        
        # Set new nested value
        config.set('new_section.new_key', 'new_value')
        self.assertEqual(config.get('new_section.new_key'), 'new_value')


if __name__ == '__main__':
    unittest.main()
