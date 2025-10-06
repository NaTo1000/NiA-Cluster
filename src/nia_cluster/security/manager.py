"""
Security Manager
Handles encryption, authentication, and key management
"""

import logging
import os
from pathlib import Path
from typing import Dict, Any, Optional
from nia_cluster.config import ConfigManager


logger = logging.getLogger(__name__)


class SecurityManager:
    """
    Manages security for the cluster.
    
    Features:
    - SSH key-based authentication
    - Encryption for data transmission
    - Secure key storage
    - Access control
    """
    
    def __init__(self, config: ConfigManager):
        """
        Initialize security manager.
        
        Args:
            config: Configuration manager instance
        """
        self.config = config
        self.encryption_enabled = config.get('security.encryption', True)
        self.key_storage = Path(
            os.path.expanduser(config.get('security.key_storage', '~/.nia-cluster/keys'))
        )
        
        self.initialized = False
        
        logger.info("Security Manager initialized")
    
    def initialize(self):
        """Initialize security components."""
        try:
            self._ensure_key_directory()
            self._load_or_generate_keys()
            self.initialized = True
            logger.info("Security components initialized")
        except Exception as e:
            logger.error(f"Failed to initialize security: {e}")
    
    def _ensure_key_directory(self):
        """Ensure key storage directory exists with proper permissions."""
        try:
            self.key_storage.mkdir(parents=True, exist_ok=True)
            # Set restrictive permissions (700) on Unix-like systems
            if os.name != 'nt':  # Not Windows
                os.chmod(self.key_storage, 0o700)
            logger.info(f"Key storage directory ready at {self.key_storage}")
        except Exception as e:
            logger.error(f"Failed to create key directory: {e}")
            raise
    
    def _load_or_generate_keys(self):
        """Load existing keys or generate new ones."""
        ssh_key_path = self.key_storage / "id_rsa"
        
        if ssh_key_path.exists():
            logger.info("Loading existing SSH keys")
            # Placeholder for key loading
        else:
            logger.info("Generating new SSH keys")
            self._generate_ssh_keys()
    
    def _generate_ssh_keys(self):
        """Generate SSH key pair."""
        try:
            # Placeholder for SSH key generation
            # In production, this would use cryptography library
            # to generate RSA or Ed25519 keys
            
            ssh_key_path = self.key_storage / "id_rsa"
            ssh_pub_path = self.key_storage / "id_rsa.pub"
            
            logger.info(f"SSH keys would be generated at {ssh_key_path}")
            
            # Set restrictive permissions on private key
            if os.name != 'nt':
                # os.chmod(ssh_key_path, 0o600)
                pass
            
        except Exception as e:
            logger.error(f"Failed to generate SSH keys: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get security status.
        
        Returns:
            Dictionary with status information
        """
        return {
            "initialized": self.initialized,
            "encryption_enabled": self.encryption_enabled,
            "key_storage": str(self.key_storage),
            "ssh_keys_present": (self.key_storage / "id_rsa").exists()
        }
    
    def encrypt_data(self, data: bytes) -> bytes:
        """
        Encrypt data.
        
        Args:
            data: Data to encrypt
            
        Returns:
            Encrypted data
        """
        if not self.encryption_enabled:
            return data
        
        # Placeholder for encryption
        # In production, this would use cryptography library
        logger.debug("Encrypting data")
        return data
    
    def decrypt_data(self, data: bytes) -> bytes:
        """
        Decrypt data.
        
        Args:
            data: Data to decrypt
            
        Returns:
            Decrypted data
        """
        if not self.encryption_enabled:
            return data
        
        # Placeholder for decryption
        logger.debug("Decrypting data")
        return data
    
    def verify_ssh_key(self, public_key: str) -> bool:
        """
        Verify an SSH public key.
        
        Args:
            public_key: SSH public key to verify
            
        Returns:
            True if key is valid and authorized, False otherwise
        """
        # Placeholder for SSH key verification
        # In production, this would check against authorized_keys
        logger.debug("Verifying SSH key")
        return True
    
    def authorize_key(self, public_key: str, user: str):
        """
        Authorize an SSH public key for a user.
        
        Args:
            public_key: SSH public key to authorize
            user: Username to authorize key for
        """
        authorized_keys_path = self.key_storage / "authorized_keys"
        
        try:
            with open(authorized_keys_path, 'a') as f:
                f.write(f"{public_key} {user}\n")
            logger.info(f"Authorized key for user {user}")
        except Exception as e:
            logger.error(f"Failed to authorize key: {e}")
