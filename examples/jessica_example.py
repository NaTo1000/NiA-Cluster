#!/usr/bin/env python3
"""
Example of using JessicAI for voice commands and security
"""

import logging
from nia_cluster.config import ConfigManager
from nia_cluster.ai import JessicAI

logging.basicConfig(level=logging.INFO)

def main():
    print("JessicAI Security & Voice Control Example")
    print("-" * 50)
    
    # Create configuration
    config = ConfigManager()
    config.set('ai.jessica.enabled', True)
    config.set('ai.jessica.notifications.email', True)
    
    # Create JessicAI instance
    print("\n1. Initializing JessicAI...")
    jessica = JessicAI(config)
    
    # Start services
    print("\n2. Starting JessicAI services...")
    jessica.start()
    
    # Test voice commands
    print("\n3. Testing voice commands...")
    commands = ["status", "help", "shutdown", "unknown command"]
    
    for cmd in commands:
        print(f"\n   Command: '{cmd}'")
        response = jessica.process_voice_command(cmd)
        print(f"   Response: {response}")
    
    # Test security event handling
    print("\n4. Testing security event handling...")
    test_event = {
        "type": "intrusion_attempt",
        "source": "192.168.1.100",
        "port": 22
    }
    
    print(f"   Event: {test_event}")
    jessica.handle_security_event(test_event)
    
    # Send test notification
    print("\n5. Sending test notification...")
    jessica.send_notification("Test notification from JessicAI", "email")
    
    # Stop services
    print("\n6. Stopping JessicAI...")
    jessica.stop()
    
    print("\n✓ Example completed!")

if __name__ == '__main__':
    main()
