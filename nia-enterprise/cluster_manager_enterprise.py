#!/usr/bin/env python3
"""
NiA-Enterprise Cluster Manager
Enterprise-grade WiFi/BLE ESP clustering manager with advanced security and monitoring

Features:
- High-performance packet sharding and reforming
- Optimized double packet shuffle for transmission efficiency
- Quantum superposition-inspired routing optimization
"""
import argparse
import asyncio
import json
import logging
import sys
import ssl
import time
from datetime import datetime
from typing import Set, Dict, Optional, List
from pathlib import Path

try:
    import websockets
    from websockets import WebSocketServerProtocol
except ImportError:
    print("Error: websockets library not installed. Run: pip install websockets")
    sys.exit(1)

try:
    from packet_sharding import (
        PacketShardManager,
        PacketShard,
        create_sharding_system
    )
    SHARDING_AVAILABLE = True
except ImportError:
    SHARDING_AVAILABLE = False
    print("Warning: packet_sharding module not available. Sharding disabled.")

try:
    from prometheus_client import Counter, Gauge, Histogram, start_http_server
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    print("Warning: prometheus_client not installed. Metrics disabled.")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Prometheus metrics
if PROMETHEUS_AVAILABLE:
    NODE_CONNECTIONS = Gauge('nia_node_connections', 'Number of connected nodes')
    MESSAGE_COUNTER = Counter('nia_messages_total', 'Total messages processed', ['type'])
    RESPONSE_TIME = Histogram('nia_response_time_seconds', 'Response time in seconds')
    AUTH_FAILURES = Counter('nia_auth_failures_total', 'Total authentication failures')
    SHARDS_PROCESSED = Counter('nia_shards_processed_total', 'Total shards processed')
    PACKETS_REFORMED = Counter('nia_packets_reformed_total', 'Total packets reformed from shards')


# Default sharding configuration
DEFAULT_SHARD_SIZE = 1024  # bytes
DEFAULT_SHUFFLE_BLOCK_SIZE = 8


class SecurityManager:
    """Manages authentication and authorization"""
    
    def __init__(self, api_keys: Optional[Dict[str, str]] = None):
        self.api_keys = api_keys or {}
        self.audit_log = []
        
    def validate_api_key(self, api_key: str) -> bool:
        """Validate API key"""
        is_valid = api_key in self.api_keys.values()
        if not is_valid and PROMETHEUS_AVAILABLE:
            AUTH_FAILURES.inc()
        return is_valid
    
    def audit_log_event(self, event_type: str, user: str, details: dict):
        """Log security event for audit"""
        event = {
            'timestamp': datetime.now().isoformat(),
            'type': event_type,
            'user': user,
            'details': details
        }
        self.audit_log.append(event)
        logger.info(f"AUDIT: {event_type} by {user}: {details}")


