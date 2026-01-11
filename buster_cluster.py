#!/usr/bin/env python3
"""
Buster Cluster - Autonomous Distribution System
Self-managing AI-driven cluster that distributes across cloud networks
based on security assessments and network performance.

Features:
- Autonomous decision-making for workload distribution
- Security assessment of cloud networks
- Network speed monitoring and optimization
- Self-revision every 15 seconds with on-the-fly optimizations
- Fully autonomous AI operations
"""
import argparse
import asyncio
import json
import logging
import secrets
import sys
import time
import hashlib
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple
from enum import Enum, auto

# Cryptographically secure random for security-sensitive operations
secure_random = secrets.SystemRandom()

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


class SecurityLevel(Enum):
    """Security assessment levels for cloud networks"""
    CRITICAL = 1
    LOW = 2
    MEDIUM = 3
    HIGH = 4
    MAXIMUM = 5


class NetworkStatus(Enum):
    """Network status indicators"""
    OFFLINE = auto()
    DEGRADED = auto()
    NORMAL = auto()
    OPTIMAL = auto()


@dataclass
class CloudNetwork:
    """Represents a cloud network endpoint"""
    network_id: str
    name: str
    region: str
    provider: str  # aws, gcp, azure, etc.
    endpoint: str
    port: int = 4040
    security_level: SecurityLevel = SecurityLevel.MEDIUM
    latency_ms: float = 100.0
    bandwidth_mbps: float = 100.0
    status: NetworkStatus = NetworkStatus.NORMAL
    last_assessment: Optional[str] = None
    score: float = 0.0

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            'network_id': self.network_id,
            'name': self.name,
            'region': self.region,
            'provider': self.provider,
            'endpoint': self.endpoint,
            'port': self.port,
            'security_level': self.security_level.name,
            'latency_ms': self.latency_ms,
            'bandwidth_mbps': self.bandwidth_mbps,
            'status': self.status.name,
            'last_assessment': self.last_assessment,
            'score': self.score
        }


@dataclass
class OptimizationResult:
    """Result of an optimization cycle"""
    timestamp: str
    cycle_id: int
    decisions_made: int
    migrations_triggered: int
    security_updates: int
    performance_improvements: float
    notes: List[str] = field(default_factory=list)


class SecurityAssessor:
    """Assesses security of cloud networks"""

    def __init__(self):
        self.assessment_history: List[dict] = []

    def assess_network(self, network: CloudNetwork) -> Tuple[SecurityLevel, List[str]]:
        """
        Assess security level of a cloud network.
        Returns security level and list of findings.
        """
        findings = []
        base_score = 3  # Start at MEDIUM

        # Assess based on provider (simulated security posture)
        provider_scores = {
            'gcp': 1,
            'aws': 1,
            'azure': 1,
            'private': 0,
            'hybrid': 0,
            'unknown': -1
        }
        provider_adjustment = provider_scores.get(network.provider.lower(), -1)
        base_score += provider_adjustment

        # Assess based on endpoint security (TLS)
        if network.endpoint.startswith('wss://'):
            base_score += 1
            findings.append("TLS encryption enabled")
        else:
            base_score -= 1
            findings.append("WARNING: No TLS encryption detected")

        # Assess based on region (some regions have stricter compliance)
        secure_regions = ['us-central1', 'us-east1', 'europe-west1', 'eu-west-1']
        if any(region in network.region.lower() for region in secure_regions):
            base_score += 0.5
            findings.append(f"Region {network.region} has good compliance posture")

        # Clamp score between 1-5
        final_score = max(1, min(5, round(base_score)))

        assessment = {
            'network_id': network.network_id,
            'timestamp': datetime.now().isoformat(),
            'security_level': SecurityLevel(final_score).name,
            'findings': findings
        }
        self.assessment_history.append(assessment)

        logger.info(f"Security assessment for {network.name}: {SecurityLevel(final_score).name}")
        return SecurityLevel(final_score), findings

    def get_assessment_report(self) -> List[dict]:
        """Get full assessment history"""
        return self.assessment_history


