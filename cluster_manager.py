#!/usr/bin/env python3
"""
NiA-Cluster Manager
Internal WiFi/BLE ESP clustering manager with port control and security
"""
import argparse
import asyncio
import json
import logging
import sys
from datetime import datetime
from typing import Set, Dict, Optional

try:
    import websockets
except ImportError:
    print("Error: websockets library not installed. Run: pip install websockets")
    sys.exit(1)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ClusterRelay:
    """Relay server for cluster coordination"""
    
    def __init__(self, port: int, cluster_name: str):
        self.port = port
        self.cluster_name = cluster_name
        self.nodes: Dict[str, websockets.WebSocketServerProtocol] = {}
        self.node_info: Dict[str, dict] = {}
        
    async def register_node(self, websocket, node_name: str, node_data: dict):
        """Register a node with the relay"""
        self.nodes[node_name] = websocket
        self.node_info[node_name] = {
            'name': node_name,
            'connected_at': datetime.now().isoformat(),
            'lan_port': node_data.get('lan_port'),
            'ble_enabled': node_data.get('ble_enabled', False),
            'cluster': node_data.get('cluster', self.cluster_name)
        }
        logger.info(f"Node '{node_name}' registered (BLE: {node_data.get('ble_enabled', False)})")
        
        # Broadcast node list to all connected nodes
        await self.broadcast_node_list()
    
    async def unregister_node(self, node_name: str):
        """Unregister a node from the relay"""
        if node_name in self.nodes:
            del self.nodes[node_name]
        if node_name in self.node_info:
            del self.node_info[node_name]
        logger.info(f"Node '{node_name}' unregistered")
        
        # Broadcast updated node list
        await self.broadcast_node_list()
    
    async def broadcast_node_list(self):
        """Broadcast current node list to all connected nodes"""
        message = {
            'type': 'node_list',
            'nodes': self.node_info
        }
        disconnected = []
        for node_name, ws in self.nodes.items():
            try:
                await ws.send(json.dumps(message))
            except Exception as e:
                logger.error(f"Failed to send to {node_name}: {e}")
                disconnected.append(node_name)
        
        # Clean up disconnected nodes
        for node_name in disconnected:
            await self.unregister_node(node_name)
    
    async def handle_node(self, websocket, path):
        """Handle incoming node connections"""
        node_name = None
        try:
            # Wait for registration message
            async for message in websocket:
                data = json.loads(message)
                
                if data.get('type') == 'register':
                    node_name = data.get('node_name')
                    await self.register_node(websocket, node_name, data)
                    
                    # Send acknowledgment
                    await websocket.send(json.dumps({
                        'type': 'registered',
                        'node_name': node_name,
                        'cluster': self.cluster_name
                    }))
                    
                elif data.get('type') == 'heartbeat':
                    # Respond to heartbeat
                    await websocket.send(json.dumps({
                        'type': 'heartbeat_ack',
                        'timestamp': datetime.now().isoformat()
                    }))
                    
                elif data.get('type') == 'message':
                    # Forward messages between nodes
                    target = data.get('target')
                    if target and target in self.nodes:
                        await self.nodes[target].send(json.dumps(data))
                    else:
                        await websocket.send(json.dumps({
                            'type': 'error',
                            'message': f'Target node {target} not found'
                        }))
                        
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"Node connection closed: {node_name}")
        except Exception as e:
            logger.error(f"Error handling node: {e}")
        finally:
            if node_name:
                await self.unregister_node(node_name)
    
    async def start(self):
        """Start the relay server"""
        logger.info(f"Starting relay server for cluster '{self.cluster_name}' on port {self.port}")
        async with websockets.serve(self.handle_node, "0.0.0.0", self.port):
            logger.info(f"Relay server running on ws://0.0.0.0:{self.port}")
            await asyncio.Future()  # Run forever