class EnterpriseClusterRelay:
    """Enterprise relay server with HA, monitoring, and packet sharding"""
    
    def __init__(self, port: int, cluster_name: str, enable_tls: bool = False,
                 tls_cert: Optional[str] = None, tls_key: Optional[str] = None,
                 api_keys: Optional[Dict[str, str]] = None, ha_enabled: bool = False,
                 peer_relays: Optional[list] = None, enable_sharding: bool = True,
                 shard_size: int = DEFAULT_SHARD_SIZE,
                 shuffle_block_size: int = DEFAULT_SHUFFLE_BLOCK_SIZE):
        self.port = port
        self.cluster_name = cluster_name
        self.enable_tls = enable_tls
        self.tls_cert = tls_cert
        self.tls_key = tls_key
        self.ha_enabled = ha_enabled
        self.peer_relays = peer_relays or []
        self.enable_sharding = enable_sharding and SHARDING_AVAILABLE
        
        self.nodes: Dict[str, WebSocketServerProtocol] = {}
        self.node_info: Dict[str, dict] = {}
        self.security = SecurityManager(api_keys)
        
        # Initialize packet sharding system if enabled
        if self.enable_sharding:
            self.shard_manager = create_sharding_system(
                shard_size=shard_size,
                shuffle_block_size=shuffle_block_size
            )
            logger.info(f"Packet sharding enabled (shard_size={shard_size}, "
                       f"shuffle_block_size={shuffle_block_size})")
        else:
            self.shard_manager = None
        
        # Metrics
        self.start_time = time.time()
        self.message_count = 0
        
    async def register_node(self, websocket, node_name: str, node_data: dict):
        """Register a node with the relay"""
        # Authenticate if API key provided
        api_key = node_data.get('api_key')
        if api_key and not self.security.validate_api_key(api_key):
            logger.warning(f"Authentication failed for node '{node_name}'")
            await websocket.send(json.dumps({
                'type': 'error',
                'message': 'Authentication failed'
            }))
            return False
            
        self.nodes[node_name] = websocket
        self.node_info[node_name] = {
            'name': node_name,
            'connected_at': datetime.now().isoformat(),
            'lan_port': node_data.get('lan_port'),
            'ble_enabled': node_data.get('ble_enabled', False),
            'cluster': node_data.get('cluster', self.cluster_name),
            'version': node_data.get('version', 'unknown'),
            'health': 'healthy'
        }
        
        logger.info(f"Node '{node_name}' registered (BLE: {node_data.get('ble_enabled', False)}, "
                   f"Version: {node_data.get('version', 'unknown')})")
        
        # Update metrics
        if PROMETHEUS_AVAILABLE:
            NODE_CONNECTIONS.set(len(self.nodes))
            MESSAGE_COUNTER.labels(type='registration').inc()
        
        # Audit log
        self.security.audit_log_event('node_registration', node_name, {
            'cluster': self.cluster_name,
            'ble_enabled': node_data.get('ble_enabled', False)
        })
        
        # Broadcast node list to all connected nodes
        await self.broadcast_node_list()
        return True
        
    async def unregister_node(self, node_name: str):
        """Unregister a node"""
        if node_name in self.nodes:
            del self.nodes[node_name]
            del self.node_info[node_name]
            logger.info(f"Node '{node_name}' unregistered")
            
            if PROMETHEUS_AVAILABLE:
                NODE_CONNECTIONS.set(len(self.nodes))
            
            await self.broadcast_node_list()
    
    async def broadcast_node_list(self):
        """Broadcast current node list to all connected nodes"""
        node_list = {
            'type': 'node_list',
            'nodes': list(self.node_info.values()),
            'timestamp': datetime.now().isoformat()
        }
        
        message = json.dumps(node_list)
        disconnected = []
        
        for node_name, websocket in self.nodes.items():
            try:
                await websocket.send(message)
            except Exception as e:
                logger.error(f"Failed to send to {node_name}: {e}")
                disconnected.append(node_name)
        
        # Clean up disconnected nodes
        for node_name in disconnected:
            await self.unregister_node(node_name)
    
    async def handle_client(self, websocket, path):
        """Handle client connection"""
        node_name = None
        try:
            async for message in websocket:
                data = json.loads(message)
                msg_type = data.get('type')
                
                if PROMETHEUS_AVAILABLE:
                    MESSAGE_COUNTER.labels(type=msg_type).inc()
                
                if msg_type == 'register':
                    node_name = data.get('node_name')
                    success = await self.register_node(websocket, node_name, data)
                    if not success:
                        break
                        
                elif msg_type == 'heartbeat':
                    # Update node health
                    node_name = data.get('node_name')
                    if node_name in self.node_info:
                        self.node_info[node_name]['last_heartbeat'] = datetime.now().isoformat()
                        self.node_info[node_name]['health'] = data.get('health', 'healthy')
                    
                    # Send heartbeat response
                    await websocket.send(json.dumps({
                        'type': 'heartbeat_ack',
                        'timestamp': datetime.now().isoformat()
                    }))
                    
                elif msg_type == 'message':
                    # Relay message to target node
                    target = data.get('target')
                    if target in self.nodes:
                        await self.nodes[target].send(json.dumps({
                            'type': 'message',
                            'from': node_name,
                            'data': data.get('data'),
                            'timestamp': datetime.now().isoformat()
                        }))
                
                elif msg_type == 'sharded_message':
                    # Handle sharded message transmission with quantum optimization
                    await self._handle_sharded_message(websocket, node_name, data)
                
                elif msg_type == 'shard':
                    # Handle individual shard reception
                    await self._handle_shard_reception(websocket, node_name, data)
                        
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"Connection closed for node '{node_name}'")
        except Exception as e:
            logger.error(f"Error handling client: {e}")
        finally:
            if node_name:
                await self.unregister_node(node_name)
    
    async def _handle_sharded_message(self, websocket, node_name: str, data: dict):
        """
        Handle a sharded message transmission request.
        
        Shards the message payload using double packet shuffle with
        quantum superposition optimization and sends to target.
        """
        if not self.enable_sharding or not self.shard_manager:
            # Fall back to regular message handling
            target = data.get('target')
            if target in self.nodes:
                await self.nodes[target].send(json.dumps({
                    'type': 'message',
                    'from': node_name,
                    'data': data.get('data'),
                    'timestamp': datetime.now().isoformat()
                }))
            return
        
        target = data.get('target')
        payload = data.get('data', '')
        priority = data.get('priority', 0)
        
        if target not in self.nodes:
            await websocket.send(json.dumps({
                'type': 'error',
                'message': f'Target node {target} not found'
            }))
            return
        
        # Convert payload to bytes if necessary
        if isinstance(payload, str):
            payload_bytes = payload.encode('utf-8')
        elif isinstance(payload, dict):
            payload_bytes = json.dumps(payload).encode('utf-8')
        else:
            payload_bytes = bytes(payload)
        
        # Shard the packet using quantum-optimized double shuffle
        shards = self.shard_manager.shard_packet(payload_bytes, priority=priority)
        prepared_shards = self.shard_manager.prepare_for_transmission(shards)
        
        # Get optimal route using quantum superposition collapse
        packet_id = shards[0].packet_id if shards else None
        if packet_id:
            route = self.shard_manager.get_optimal_route(packet_id)
            logger.debug(f"Quantum-optimized route {route} selected for packet {packet_id[:8]}")
        
        # Send each shard to the target
        start_time = time.time()
        for shard in prepared_shards:
            shard_message = {
                'type': 'shard',
                'from': node_name,
                'shard': shard.to_dict(),
                'timestamp': datetime.now().isoformat()
            }
            await self.nodes[target].send(json.dumps(shard_message))
            
            if PROMETHEUS_AVAILABLE:
                SHARDS_PROCESSED.inc()
        
        # Record transmission result for quantum optimization
        latency_ms = (time.time() - start_time) * 1000
        if packet_id:
            self.shard_manager.record_transmission_result(packet_id, 0, latency_ms)
        
        logger.info(f"Sent {len(prepared_shards)} shards to {target} "
                   f"(packet {packet_id[:8] if packet_id else 'unknown'}, {latency_ms:.2f}ms)")
        
        # Acknowledge transmission to sender
        await websocket.send(json.dumps({
            'type': 'sharded_message_sent',
            'packet_id': packet_id,
            'shards_sent': len(prepared_shards),
            'target': target,
            'latency_ms': latency_ms,
            'timestamp': datetime.now().isoformat()
        }))
    
    async def _handle_shard_reception(self, websocket, node_name: str, data: dict):
        """
        Handle reception of an individual shard.
        
        Receives shards and attempts to reform complete packets.
        """
        if not self.enable_sharding or not self.shard_manager:
            logger.warning("Received shard but sharding is disabled")
            return
        
        shard_data = data.get('shard')
        if not shard_data:
            logger.warning("Received shard message without shard data")
            return
        
        try:
            shard = PacketShard.from_dict(shard_data)
            
            if PROMETHEUS_AVAILABLE:
                SHARDS_PROCESSED.inc()
            
            # Attempt to reform the packet
            reformed_data = self.shard_manager.receive_shard(shard)
            
            if reformed_data is not None:
                # Packet is complete, notify the receiver
                if PROMETHEUS_AVAILABLE:
                    PACKETS_REFORMED.inc()
                
                logger.info(f"Reformed packet {shard.packet_id[:8]}: {len(reformed_data)} bytes")
                
                await websocket.send(json.dumps({
                    'type': 'packet_reformed',
                    'packet_id': shard.packet_id,
                    'data': reformed_data.decode('utf-8', errors='replace'),
                    'size': len(reformed_data),
                    'timestamp': datetime.now().isoformat()
                }))
            
        except Exception as e:
            logger.error(f"Error processing shard: {e}")
    
    async def health_check_server(self):
        """Simple HTTP health check endpoint"""
        from aiohttp import web
        
        async def health(request):
            response = {
                'status': 'healthy',
                'cluster': self.cluster_name,
                'nodes_connected': len(self.nodes),
                'uptime_seconds': int(time.time() - self.start_time),
                'version': '1.0.0-enterprise',
                'sharding_enabled': self.enable_sharding
            }
            
            # Add sharding stats if enabled
            if self.enable_sharding and self.shard_manager:
                response['pending_packets'] = self.shard_manager.get_pending_packets_count()
            
            return web.json_response(response)
        
        app = web.Application()
        app.router.add_get('/health', health)
        app.router.add_get('/healthz', health)
        
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, '0.0.0.0', 8080)
        await site.start()
        logger.info("Health check endpoint started on port 8080")
    
    async def start(self):
        """Start the relay server"""
        # Start health check server
        asyncio.create_task(self.health_check_server())
        
        # Start Prometheus metrics server
        if PROMETHEUS_AVAILABLE:
            start_http_server(9090)
            logger.info("Prometheus metrics server started on port 9090")
        
        # Configure SSL if enabled
        ssl_context = None
        if self.enable_tls:
            ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            if self.tls_cert and self.tls_key:
                ssl_context.load_cert_chain(self.tls_cert, self.tls_key)
                logger.info("TLS enabled with provided certificates")
        
        logger.info(f"Starting Enterprise Relay server on port {self.port}")
        logger.info(f"Cluster: {self.cluster_name}")
        logger.info(f"TLS: {'enabled' if self.enable_tls else 'disabled'}")
        logger.info(f"HA Mode: {'enabled' if self.ha_enabled else 'disabled'}")
        logger.info(f"Packet Sharding: {'enabled' if self.enable_sharding else 'disabled'}")
        
        async with websockets.serve(
            self.handle_client,
            '0.0.0.0',
            self.port,
            ssl=ssl_context
        ):
            logger.info(f"Enterprise Relay server running on port {self.port}")
            await asyncio.Future()  # Run forever