class NetworkSpeedAnalyzer:
    """Analyzes network speed and performance"""

    # Constants for bandwidth scoring
    BANDWIDTH_SCALE_FACTOR = 10
    MAX_BANDWIDTH_FOR_SCORE = 1000  # 1000 Mbps = score of 100
    MAX_LATENCY_FOR_SCORE = 100  # 100ms latency = score of 0

    def __init__(self):
        self.measurements: Dict[str, List[dict]] = {}

    async def measure_latency(self, network: CloudNetwork) -> float:
        """
        Measure network latency to a cloud network.
        Returns latency in milliseconds.
        """
        # Simulated latency measurement (in production, would do actual ping/probe)
        # Base latency varies by provider and region
        base_latency = {
            'gcp': 20,
            'aws': 25,
            'azure': 22,
            'private': 5,
            'hybrid': 30
        }.get(network.provider.lower(), 50)

        # Add some variance using secure random
        variance = secure_random.uniform(-10, 20)
        measured_latency = max(1, base_latency + variance)

        # Store measurement
        if network.network_id not in self.measurements:
            self.measurements[network.network_id] = []
        self.measurements[network.network_id].append({
            'timestamp': datetime.now().isoformat(),
            'latency_ms': measured_latency,
            'type': 'latency'
        })

        logger.debug(f"Latency to {network.name}: {measured_latency:.2f}ms")
        return measured_latency

    async def measure_bandwidth(self, network: CloudNetwork) -> float:
        """
        Measure available bandwidth to a cloud network.
        Returns bandwidth in Mbps.
        """
        # Simulated bandwidth measurement
        base_bandwidth = {
            'gcp': 1000,
            'aws': 900,
            'azure': 950,
            'private': 10000,
            'hybrid': 500
        }.get(network.provider.lower(), 100)

        # Add variance using secure random
        variance = secure_random.uniform(-100, 200)
        measured_bandwidth = max(10, base_bandwidth + variance)

        # Store measurement
        if network.network_id not in self.measurements:
            self.measurements[network.network_id] = []
        self.measurements[network.network_id].append({
            'timestamp': datetime.now().isoformat(),
            'bandwidth_mbps': measured_bandwidth,
            'type': 'bandwidth'
        })

        logger.debug(f"Bandwidth to {network.name}: {measured_bandwidth:.2f}Mbps")
        return measured_bandwidth

    async def assess_network_performance(self, network: CloudNetwork) -> dict:
        """
        Full performance assessment of a network.
        Returns performance metrics.
        """
        latency = await self.measure_latency(network)
        bandwidth = await self.measure_bandwidth(network)

        # Calculate performance score (0-100)
        # Lower latency is better, higher bandwidth is better
        latency_score = max(0, self.MAX_LATENCY_FOR_SCORE - latency)
        bandwidth_score = min(100, bandwidth / self.BANDWIDTH_SCALE_FACTOR)

        performance_score = (latency_score * 0.4 + bandwidth_score * 0.6)

        return {
            'network_id': network.network_id,
            'latency_ms': latency,
            'bandwidth_mbps': bandwidth,
            'latency_score': latency_score,
            'bandwidth_score': bandwidth_score,
            'overall_score': performance_score,
            'timestamp': datetime.now().isoformat()
        }


