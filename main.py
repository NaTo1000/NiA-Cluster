#!/usr/bin/env python3
"""
NiA-Cluster: Internal wifi ble esp clustering manager with port control and security
"""
import argparse
import sys
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class RelayServer:
    """Relay server for cluster communication"""
    
    def __init__(self, host, port):
        self.host = host
        self.port = port
        
    def start(self):
        logger.info(f"Starting relay server on {self.host}:{self.port}")
        # Placeholder for relay server implementation
        try:
            import socket
            import threading
            
            server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server.bind((self.host, int(self.port)))
            server.listen(5)
            logger.info(f"Relay server listening on {self.host}:{self.port}")
            
            while True:
                try:
                    client, address = server.accept()
                    logger.info(f"Connection from {address}")
                    # Handle client connection
                    client.close()
                except KeyboardInterrupt:
                    break
                except Exception as e:
                    logger.error(f"Error handling connection: {e}")
        except Exception as e:
            logger.error(f"Failed to start relay server: {e}")
            sys.exit(1)


class ClusterNode:
    """Cluster node for distributed operations"""
    
    def __init__(self, cluster, node, relay_host, relay_port, lan_port, enable_ble=False):
        self.cluster = cluster
        self.node = node
        self.relay_host = relay_host
        self.relay_port = relay_port
        self.lan_port = lan_port
        self.enable_ble = enable_ble
        
    def start(self):
        logger.info(f"Starting node {self.node} in cluster {self.cluster}")
        logger.info(f"Connecting to relay at {self.relay_host}:{self.relay_port}")
        logger.info(f"LAN port: {self.lan_port}")
        if self.enable_ble:
            logger.info("BLE enabled")
        
        # Placeholder for node implementation
        try:
            import socket
            import time
            
            while True:
                try:
                    # Try to connect to relay server
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.connect((self.relay_host, int(self.relay_port)))
                    logger.info(f"Connected to relay server")
                    sock.close()
                    break
                except Exception as e:
                    logger.warning(f"Could not connect to relay: {e}. Retrying in 5 seconds...")
                    time.sleep(5)
            
            # Keep the node running
            logger.info(f"Node {self.node} is running")
            while True:
                time.sleep(10)
                
        except KeyboardInterrupt:
            logger.info("Node shutting down")
        except Exception as e:
            logger.error(f"Node error: {e}")
            sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description='NiA-Cluster Manager')
    parser.add_argument('--mode', required=True, choices=['relay-server', 'node'],
                        help='Operation mode')
    parser.add_argument('--host', help='Host address for relay server')
    parser.add_argument('--port', help='Port for relay server')
    parser.add_argument('--cluster', help='Cluster name for node')
    parser.add_argument('--node', help='Node name')
    parser.add_argument('--relay-host', help='Relay server host for node')
    parser.add_argument('--relay-port', help='Relay server port for node')
    parser.add_argument('--lan-port', help='LAN port for node')
    parser.add_argument('--enable-ble', action='store_true', help='Enable BLE support')
    
    args = parser.parse_args()
    
    if args.mode == 'relay-server':
        if not args.host or not args.port:
            logger.error("Relay server requires --host and --port")
            sys.exit(1)
        
        relay = RelayServer(args.host, args.port)
        relay.start()
        
    elif args.mode == 'node':
        if not all([args.cluster, args.node, args.relay_host, args.relay_port, args.lan_port]):
            logger.error("Node mode requires --cluster, --node, --relay-host, --relay-port, and --lan-port")
            sys.exit(1)
        
        node = ClusterNode(
            args.cluster, 
            args.node, 
            args.relay_host, 
            args.relay_port, 
            args.lan_port,
            args.enable_ble
        )
        node.start()


if __name__ == '__main__':
    main()