class ClusterNode:
    """Cluster node with optional BLE support"""
    
    def __init__(self, cluster_name: str, node_name: str, relay_host: str, 
                 relay_port: int, lan_port: int, enable_ble: bool = False):
        self.cluster_name = cluster_name
        self.node_name = node_name
        self.relay_host = relay_host
        self.relay_port = relay_port
        self.lan_port = lan_port
        self.enable_ble = enable_ble
        self.websocket = None
        self.connected = False
        self.peer_nodes: Dict[str, dict] = {}
        
    async def connect_to_relay(self):
        """Connect to the relay server"""
        relay_url = f"ws://{self.relay_host}:{self.relay_port}"
        logger.info(f"Connecting to relay at {relay_url}")
        
        try:
            self.websocket = await websockets.connect(relay_url)
            self.connected = True
            
            # Register with the relay
            await self.websocket.send(json.dumps({
                'type': 'register',
                'node_name': self.node_name,
                'cluster': self.cluster_name,
                'lan_port': self.lan_port,
                'ble_enabled': self.enable_ble
            }))
            
            logger.info(f"Node '{self.node_name}' connected to relay")
            
            # Wait for registration confirmation
            response = await self.websocket.recv()
            data = json.loads(response)
            
            if data.get('type') == 'registered':
                logger.info(f"Successfully registered with cluster '{data.get('cluster')}'")
                if self.enable_ble:
                    logger.info("BLE support enabled")
            
        except Exception as e:
            logger.error(f"Failed to connect to relay: {e}")
            self.connected = False
            raise
    
    async def handle_messages(self):
        """Handle incoming messages from the relay"""
        try:
            async for message in self.websocket:
                data = json.loads(message)
                msg_type = data.get('type')
                
                if msg_type == 'node_list':
                    self.peer_nodes = data.get('nodes', {})
                    # Remove self from peer list
                    self.peer_nodes.pop(self.node_name, None)
                    logger.info(f"Updated peer list: {list(self.peer_nodes.keys())}")
                    
                elif msg_type == 'heartbeat_ack':
                    logger.debug(f"Heartbeat acknowledged at {data.get('timestamp')}")
                    
                elif msg_type == 'message':
                    logger.info(f"Received message from {data.get('source')}: {data.get('payload')}")
                    
                elif msg_type == 'error':
                    logger.error(f"Error from relay: {data.get('message')}")
                    
        except websockets.exceptions.ConnectionClosed:
            logger.info("Connection to relay closed")
            self.connected = False
        except Exception as e:
            logger.error(f"Error handling messages: {e}")
            self.connected = False
    
    async def send_heartbeat(self):
        """Send periodic heartbeat to relay"""
        while self.connected:
            try:
                await self.websocket.send(json.dumps({
                    'type': 'heartbeat',
                    'node_name': self.node_name
                }))
                await asyncio.sleep(30)  # Send heartbeat every 30 seconds
            except Exception as e:
                logger.error(f"Failed to send heartbeat: {e}")
                break
    
    async def start(self):
        """Start the node"""
        logger.info(f"Starting node '{self.node_name}' in cluster '{self.cluster_name}'")
        logger.info(f"LAN port: {self.lan_port}, BLE: {'enabled' if self.enable_ble else 'disabled'}")
        
        await self.connect_to_relay()
        
        # Run message handler and heartbeat in parallel
        await asyncio.gather(
            self.handle_messages(),
            self.send_heartbeat()
        )


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='NiA-Cluster Manager - WiFi/BLE ESP clustering system'
    )
    
    parser.add_argument('--mode', required=True, choices=['relay', 'node'],
                        help='Operation mode: relay or node')
    parser.add_argument('--cluster', required=True,
                        help='Cluster name')
    
    # Relay-specific arguments
    parser.add_argument('--relay-port', type=int, default=4040,
                        help='Relay server port (relay mode) or relay port to connect to (node mode)')
    
    # Node-specific arguments
    parser.add_argument('--node', 
                        help='Node name (required in node mode)')
    parser.add_argument('--relay-host', 
                        help='Relay server hostname (required in node mode)')
    parser.add_argument('--lan-port', type=int,
                        help='Node LAN port (required in node mode)')
    parser.add_argument('--enable-ble', action='store_true',
                        help='Enable BLE support (node mode)')
    
    parser.add_argument('--debug', action='store_true',
                        help='Enable debug logging')
    
    args = parser.parse_args()
    
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        if args.mode == 'relay':
            # Start relay server
            relay = ClusterRelay(args.relay_port, args.cluster)
            asyncio.run(relay.start())
            
        elif args.mode == 'node':
            # Validate node-specific arguments
            if not args.node:
                parser.error("--node is required in node mode")
            if not args.relay_host:
                parser.error("--relay-host is required in node mode")
            if not args.lan_port:
                parser.error("--lan-port is required in node mode")
            
            # Start node
            node = ClusterNode(
                args.cluster,
                args.node,
                args.relay_host,
                args.relay_port,
                args.lan_port,
                args.enable_ble
            )
            asyncio.run(node.start())
            
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