class AutonomousDecisionEngine:
    """
    AI-driven decision engine for autonomous cluster operations.
    Makes decisions about workload distribution based on security and performance.
    """

    def __init__(self, security_weight: float = 0.5, performance_weight: float = 0.5):
        self.security_weight = security_weight
        self.performance_weight = performance_weight
        self.decision_history: List[dict] = []
        self.optimization_rules: List[dict] = []

    def calculate_network_score(
        self,
        network: CloudNetwork,
        security_level: SecurityLevel,
        performance: dict
    ) -> float:
        """
        Calculate overall score for a network based on security and performance.
        Returns score between 0 and 100.
        """
        # Security score (1-5 mapped to 20-100)
        security_score = security_level.value * 20

        # Performance score from assessment
        performance_score = performance.get('overall_score', 50)

        # Weighted combination
        total_score = (
            self.security_weight * security_score +
            self.performance_weight * performance_score
        )

        return total_score

    def decide_optimal_network(
        self,
        networks: List[CloudNetwork],
        security_assessments: Dict[str, SecurityLevel],
        performance_assessments: Dict[str, dict]
    ) -> Optional[CloudNetwork]:
        """
        Decide the optimal network for workload distribution.
        Returns the best network or None if no suitable network found.
        """
        if not networks:
            return None

        best_network = None
        best_score = -1

        for network in networks:
            if network.status == NetworkStatus.OFFLINE:
                continue

            security_level = security_assessments.get(
                network.network_id,
                SecurityLevel.MEDIUM
            )
            performance = performance_assessments.get(network.network_id, {})

            score = self.calculate_network_score(network, security_level, performance)
            network.score = score

            logger.debug(f"Network {network.name} score: {score:.2f}")

            if score > best_score:
                best_score = score
                best_network = network

        if best_network:
            decision = {
                'timestamp': datetime.now().isoformat(),
                'decision': 'select_network',
                'selected': best_network.network_id,
                'score': best_score,
                'reason': f"Highest combined security/performance score: {best_score:.2f}"
            }
            self.decision_history.append(decision)
            logger.info(f"Decision: Selected {best_network.name} (score: {best_score:.2f})")

        return best_network

    def generate_optimization_rules(self, cycle_data: dict) -> List[dict]:
        """
        Self-generate optimization rules based on historical data.
        This is the "self-coding" aspect - dynamically generating rules.
        """
        rules = []

        # Analyze decision history for patterns
        if len(self.decision_history) >= 3:
            # Check if we're consistently selecting the same network
            recent_selections = [
                d.get('selected')
                for d in self.decision_history[-3:]
            ]
            if len(set(recent_selections)) == 1:
                rules.append({
                    'type': 'sticky_network',
                    'network_id': recent_selections[0],
                    'reason': 'Consistent selection indicates stable optimal network',
                    'action': 'increase_confidence'
                })

        # Generate performance-based rules
        if cycle_data.get('avg_latency', 100) > 80:
            rules.append({
                'type': 'latency_optimization',
                'threshold': 80,
                'action': 'prefer_lower_latency_networks',
                'priority': 'high'
            })

        # Generate security-based rules
        if cycle_data.get('security_incidents', 0) > 0:
            rules.append({
                'type': 'security_enforcement',
                'action': 'increase_security_weight',
                'new_weight': min(0.8, self.security_weight + 0.1),
                'priority': 'critical'
            })

        self.optimization_rules = rules
        return rules


