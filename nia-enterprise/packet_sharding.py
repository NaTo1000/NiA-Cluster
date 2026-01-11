#!/usr/bin/env python3
"""
Packet Sharding and Quantum Superposition Optimization Module

This module provides high-performance packet sharding and reforming capabilities
with an optimized double packet shuffle algorithm leveraging quantum superposition effects.

Features:
- Packet sharding: Break down large messages into smaller shards
- Packet reforming: Reassemble shards into original messages
- Double packet shuffle: Optimized transmission ordering
- Quantum superposition optimization: Probabilistic path selection
"""

import hashlib
import json
import logging
import math
import random
import time
import uuid
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Set
from collections import defaultdict

logger = logging.getLogger(__name__)


@dataclass
class PacketShard:
    """Represents a single shard of a packet."""
    shard_id: str
    packet_id: str
    sequence: int
    total_shards: int
    data: bytes
    checksum: str
    timestamp: float = field(default_factory=time.time)
    priority: int = 0
    superposition_state: Optional[float] = None  # Quantum probability amplitude

    def to_dict(self) -> dict:
        """Convert shard to dictionary for serialization."""
        return {
            'shard_id': self.shard_id,
            'packet_id': self.packet_id,
            'sequence': self.sequence,
            'total_shards': self.total_shards,
            'data': self.data.hex() if isinstance(self.data, bytes) else self.data,
            'checksum': self.checksum,
            'timestamp': self.timestamp,
            'priority': self.priority,
            'superposition_state': self.superposition_state
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'PacketShard':
        """Create shard from dictionary."""
        shard_data = data.get('data', '')
        if isinstance(shard_data, str):
            shard_data = bytes.fromhex(shard_data)
        return cls(
            shard_id=data['shard_id'],
            packet_id=data['packet_id'],
            sequence=data['sequence'],
            total_shards=data['total_shards'],
            data=shard_data,
            checksum=data['checksum'],
            timestamp=data.get('timestamp', time.time()),
            priority=data.get('priority', 0),
            superposition_state=data.get('superposition_state')
        )

    def verify_checksum(self) -> bool:
        """Verify the shard's checksum."""
        computed = hashlib.sha256(self.data).hexdigest()[:16]
        return computed == self.checksum


class QuantumSuperpositionOptimizer:
    """
    Quantum-inspired optimization for packet routing and scheduling.
    
    Uses probabilistic superposition states to optimize packet routing decisions
    by maintaining probability amplitudes for different routing paths and
    collapsing to optimal solutions based on measured performance.
    """
    
    # Phase scaling factor for converting performance metrics to phase shifts.
    # Using π ensures full range of constructive/destructive interference.
    PERFORMANCE_PHASE_SCALE = math.pi

    def __init__(self, num_paths: int = 4, coherence_factor: float = 0.9):
        """
        Initialize the quantum superposition optimizer.
        
        Args:
            num_paths: Number of potential routing paths to consider
            coherence_factor: Quantum coherence decay factor (0-1)
        """
        self.num_paths = num_paths
        self.coherence_factor = coherence_factor
        self.path_amplitudes: Dict[str, List[float]] = {}
        self.measurement_history: Dict[str, List[Tuple[int, float]]] = defaultdict(list)
        self._phase_offsets: Dict[str, List[float]] = {}
        # Pre-calculate uniform amplitude for efficiency
        self._uniform_amplitude = 1.0 / math.sqrt(self.num_paths)

    def initialize_superposition(self, packet_id: str) -> List[float]:
        """
        Initialize a packet in superposition across all paths.
        
        Creates equal probability amplitudes for all paths,
        representing the packet existing in all paths simultaneously.
        """
        # Initialize with equal probability amplitudes (normalized)
        amplitudes = [self._uniform_amplitude] * self.num_paths
        
        # Add random phase offsets for interference patterns
        phases = [random.uniform(0, 2 * math.pi) for _ in range(self.num_paths)]
        
        self.path_amplitudes[packet_id] = amplitudes
        self._phase_offsets[packet_id] = phases
        
        return amplitudes

    def apply_phase_shift(self, packet_id: str, path_index: int, 
                          performance_metric: float) -> None:
        """
        Apply a phase shift based on measured performance.
        
        Higher performance metrics increase the probability amplitude
        for the corresponding path through constructive interference.
        """
        if packet_id not in self.path_amplitudes:
            self.initialize_superposition(packet_id)
        
        # Scale performance to phase shift using defined constant
        phase_shift = performance_metric * self.PERFORMANCE_PHASE_SCALE
        self._phase_offsets[packet_id][path_index] += phase_shift
        
        # Update amplitude through interference
        current_amp = self.path_amplitudes[packet_id][path_index]
        phase = self._phase_offsets[packet_id][path_index]
        
        # Constructive/destructive interference based on phase
        interference_factor = 0.5 * (1 + math.cos(phase))
        new_amp = current_amp * (0.5 + 0.5 * interference_factor)
        
        self.path_amplitudes[packet_id][path_index] = new_amp
        
        # Normalize amplitudes to maintain probability conservation
        self._normalize_amplitudes(packet_id)

    def _normalize_amplitudes(self, packet_id: str) -> None:
        """Normalize amplitudes to ensure probabilities sum to 1."""
        amplitudes = self.path_amplitudes[packet_id]
        total = sum(a * a for a in amplitudes)  # Sum of squared amplitudes
        if total > 0:
            norm_factor = 1.0 / math.sqrt(total)
            self.path_amplitudes[packet_id] = [a * norm_factor for a in amplitudes]
        else:
            # Handle zero amplitude case - reset to uniform distribution
            self.path_amplitudes[packet_id] = [self._uniform_amplitude] * self.num_paths

    def collapse_to_path(self, packet_id: str) -> int:
        """
        Collapse the superposition to select a single path.
        
        Uses the probability distribution derived from amplitude squares
        to randomly select a path, simulating quantum measurement.
        
        Returns:
            Selected path index
        """
        if packet_id not in self.path_amplitudes:
            self.initialize_superposition(packet_id)
        
        amplitudes = self.path_amplitudes[packet_id]
        
        # Calculate probabilities from amplitude squares
        probabilities = [a * a for a in amplitudes]
        
        # Normalize probabilities
        total = sum(probabilities)
        if total > 0:
            probabilities = [p / total for p in probabilities]
        else:
            probabilities = [1.0 / self.num_paths] * self.num_paths
        
        # Random selection based on probability distribution
        r = random.random()
        cumulative = 0.0
        selected_path = 0
        
        for i, prob in enumerate(probabilities):
            cumulative += prob
            if r <= cumulative:
                selected_path = i
                break
        
        logger.debug(f"Packet {packet_id[:8]} collapsed to path {selected_path} "
                    f"(probabilities: {[f'{p:.3f}' for p in probabilities]})")
        
        return selected_path

    def record_measurement(self, packet_id: str, path_index: int, 
                          latency_ms: float) -> None:
        """
        Record a measurement of path performance.
        
        Updates the quantum state based on observed latency,
        improving future routing decisions through learning.
        """
        self.measurement_history[packet_id].append((path_index, latency_ms))
        
        # Convert latency to performance metric (lower is better)
        # Using inverse exponential for smooth performance scaling
        performance = math.exp(-latency_ms / 100.0)
        
        self.apply_phase_shift(packet_id, path_index, performance)

    def apply_coherence_decay(self) -> None:
        """
        Apply quantum decoherence to all superposition states.
        
        Gradually reduces quantum effects over time, causing
        the system to settle toward classical behavior.
        """
        for packet_id in self.path_amplitudes:
            amplitudes = self.path_amplitudes[packet_id]
            
            # Apply decay toward uniform distribution
            uniform = 1.0 / math.sqrt(self.num_paths)
            decayed = [
                self.coherence_factor * a + (1 - self.coherence_factor) * uniform
                for a in amplitudes
            ]
            
            self.path_amplitudes[packet_id] = decayed
            self._normalize_amplitudes(packet_id)

    def get_superposition_state(self, packet_id: str) -> Optional[List[float]]:
        """Get the current superposition state for a packet."""
        return self.path_amplitudes.get(packet_id)

    def clear_packet_state(self, packet_id: str) -> None:
        """Clear the quantum state for a completed packet."""
        self.path_amplitudes.pop(packet_id, None)
        self._phase_offsets.pop(packet_id, None)
        self.measurement_history.pop(packet_id, None)


class DoublePacketShuffle:
    """
    Optimized double packet shuffle algorithm for transmission.
    
    This algorithm optimizes packet transmission order by performing
    two-phase shuffling:
    1. First shuffle: Interleave packets for better error recovery
    2. Second shuffle: Apply quantum-optimized reordering
    """

    def __init__(self, block_size: int = 8):
        """
        Initialize the double packet shuffle.
        
        Args:
            block_size: Number of shards to process as a block
        """
        self.block_size = block_size
        self.quantum_optimizer = QuantumSuperpositionOptimizer(num_paths=block_size)

    def first_shuffle(self, shards: List[PacketShard]) -> List[PacketShard]:
        """
        First phase: Interleave shards for burst error protection.
        
        Uses a matrix transposition approach to spread sequential
        shards across the transmission, making the data more
        resilient to burst errors.
        """
        if len(shards) <= 1:
            return shards
        
        n = len(shards)
        rows = math.ceil(n / self.block_size)
        cols = self.block_size
        
        # Create a 2D matrix and fill with shards
        matrix: List[List[Optional[PacketShard]]] = [
            [None for _ in range(cols)] for _ in range(rows)
        ]
        
        for i, shard in enumerate(shards):
            row = i // cols
            col = i % cols
            matrix[row][col] = shard
        
        # Read out in column-major order (transpose)
        shuffled: List[PacketShard] = []
        for col in range(cols):
            for row in range(rows):
                if matrix[row][col] is not None:
                    shuffled.append(matrix[row][col])
        
        logger.debug(f"First shuffle: {n} shards interleaved with block_size={self.block_size}")
        return shuffled

    def second_shuffle(self, shards: List[PacketShard]) -> List[PacketShard]:
        """
        Second phase: Apply quantum-optimized reordering.
        
        Uses quantum superposition states to determine optimal
        transmission order within blocks, maximizing parallel
        processing potential.
        """
        if len(shards) <= 1:
            return shards
        
        result: List[PacketShard] = []
        
        # Process shards in blocks
        for block_start in range(0, len(shards), self.block_size):
            block_end = min(block_start + self.block_size, len(shards))
            block = shards[block_start:block_end]
            
            # Initialize superposition for this block (block-level state)
            block_id = f"block_{block_start}"
            self.quantum_optimizer.initialize_superposition(block_id)
            
            # Assign quantum states to each shard using the block's collective state
            ordered_block: List[Tuple[float, PacketShard]] = []
            for i, shard in enumerate(block):
                # Collapse superposition using block-level state for consistent optimization
                path = self.quantum_optimizer.collapse_to_path(block_id)
                shard.superposition_state = (path + i) / max(self.block_size, len(block))
                ordered_block.append((shard.superposition_state, shard))
            
            # Sort by quantum state for optimal ordering
            ordered_block.sort(key=lambda x: x[0])
            result.extend([shard for _, shard in ordered_block])
            
            self.quantum_optimizer.clear_packet_state(block_id)
        
        logger.debug(f"Second shuffle: {len(shards)} shards quantum-optimized")
        return result

    def shuffle(self, shards: List[PacketShard]) -> List[PacketShard]:
        """
        Apply the complete double shuffle algorithm.
        
        Returns shards in optimized transmission order.
        """
        # Apply both shuffle phases
        phase1 = self.first_shuffle(shards)
        phase2 = self.second_shuffle(phase1)
        
        logger.info(f"Double shuffle complete: {len(shards)} shards processed")
        return phase2

    def unshuffle_first(self, shards: List[PacketShard], 
                        total_expected: int) -> List[PacketShard]:
        """
        Reverse the first shuffle phase.
        
        Reconstructs the original shard ordering from interleaved order.
        """
        if len(shards) <= 1:
            return shards
        
        n = total_expected
        rows = math.ceil(n / self.block_size)
        cols = self.block_size
        
        # Create matrix and fill in column-major order
        matrix: List[List[Optional[PacketShard]]] = [
            [None for _ in range(cols)] for _ in range(rows)
        ]
        
        shard_idx = 0
        for col in range(cols):
            for row in range(rows):
                if shard_idx < len(shards) and row * cols + col < n:
                    matrix[row][col] = shards[shard_idx]
                    shard_idx += 1
        
        # Read out in row-major order
        unshuffled: List[PacketShard] = []
        for row in range(rows):
            for col in range(cols):
                if matrix[row][col] is not None:
                    unshuffled.append(matrix[row][col])
        
        return unshuffled

    def unshuffle(self, shards: List[PacketShard], 
                  total_expected: int) -> List[PacketShard]:
        """
        Reverse the complete double shuffle.
        
        Since second shuffle uses quantum optimization which is
        tracked by sequence numbers, we only need to reverse the
        first interleaving shuffle and sort by sequence.
        """
        # Sort by sequence number to reverse second shuffle
        sorted_shards = sorted(shards, key=lambda s: s.sequence)
        
        # Reverse first shuffle
        return self.unshuffle_first(sorted_shards, total_expected)


class PacketShardManager:
    """
    Manages packet sharding and reforming with quantum optimization.
    
    Provides high-level API for:
    - Breaking packets into optimally-sized shards
    - Applying double shuffle for transmission
    - Reassembling shards into original packets
    - Quantum-optimized routing decisions
    """

    DEFAULT_SHARD_SIZE = 1024  # Default shard size in bytes

    def __init__(self, shard_size: int = DEFAULT_SHARD_SIZE, 
                 shuffle_block_size: int = 8):
        """
        Initialize the packet shard manager.
        
        Args:
            shard_size: Maximum size of each shard in bytes
            shuffle_block_size: Block size for double shuffle algorithm
        """
        self.shard_size = shard_size
        self.shuffler = DoublePacketShuffle(block_size=shuffle_block_size)
        self.quantum_optimizer = QuantumSuperpositionOptimizer()
        self.pending_packets: Dict[str, Dict[int, PacketShard]] = {}
        self.packet_metadata: Dict[str, dict] = {}

    def shard_packet(self, data: bytes, packet_id: Optional[str] = None,
                     priority: int = 0) -> List[PacketShard]:
        """
        Break a packet into shards.
        
        Args:
            data: Raw packet data to shard
            packet_id: Optional packet identifier (generated if not provided)
            priority: Priority level for the packet (higher = more important)
            
        Returns:
            List of PacketShard objects ready for transmission
        """
        if packet_id is None:
            packet_id = str(uuid.uuid4())
        
        shards: List[PacketShard] = []
        total_shards = math.ceil(len(data) / self.shard_size)
        
        if total_shards == 0:
            total_shards = 1
        
        for i in range(total_shards):
            start = i * self.shard_size
            end = min((i + 1) * self.shard_size, len(data))
            shard_data = data[start:end]
            
            # Compute checksum for integrity verification
            checksum = hashlib.sha256(shard_data).hexdigest()[:16]
            
            shard = PacketShard(
                shard_id=str(uuid.uuid4()),
                packet_id=packet_id,
                sequence=i,
                total_shards=total_shards,
                data=shard_data,
                checksum=checksum,
                priority=priority
            )
            shards.append(shard)
        
        # Initialize quantum superposition for routing optimization
        self.quantum_optimizer.initialize_superposition(packet_id)
        
        logger.info(f"Sharded packet {packet_id[:8]}: {len(data)} bytes -> "
                   f"{total_shards} shards of max {self.shard_size} bytes")
        
        return shards

    def prepare_for_transmission(self, shards: List[PacketShard]) -> List[PacketShard]:
        """
        Prepare shards for transmission by applying double shuffle.
        
        Returns shards in optimized transmission order.
        """
        return self.shuffler.shuffle(shards)

    def receive_shard(self, shard: PacketShard) -> Optional[bytes]:
        """
        Receive a shard and attempt to reform the packet.
        
        Args:
            shard: The received PacketShard
            
        Returns:
            Complete packet data if all shards received, None otherwise
        """
        # Verify checksum
        if not shard.verify_checksum():
            logger.warning(f"Shard {shard.shard_id[:8]} failed checksum verification")
            return None
        
        packet_id = shard.packet_id
        
        # Initialize storage for this packet if needed
        if packet_id not in self.pending_packets:
            self.pending_packets[packet_id] = {}
            # Get optimal route for this packet using quantum optimization
            selected_route = self.quantum_optimizer.collapse_to_path(packet_id)
            self.packet_metadata[packet_id] = {
                'total_shards': shard.total_shards,
                'first_received': time.time(),
                'priority': shard.priority,
                'route': selected_route  # Track route for performance feedback
            }
        
        # Store the shard
        self.pending_packets[packet_id][shard.sequence] = shard
        
        received = len(self.pending_packets[packet_id])
        total = self.packet_metadata[packet_id]['total_shards']
        
        logger.debug(f"Received shard {shard.sequence + 1}/{total} for packet {packet_id[:8]}")
        
        # Check if we have all shards
        if received >= total:
            return self.reform_packet(packet_id)
        
        return None

    def reform_packet(self, packet_id: str) -> Optional[bytes]:
        """
        Reassemble a complete packet from its shards.
        
        Args:
            packet_id: The packet identifier
            
        Returns:
            Complete packet data, or None if incomplete
        """
        if packet_id not in self.pending_packets:
            logger.warning(f"No shards found for packet {packet_id[:8]}")
            return None
        
        shards_dict = self.pending_packets[packet_id]
        metadata = self.packet_metadata.get(packet_id, {})
        total_shards = metadata.get('total_shards', 0)
        
        # Check we have all shards
        if len(shards_dict) < total_shards:
            logger.debug(f"Packet {packet_id[:8]} incomplete: {len(shards_dict)}/{total_shards}")
            return None
        
        # Sort shards by sequence and concatenate
        # Note: The shuffle only affects transmission order, not the data.
        # Each shard's data corresponds to its sequence number, so we just
        # need to sort by sequence to reconstruct the original packet.
        sorted_shards = [shards_dict[i] for i in sorted(shards_dict.keys())]
        
        # Concatenate data in sequence order
        packet_data = b''.join(shard.data for shard in sorted_shards)
        
        # Calculate assembly time
        assembly_time = time.time() - metadata.get('first_received', time.time())
        
        logger.info(f"Reformed packet {packet_id[:8]}: {len(packet_data)} bytes "
                   f"from {total_shards} shards in {assembly_time:.3f}s")
        
        # Record measurement for quantum optimization using the actual route
        route = metadata.get('route', 0)
        self.quantum_optimizer.record_measurement(packet_id, route, assembly_time * 1000)
        
        # Cleanup
        self._cleanup_packet(packet_id)
        
        return packet_data

    def get_optimal_route(self, packet_id: str) -> int:
        """
        Get the quantum-optimized route for a packet.
        
        Returns the path index that the quantum optimizer
        has collapsed to for this packet.
        """
        return self.quantum_optimizer.collapse_to_path(packet_id)

    def record_transmission_result(self, packet_id: str, path_index: int,
                                   latency_ms: float) -> None:
        """
        Record the result of a transmission for optimization.
        
        Updates the quantum optimizer with measured performance.
        """
        self.quantum_optimizer.record_measurement(packet_id, path_index, latency_ms)

    def _cleanup_packet(self, packet_id: str) -> None:
        """Clean up storage for a completed packet."""
        self.pending_packets.pop(packet_id, None)
        self.packet_metadata.pop(packet_id, None)
        self.quantum_optimizer.clear_packet_state(packet_id)

    def get_pending_packets_count(self) -> int:
        """Get the number of packets awaiting completion."""
        return len(self.pending_packets)

    def get_shard_stats(self, packet_id: str) -> Optional[dict]:
        """Get statistics for a pending packet."""
        if packet_id not in self.pending_packets:
            return None
        
        metadata = self.packet_metadata.get(packet_id, {})
        shards_received = len(self.pending_packets[packet_id])
        total_shards = metadata.get('total_shards', 0)
        
        return {
            'packet_id': packet_id,
            'shards_received': shards_received,
            'total_shards': total_shards,
            'completion_percent': (shards_received / total_shards * 100) if total_shards > 0 else 0,
            'priority': metadata.get('priority', 0),
            'age_seconds': time.time() - metadata.get('first_received', time.time())
        }

    def cleanup_stale_packets(self, max_age_seconds: float = 60.0) -> int:
        """
        Clean up packets that have been pending too long.
        
        Args:
            max_age_seconds: Maximum age before a packet is considered stale
            
        Returns:
            Number of packets cleaned up
        """
        current_time = time.time()
        stale_packets = []
        
        for packet_id, metadata in self.packet_metadata.items():
            age = current_time - metadata.get('first_received', current_time)
            if age > max_age_seconds:
                stale_packets.append(packet_id)
        
        for packet_id in stale_packets:
            logger.warning(f"Cleaning up stale packet {packet_id[:8]}")
            self._cleanup_packet(packet_id)
        
        return len(stale_packets)


def create_sharding_system(shard_size: int = 1024, 
                           shuffle_block_size: int = 8) -> PacketShardManager:
    """
    Factory function to create a configured packet sharding system.
    
    Args:
        shard_size: Maximum size of each shard in bytes
        shuffle_block_size: Block size for double shuffle algorithm
        
    Returns:
        Configured PacketShardManager instance
    """
    return PacketShardManager(
        shard_size=shard_size,
        shuffle_block_size=shuffle_block_size
    )
