"""
VLAN management module for network segmentation
"""

import logging
import subprocess
import platform
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class VLANManager:
    """Manages VLAN configuration and segmentation"""
    
    def __init__(self):
        self.platform = platform.system()
        self.vlans: Dict[int, Dict] = {}
        
    def create_vlan(self, vlan_id: int, interface: str, name: Optional[str] = None) -> bool:
        """
        Create a new VLAN
        
        Args:
            vlan_id: VLAN ID (1-4094)
            interface: Physical interface name
            name: Optional VLAN name
        """
        if not (1 <= vlan_id <= 4094):
            logger.error(f"Invalid VLAN ID: {vlan_id}. Must be between 1 and 4094.")
            return False
        
        vlan_name = name or f"vlan{vlan_id}"
        logger.info(f"Creating VLAN {vlan_id} on interface {interface}")
        
        try:
            if self.platform == "Linux":
                success = self._create_vlan_linux(vlan_id, interface, vlan_name)
            elif self.platform == "Windows":
                success = self._create_vlan_windows(vlan_id, interface, vlan_name)
            else:
                logger.error(f"VLAN creation not supported on {self.platform}")
                return False
            
            if success:
                self.vlans[vlan_id] = {
                    "interface": interface,
                    "name": vlan_name,
                    "id": vlan_id
                }
                logger.info(f"Created VLAN {vlan_id}")
                
            return success
            
        except Exception as e:
            logger.error(f"Failed to create VLAN: {e}")
            return False
    
    def _create_vlan_linux(self, vlan_id: int, interface: str, name: str) -> bool:
        """Create VLAN on Linux using ip command"""
        try:
            vlan_interface = f"{interface}.{vlan_id}"
            
            # Create VLAN interface
            result = subprocess.run(
                ["ip", "link", "add", "link", interface, "name", vlan_interface,
                 "type", "vlan", "id", str(vlan_id)],
                capture_output=True,
                timeout=10
            )
            
            if result.returncode != 0:
                logger.error(f"Failed to create VLAN interface: {result.stderr.decode()}")
                return False
            
            # Bring interface up
            subprocess.run(
                ["ip", "link", "set", vlan_interface, "up"],
                capture_output=True,
                timeout=10
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Linux VLAN creation failed: {e}")
            return False
    
    def _create_vlan_windows(self, vlan_id: int, interface: str, name: str) -> bool:
        """Create VLAN on Windows (requires admin privileges)"""
        try:
            # Windows VLAN configuration typically requires PowerShell
            ps_command = f"""
            New-NetLbfoTeamNic -Team "{interface}" -VlanID {vlan_id} -Name "{name}"
            """
            
            result = subprocess.run(
                ["powershell", "-Command", ps_command],
                capture_output=True,
                timeout=30
            )
            
            return result.returncode == 0
            
        except Exception as e:
            logger.error(f"Windows VLAN creation failed: {e}")
            return False
    
    def delete_vlan(self, vlan_id: int) -> bool:
        """Delete a VLAN"""
        if vlan_id not in self.vlans:
            logger.warning(f"VLAN {vlan_id} not found")
            return False
        
        vlan_info = self.vlans[vlan_id]
        logger.info(f"Deleting VLAN {vlan_id}")
        
        try:
            if self.platform == "Linux":
                success = self._delete_vlan_linux(vlan_id, vlan_info["interface"])
            elif self.platform == "Windows":
                success = self._delete_vlan_windows(vlan_id, vlan_info["name"])
            else:
                logger.error(f"VLAN deletion not supported on {self.platform}")
                return False
            
            if success:
                del self.vlans[vlan_id]
                logger.info(f"Deleted VLAN {vlan_id}")
                
            return success
            
        except Exception as e:
            logger.error(f"Failed to delete VLAN: {e}")
            return False
    
    def _delete_vlan_linux(self, vlan_id: int, interface: str) -> bool:
        """Delete VLAN on Linux"""
        try:
            vlan_interface = f"{interface}.{vlan_id}"
            
            result = subprocess.run(
                ["ip", "link", "delete", vlan_interface],
                capture_output=True,
                timeout=10
            )
            
            return result.returncode == 0
            
        except Exception as e:
            logger.error(f"Linux VLAN deletion failed: {e}")
            return False
    
    def _delete_vlan_windows(self, vlan_id: int, name: str) -> bool:
        """Delete VLAN on Windows"""
        try:
            ps_command = f'Remove-NetLbfoTeamNic -Name "{name}"'
            
            result = subprocess.run(
                ["powershell", "-Command", ps_command],
                capture_output=True,
                timeout=30
            )
            
            return result.returncode == 0
            
        except Exception as e:
            logger.error(f"Windows VLAN deletion failed: {e}")
            return False
    
    def list_vlans(self) -> List[Dict]:
        """Get list of configured VLANs"""
        return list(self.vlans.values())
    
    def get_vlan(self, vlan_id: int) -> Optional[Dict]:
        """Get VLAN information"""
        return self.vlans.get(vlan_id)
    
    def assign_ip(self, vlan_id: int, ip_address: str, netmask: str = "255.255.255.0") -> bool:
        """
        Assign IP address to VLAN interface
        
        Args:
            vlan_id: VLAN ID
            ip_address: IP address to assign
            netmask: Network mask
        """
        if vlan_id not in self.vlans:
            logger.error(f"VLAN {vlan_id} not found")
            return False
        
        vlan_info = self.vlans[vlan_id]
        logger.info(f"Assigning IP {ip_address} to VLAN {vlan_id}")
        
        try:
            if self.platform == "Linux":
                vlan_interface = f"{vlan_info['interface']}.{vlan_id}"
                
                # Calculate CIDR notation
                cidr = self._netmask_to_cidr(netmask)
                
                result = subprocess.run(
                    ["ip", "addr", "add", f"{ip_address}/{cidr}", "dev", vlan_interface],
                    capture_output=True,
                    timeout=10
                )
                
                return result.returncode == 0
                
            elif self.platform == "Windows":
                ps_command = f"""
                New-NetIPAddress -InterfaceAlias "{vlan_info['name']}" `
                    -IPAddress {ip_address} -PrefixLength {self._netmask_to_cidr(netmask)}
                """
                
                result = subprocess.run(
                    ["powershell", "-Command", ps_command],
                    capture_output=True,
                    timeout=30
                )
                
                return result.returncode == 0
                
        except Exception as e:
            logger.error(f"Failed to assign IP: {e}")
            return False
    
    def _netmask_to_cidr(self, netmask: str) -> int:
        """Convert netmask to CIDR notation"""
        return sum([bin(int(x)).count('1') for x in netmask.split('.')])