class BusterCluster:
    """
    Main Buster Cluster class - Autonomous distribution system.
    Manages workload distribution across cloud networks with AI-driven decisions.
    """

    OPTIMIZATION_INTERVAL = 15  # seconds

    def __init__(
        self,
        cluster_name: str,
        node_id: str,
        enable_autonomous: bool = True,
        security_weight: float = 0.5,
        performance_weight: float = 0.5
    ):
        self.cluster_name = cluster_name
        self.node_id = node_id
        self.enable_autonomous = enable_autonomous

        # Cloud networks registry
        self.networks: Dict[str, CloudNetwork] = {}

        # Assessment components
        self.security_assessor = SecurityAssessor()
        self.speed_analyzer = NetworkSpeedAnalyzer()

        # Decision engine
        self.decision_engine = AutonomousDecisionEngine(
            security_weight=security_weight,
            performance_weight=performance_weight
        )

        # State
        self.current_network: Optional[CloudNetwork] = None
        self.optimization_cycle = 0
        self.start_time = time.time()
        self.running = False
        self.connected_relays: Dict[str, websockets.WebSocketClientProtocol] = {}

        # Optimization history
        self.optimization_history: List[OptimizationResult] = []

        logger.info(f"Buster Cluster initialized: {cluster_name}/{node_id}")
        logger.info(f"Autonomous mode: {'enabled' if enable_autonomous else 'disabled'}")
        logger.info(f"Optimization interval: {self.OPTIMIZATION_INTERVAL}s")

    def register_network(self, network: CloudNetwork) -> None:
        """Register a cloud network with the cluster"""
        self.networks[network.network_id] = network
        logger.info(f"Registered network: {network.name} ({network.provider})")

    def unregister_network(self, network_id: str) -> None:
        """Unregister a cloud network"""
        if network_id in self.networks:
            del self.networks[network_id]
            logger.info(f"Unregistered network: {network_id}")

    async def assess_all_networks(self) -> Tuple[Dict[str, SecurityLevel], Dict[str, dict]]:
        """
        Perform full assessment of all registered networks.
        Returns security and performance assessments.
        """
        security_assessments = {}
        performance_assessments = {}

        for network_id, network in self.networks.items():
            # Security assessment
            security_level, _ = self.security_assessor.assess_network(network)
            security_assessments[network_id] = security_level
            network.security_level = security_level

            # Performance assessment
            performance = await self.speed_analyzer.assess_network_performance(network)
            performance_assessments[network_id] = performance
            network.latency_ms = performance['latency_ms']
            network.bandwidth_mbps = performance['bandwidth_mbps']
            network.last_assessment = datetime.now().isoformat()

        return security_assessments, performance_assessments

    async def optimization_cycle_task(self) -> OptimizationResult:
        """
        Perform one optimization cycle.
        This runs every 15 seconds and makes autonomous decisions.
        """
        self.optimization_cycle += 1
        cycle_start = time.time()

        logger.info(f"=== Optimization Cycle {self.optimization_cycle} ===")

        # Track changes made
        decisions_made = 0
        migrations_triggered = 0
        security_updates = 0
        notes = []

        # 1. Assess all networks
        security_assessments, performance_assessments = await self.assess_all_networks()
        notes.append(f"Assessed {len(self.networks)} networks")

        # 2. Calculate average metrics for rule generation
        avg_latency = 0
        if performance_assessments:
            avg_latency = sum(
                p.get('latency_ms', 0) for p in performance_assessments.values()
            ) / len(performance_assessments)

        cycle_data = {
            'avg_latency': avg_latency,
            'security_incidents': 0,  # Would be populated from real monitoring
            'network_count': len(self.networks)
        }

        # 3. Self-generate optimization rules (self-coding)
        new_rules = self.decision_engine.generate_optimization_rules(cycle_data)
        if new_rules:
            notes.append(f"Generated {len(new_rules)} optimization rules")
            logger.info(f"Self-generated {len(new_rules)} new optimization rules")
            for rule in new_rules:
                logger.debug(f"  Rule: {rule['type']} - {rule.get('action', 'N/A')}")

        # 4. Make autonomous decision about optimal network
        if self.enable_autonomous:
            networks_list = list(self.networks.values())
            optimal_network = self.decision_engine.decide_optimal_network(
                networks_list,
                security_assessments,
                performance_assessments
            )

            if optimal_network:
                decisions_made += 1

                # Check if migration needed
                if self.current_network != optimal_network:
                    if self.current_network:
                        migrations_triggered += 1
                        notes.append(
                            f"Migrating from {self.current_network.name} to {optimal_network.name}"
                        )
                        logger.info(
                            f"Migration triggered: {self.current_network.name} -> {optimal_network.name}"
                        )
                    else:
                        notes.append(f"Selected initial network: {optimal_network.name}")

                    self.current_network = optimal_network

        # 5. Apply security updates if needed
        for network_id, level in security_assessments.items():
            if level.value < SecurityLevel.MEDIUM.value:
                security_updates += 1
                notes.append(f"Network {network_id} flagged for security review")
                logger.warning(f"Low security detected on network {network_id}")

        # Calculate performance improvement (simulated)
        cycle_duration = time.time() - cycle_start
        performance_improvement = max(0, 100 - (cycle_duration * 1000))  # Inverse of cycle time

        result = OptimizationResult(
            timestamp=datetime.now().isoformat(),
            cycle_id=self.optimization_cycle,
            decisions_made=decisions_made,
            migrations_triggered=migrations_triggered,
            security_updates=security_updates,
            performance_improvements=performance_improvement,
            notes=notes
        )

        self.optimization_history.append(result)

        logger.info(f"Cycle {self.optimization_cycle} complete: "
                   f"{decisions_made} decisions, "
                   f"{migrations_triggered} migrations, "
                   f"{security_updates} security updates")

        return result

    async def run_autonomous_loop(self) -> None:
        """
        Main autonomous operation loop.
        Runs optimization cycles every 15 seconds.
        """
        logger.info("Starting autonomous operation loop")
        self.running = True

        consecutive_errors = 0
        max_consecutive_errors = 5

        while self.running:
            try:
                await self.optimization_cycle_task()
                await asyncio.sleep(self.OPTIMIZATION_INTERVAL)
                consecutive_errors = 0  # Reset on success
            except asyncio.CancelledError:
                logger.info("Autonomous loop cancelled")
                break
            except (ConnectionError, OSError) as e:
                consecutive_errors += 1
                logger.error(f"Network error in optimization cycle ({consecutive_errors}/{max_consecutive_errors}): {e}")
                if consecutive_errors >= max_consecutive_errors:
                    logger.critical("Too many consecutive network errors, stopping autonomous loop")
                    self.running = False
                    raise
                await asyncio.sleep(self.OPTIMIZATION_INTERVAL)
            except ValueError as e:
                logger.error(f"Configuration error in optimization cycle: {e}")
                await asyncio.sleep(self.OPTIMIZATION_INTERVAL)
            except RuntimeError as e:
                logger.error(f"Runtime error in optimization cycle: {e}")
                await asyncio.sleep(self.OPTIMIZATION_INTERVAL)

    async def connect_to_relay(self, network: CloudNetwork) -> bool:
        """Connect to a network's relay server"""
        try:
            # Respect the protocol specified in the endpoint
            endpoint = network.endpoint
            if endpoint.startswith('wss://') or endpoint.startswith('ws://'):
                # Endpoint already includes protocol
                uri = endpoint
            else:
                # Default to ws:// if no protocol specified
                uri = f"ws://{endpoint}:{network.port}"
            
            logger.info(f"Connecting to relay at {uri}")

            ws = await websockets.connect(uri)
            self.connected_relays[network.network_id] = ws

            # Register with relay
            await ws.send(json.dumps({
                'type': 'register',
                'node_name': f"buster-{self.node_id}",
                'cluster': self.cluster_name,
                'buster_enabled': True,
                'autonomous': self.enable_autonomous,
                'version': '1.0.0'
            }))

            logger.info(f"Connected to {network.name}")
            return True

        except websockets.exceptions.WebSocketException as e:
            logger.error(f"WebSocket error connecting to {network.name}: {e}")
            network.status = NetworkStatus.DEGRADED
            return False
        except ConnectionError as e:
            logger.error(f"Connection error to {network.name}: {e}")
            network.status = NetworkStatus.DEGRADED
            return False

    async def disconnect_from_relay(self, network_id: str) -> None:
        """Disconnect from a network's relay"""
        if network_id in self.connected_relays:
            try:
                await self.connected_relays[network_id].close()
            except Exception as e:
                logger.debug(f"Error closing connection: {e}")
            del self.connected_relays[network_id]
            logger.info(f"Disconnected from network {network_id}")

    def get_status(self) -> dict:
        """Get current cluster status"""
        return {
            'cluster_name': self.cluster_name,
            'node_id': self.node_id,
            'autonomous_enabled': self.enable_autonomous,
            'running': self.running,
            'uptime_seconds': int(time.time() - self.start_time),
            'optimization_cycles': self.optimization_cycle,
            'registered_networks': len(self.networks),
            'connected_networks': len(self.connected_relays),
            'current_network': self.current_network.name if self.current_network else None,
            'networks': [n.to_dict() for n in self.networks.values()]
        }

    def get_optimization_report(self) -> dict:
        """Get optimization history report"""
        return {
            'total_cycles': self.optimization_cycle,
            'total_decisions': sum(r.decisions_made for r in self.optimization_history),
            'total_migrations': sum(r.migrations_triggered for r in self.optimization_history),
            'total_security_updates': sum(r.security_updates for r in self.optimization_history),
            'current_rules': self.decision_engine.optimization_rules,
            'recent_history': [
                {
                    'cycle_id': r.cycle_id,
                    'timestamp': r.timestamp,
                    'decisions': r.decisions_made,
                    'migrations': r.migrations_triggered,
                    'notes': r.notes
                }
                for r in self.optimization_history[-10:]  # Last 10 cycles
            ]
        }

    async def start(self) -> None:
        """Start the Buster Cluster"""
        logger.info(f"Starting Buster Cluster: {self.cluster_name}")

        # Start autonomous loop
        await self.run_autonomous_loop()

    async def stop(self) -> None:
        """Stop the Buster Cluster"""
        logger.info("Stopping Buster Cluster")
        self.running = False

        # Disconnect from all relays
        for network_id in list(self.connected_relays.keys()):
            await self.disconnect_from_relay(network_id)

        logger.info("Buster Cluster stopped")


