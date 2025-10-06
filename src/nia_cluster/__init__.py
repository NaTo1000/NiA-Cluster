"""
NiA-Cluster: Advanced networking cluster tool with AI integration

A comprehensive networking solution supporting WiFi, Bluetooth, ESP-32,
VLAN management, and AI-powered monitoring and security.
"""

__version__ = "1.0.0"
__author__ = "NiA"

from .cluster.manager import ClusterManager
from .network.wifi import WiFiManager
from .network.bluetooth import BluetoothManager
from .ai.portman import PortmanAI
from .ai.jessica import JessicaAI

__all__ = [
    "ClusterManager",
    "WiFiManager", 
    "BluetoothManager",
    "PortmanAI",
    "JessicaAI",
]
