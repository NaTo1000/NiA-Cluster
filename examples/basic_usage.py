#!/usr/bin/env python3
"""
Simple example of using NiA-Cluster programmatically
"""

import time
import logging
from nia_cluster import ClusterManager

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def main():
    print("NiA-Cluster Basic Example")
    print("-" * 50)
    
    # Initialize cluster manager
    print("\n1. Initializing cluster manager...")
    manager = ClusterManager()
    
    # Start all services
    print("\n2. Starting cluster services...")
    manager.start()
    
    # Run for a short time
    print("\n3. Cluster running... (will run for 10 seconds)")
    for i in range(10):
        time.sleep(1)
        if i == 5:
            # Get status halfway through
            print("\n   Getting status...")
            status = manager.get_status()
            print(f"   Network running: {status['network']['running']}")
            print(f"   PortmanAI enabled: {status['portman_ai']['enabled']}")
            print(f"   JessicAI enabled: {status['jessica_ai']['enabled']}")
    
    # Stop all services
    print("\n4. Stopping cluster services...")
    manager.stop()
    
    print("\n✓ Example completed successfully!")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    except Exception as e:
        print(f"\n✗ Error: {e}")