def create_sample_networks() -> List[CloudNetwork]:
    """Create sample cloud networks for testing"""
    return [
        CloudNetwork(
            network_id="gcp-us-central1",
            name="GCP US Central",
            region="us-central1",
            provider="gcp",
            endpoint="gcp-relay.example.com",
            port=4040
        ),
        CloudNetwork(
            network_id="aws-us-east-1",
            name="AWS US East",
            region="us-east-1",
            provider="aws",
            endpoint="aws-relay.example.com",
            port=4040
        ),
        CloudNetwork(
            network_id="azure-westus",
            name="Azure West US",
            region="westus",
            provider="azure",
            endpoint="azure-relay.example.com",
            port=4040
        ),
        CloudNetwork(
            network_id="private-dc1",
            name="Private Datacenter 1",
            region="private",
            provider="private",
            endpoint="wss://private-relay.local",
            port=4040
        )
    ]


def main():
    """Main entry point for Buster Cluster"""
    parser = argparse.ArgumentParser(
        description='Buster Cluster - Autonomous Cloud Distribution System'
    )

    parser.add_argument('--cluster', required=True,
                       help='Cluster name')
    parser.add_argument('--node-id', required=True,
                       help='Node identifier')
    parser.add_argument('--autonomous', action='store_true', default=True,
                       help='Enable autonomous mode (default: true)')
    parser.add_argument('--no-autonomous', action='store_false', dest='autonomous',
                       help='Disable autonomous mode')
    parser.add_argument('--security-weight', type=float, default=0.5,
                       help='Weight for security in decision making (0.0-1.0)')
    parser.add_argument('--performance-weight', type=float, default=0.5,
                       help='Weight for performance in decision making (0.0-1.0)')
    parser.add_argument('--add-network', action='append', nargs=4,
                       metavar=('ID', 'REGION', 'PROVIDER', 'ENDPOINT'),
                       help='Add a cloud network (can be used multiple times)')
    parser.add_argument('--use-sample-networks', action='store_true',
                       help='Use sample networks for testing')
    parser.add_argument('--debug', action='store_true',
                       help='Enable debug logging')
    parser.add_argument('--status-only', action='store_true',
                       help='Show status and exit')

    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    # Create Buster Cluster instance
    cluster = BusterCluster(
        cluster_name=args.cluster,
        node_id=args.node_id,
        enable_autonomous=args.autonomous,
        security_weight=args.security_weight,
        performance_weight=args.performance_weight
    )

    # Register networks
    if args.use_sample_networks:
        for network in create_sample_networks():
            cluster.register_network(network)
    elif args.add_network:
        for net_args in args.add_network:
            network = CloudNetwork(
                network_id=net_args[0],
                name=net_args[0],
                region=net_args[1],
                provider=net_args[2],
                endpoint=net_args[3]
            )
            cluster.register_network(network)
    else:
        # Register default sample networks if none specified
        for network in create_sample_networks():
            cluster.register_network(network)

    if args.status_only:
        print(json.dumps(cluster.get_status(), indent=2))
        return

    # Start the cluster
    try:
        asyncio.run(cluster.start())
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        asyncio.run(cluster.stop())


if __name__ == '__main__':
    main()