class EnterpriseClusterNode:
    """Enterprise cluster node with advanced monitoring and packet sharding"""
    
    def __init__(self, cluster_name: str, node_name: str, relay_host: str,
                 relay_port: int, lan_port: int, enable_ble: bool = False,
                 api_key: Optional[str] = None, enable_tls: bool = False,
                 version: str = "1.0.0-enterprise", enable_sharding: bool = True,
                 shard_size: int = DEFAULT_SHARD_SIZE,
                 shuffle_block_size: int = DEFAULT_SHUFFLE_BLOCK_SIZE):
        self.cluster_name = cluster_name
        self.node_name = node_name
        self.relay_host = relay_host
        self.relay_port = relay_port
        self.lan_port = lan_port
        self.enable_ble = enable_ble
        self.api_key = api_key
        self.enable_tls = enable_tls
        self.version = version
        self.enable_sharding = enable_sharding and SHARDING_AVAILABLE
        self.websocket = None
        self.connected = False
        self.peer_nodes: Dict[str, dict] = {}
        
        # Initialize packet sharding system if enabled
        if self.enable_sharding:
            self.shard_manager = create_sharding_system(
                shard_size=shard_size,
                shuffle_block_size=shuffle_block_size
            )
            logger.info(f"Node packet sharding enabled (shard_size={shard_size})")
        else:
            self.shard_manager = None
        
    async def send_heartbeat(self):
        """Send periodic heartbeat to relay"""
        while self.connected:
            try:
                await self.websocket.send(json.dumps({
                    'type': 'heartbeat',
                    'node_name': self.node_name,
                    'health': 'healthy',
                    'timestamp': datetime.now().isoformat()
                }))
                await asyncio.sleep(10)  # Heartbeat every 10 seconds
            except Exception as e:
                logger.error(f"Heartbeat failed: {e}")
                break
    
    async def handle_messages(self):
        """Handle incoming messages from relay"""
        try:
            async for message in self.websocket:
                data = json.loads(message)
                msg_type = data.get('type')
                
                if msg_type == 'node_list':
                    self.peer_nodes = {
                        node['name']: node 
                        for node in data.get('nodes', [])
                        if node['name'] != self.node_name
                    }
                    logger.debug(f"Updated peer list: {len(self.peer_nodes)} peers")
                    
                elif msg_type == 'message':
                    logger.info(f"Message from {data.get('from')}: {data.get('data')}")
                    
                elif msg_type == 'heartbeat_ack':
                    logger.debug("Heartbeat acknowledged")
                
                elif msg_type == 'shard':
                    # Handle incoming shard from relay
                    await self._handle_incoming_shard(data)
                
                elif msg_type == 'packet_reformed':
                    # Complete packet has been reformed
                    logger.info(f"Received complete packet {data.get('packet_id', 'unknown')[:8]}: "
                               f"{data.get('size', 0)} bytes")
                
                elif msg_type == 'sharded_message_sent':
                    # Acknowledgment of sharded message transmission
                    logger.debug(f"Sharded message {data.get('packet_id', '')[:8]} sent to "
                                f"{data.get('target')} ({data.get('shards_sent')} shards)")
                    
        except websockets.exceptions.ConnectionClosed:
            logger.info("Connection to relay closed")
            self.connected = False
        except Exception as e:
            logger.error(f"Error handling messages: {e}")
            self.connected = False
    
    async def _handle_incoming_shard(self, data: dict):
        """Handle reception of an individual shard."""
        if not self.enable_sharding or not self.shard_manager:
            logger.warning("Received shard but sharding is disabled on this node")
            return
        
        shard_data = data.get('shard')
        if not shard_data:
            logger.warning("Received shard message without shard data")
            return
        
        try:
            shard = PacketShard.from_dict(shard_data)
            source = data.get('from', 'unknown')
            
            # Attempt to reform the packet
            reformed_data = self.shard_manager.receive_shard(shard)
            
            if reformed_data is not None:
                logger.info(f"Reformed packet {shard.packet_id[:8]} from {source}: "
                           f"{len(reformed_data)} bytes")
                
                # Notify application of complete packet
                await self._on_packet_complete(shard.packet_id, reformed_data, source)
                
        except Exception as e:
            logger.error(f"Error processing incoming shard: {e}")
    
    async def _on_packet_complete(self, packet_id: str, data: bytes, source: str):
        """
        Called when a complete packet has been reformed from shards.
        
        Override this method to handle completed packets in your application.
        """
        # Default implementation just logs the event
        logger.info(f"Complete packet {packet_id[:8]} received from {source}")
    
    async def send_sharded_message(self, target: str, data: bytes, priority: int = 0):
        """
        Send a message using optimized packet sharding.
        
        Uses double packet shuffle with quantum superposition optimization
        for efficient transmission.
        
        Args:
            target: Target node name
            data: Message data to send
            priority: Message priority (higher = more important)
        """
        if not self.connected or not self.websocket:
            raise RuntimeError("Not connected to relay")
        
        message = {
            'type': 'sharded_message',
            'target': target,
            'data': data.decode('utf-8') if isinstance(data, bytes) else data,
            'priority': priority,
            'timestamp': datetime.now().isoformat()
        }
        
        await self.websocket.send(json.dumps(message))
        logger.debug(f"Sent sharded message request to {target}")
    
    async def connect_to_relay(self):
        """Connect to the relay server"""
        try:
            uri = f"{'wss' if self.enable_tls else 'ws'}://{self.relay_host}:{self.relay_port}"
            logger.info(f"Connecting to relay at {uri}")
            
            self.websocket = await websockets.connect(uri)
            
            # Register with relay
            register_data = {
                'type': 'register',
                'node_name': self.node_name,
                'cluster': self.cluster_name,
                'lan_port': self.lan_port,
                'ble_enabled': self.enable_ble,
                'version': self.version,
                'timestamp': datetime.now().isoformat()
            }
            
            if self.api_key:
                register_data['api_key'] = self.api_key
            
            await self.websocket.send(json.dumps(register_data))
            self.connected = True
            
            logger.info(f"Connected to relay successfully (BLE: {self.enable_ble})")
            
            # Start heartbeat and message handling
            await asyncio.gather(
                self.send_heartbeat(),
                self.handle_messages()
            )
            
        except Exception as e:
            logger.error(f"Failed to connect to relay: {e}")
            self.connected = False
            raise
    
    async def start(self):
        """Start the node"""
        logger.info(f"Starting Enterprise Node '{self.node_name}'")
        logger.info(f"Cluster: {self.cluster_name}")
        logger.info(f"BLE: {'enabled' if self.enable_ble else 'disabled'}")
        logger.info(f"Packet Sharding: {'enabled' if self.enable_sharding else 'disabled'}")
        logger.info(f"Version: {self.version}")
        
        await self.connect_to_relay()


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='NiA-Enterprise Cluster Manager - Enterprise WiFi/BLE ESP clustering system'
    )
    
    parser.add_argument('--mode', required=True, choices=['relay', 'node'],
                       help='Operation mode: relay or node')
    parser.add_argument('--cluster', required=True,
                       help='Cluster name')
    
    # Relay-specific arguments
    parser.add_argument('--relay-port', type=int, default=4040,
                       help='Relay server port')
    parser.add_argument('--enable-tls', action='store_true',
                       help='Enable TLS/SSL')
    parser.add_argument('--tls-cert', 
                       help='Path to TLS certificate')
    parser.add_argument('--tls-key',
                       help='Path to TLS private key')
    parser.add_argument('--ha-enabled', action='store_true',
                       help='Enable high availability mode')
    parser.add_argument('--peer-relays',
                       help='Comma-separated list of peer relay hosts')
    parser.add_argument('--api-keys',
                       help='Path to API keys file (JSON)')
    
    # Node-specific arguments
    parser.add_argument('--node',
                       help='Node name (required in node mode)')
    parser.add_argument('--relay-host',
                       help='Relay server hostname (required in node mode)')
    parser.add_argument('--lan-port', type=int,
                       help='Node LAN port (required in node mode)')
    parser.add_argument('--enable-ble', action='store_true',
                       help='Enable BLE support (node mode)')
    parser.add_argument('--api-key',
                       help='API key for authentication')
    
    # Packet sharding arguments
    parser.add_argument('--enable-sharding', action='store_true', default=True,
                       help='Enable packet sharding with quantum optimization (default: enabled)')
    parser.add_argument('--disable-sharding', action='store_true',
                       help='Disable packet sharding')
    parser.add_argument('--shard-size', type=int, default=DEFAULT_SHARD_SIZE,
                       help=f'Shard size in bytes (default: {DEFAULT_SHARD_SIZE})')
    parser.add_argument('--shuffle-block-size', type=int, default=DEFAULT_SHUFFLE_BLOCK_SIZE,
                       help=f'Double shuffle block size (default: {DEFAULT_SHUFFLE_BLOCK_SIZE})')
    
    parser.add_argument('--debug', action='store_true',
                       help='Enable debug logging')
    parser.add_argument('--version', action='version', version='NiA-Enterprise 1.1.0')
    
    args = parser.parse_args()
    
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Determine sharding state
    enable_sharding = not args.disable_sharding
    
    try:
        if args.mode == 'relay':
            # Load API keys if provided
            api_keys = None
            if args.api_keys:
                with open(args.api_keys, 'r') as f:
                    api_keys = json.load(f)
            
            # Parse peer relays
            peer_relays = []
            if args.peer_relays:
                peer_relays = [p.strip() for p in args.peer_relays.split(',')]
            
            # Start relay server
            relay = EnterpriseClusterRelay(
                args.relay_port,
                args.cluster,
                enable_tls=args.enable_tls,
                tls_cert=args.tls_cert,
                tls_key=args.tls_key,
                api_keys=api_keys,
                ha_enabled=args.ha_enabled,
                peer_relays=peer_relays,
                enable_sharding=enable_sharding,
                shard_size=args.shard_size,
                shuffle_block_size=args.shuffle_block_size
            )
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
            node = EnterpriseClusterNode(
                args.cluster,
                args.node,
                args.relay_host,
                args.relay_port,
                args.lan_port,
                args.enable_ble,
                args.api_key,
                args.enable_tls,
                enable_sharding=enable_sharding,
                shard_size=args.shard_size,
                shuffle_block_size=args.shuffle_block_size
            )
            asyncio.run(node.start())
            
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
