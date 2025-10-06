#!/usr/bin/env python3
"""
Example of using PortmanAI for port monitoring
"""

import time
import logging
from nia_cluster.config import ConfigManager
from nia_cluster.ai import PortmanAI

logging.basicConfig(level=logging.INFO)

def main():
    print("PortmanAI Monitoring Example")
    print("-" * 50)
    
    # Create configuration
    config = ConfigManager()
    config.set('ai.portman.enabled', True)
    config.set('ai.portman.monitoring_interval', 2)
    
    # Create PortmanAI instance
    print("\n1. Initializing PortmanAI...")
    portman = PortmanAI(config)
    
    # Start monitoring
    print("\n2. Starting port monitoring...")
    portman.start_monitoring()
    
    # Monitor for a while
    print("\n3. Monitoring ports for 10 seconds...")
    for i in range(5):
        time.sleep(2)
        status = portman.get_status()
        print(f"   [{i+1}/5] Monitoring interval: {status['monitoring_interval']}s, "
              f"Running: {status['running']}")
    
    # Stop monitoring
    print("\n4. Stopping monitoring...")
    portman.stop_monitoring()
    
    print("\n✓ Example completed!")

if __name__ == '__main__':
    main()
