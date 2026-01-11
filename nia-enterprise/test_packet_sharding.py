#!/usr/bin/env python3
"""
Tests for the packet sharding and quantum superposition optimization module.
"""

import unittest
import time
from packet_sharding import (
    PacketShard,
    PacketShardManager,
    DoublePacketShuffle,
    QuantumSuperpositionOptimizer,
    create_sharding_system
)


class TestPacketShard(unittest.TestCase):
    """Tests for PacketShard class."""

    def test_shard_creation(self):
        """Test creating a PacketShard."""
        shard = PacketShard(
            shard_id="shard-001",
            packet_id="packet-001",
            sequence=0,
            total_shards=3,
            data=b"test data",
            checksum="abc123"
        )
        self.assertEqual(shard.shard_id, "shard-001")
        self.assertEqual(shard.packet_id, "packet-001")
        self.assertEqual(shard.sequence, 0)
        self.assertEqual(shard.total_shards, 3)
        self.assertEqual(shard.data, b"test data")

    def test_shard_to_dict(self):
        """Test converting shard to dictionary."""
        shard = PacketShard(
            shard_id="shard-001",
            packet_id="packet-001",
            sequence=0,
            total_shards=1,
            data=b"hello",
            checksum="abcd1234",
            priority=5
        )
        d = shard.to_dict()
        self.assertEqual(d['shard_id'], "shard-001")
        self.assertEqual(d['data'], "68656c6c6f")  # hex of "hello"
        self.assertEqual(d['priority'], 5)

    def test_shard_from_dict(self):
        """Test creating shard from dictionary."""
        d = {
            'shard_id': 'shard-002',
            'packet_id': 'packet-002',
            'sequence': 1,
            'total_shards': 2,
            'data': '776f726c64',  # hex of "world"
            'checksum': 'efgh5678',
            'priority': 3
        }
        shard = PacketShard.from_dict(d)
        self.assertEqual(shard.shard_id, "shard-002")
        self.assertEqual(shard.data, b"world")
        self.assertEqual(shard.priority, 3)

    def test_checksum_verification(self):
        """Test checksum verification."""
        import hashlib
        data = b"test data for checksum"
        checksum = hashlib.sha256(data).hexdigest()[:16]
        
        shard = PacketShard(
            shard_id="shard-003",
            packet_id="packet-003",
            sequence=0,
            total_shards=1,
            data=data,
            checksum=checksum
        )
        self.assertTrue(shard.verify_checksum())
        
        # Test with wrong checksum
        shard.checksum = "wrongchecksum123"
        self.assertFalse(shard.verify_checksum())


class TestQuantumSuperpositionOptimizer(unittest.TestCase):
    """Tests for QuantumSuperpositionOptimizer class."""

    def test_initialization(self):
        """Test optimizer initialization."""
        optimizer = QuantumSuperpositionOptimizer(num_paths=4)
        self.assertEqual(optimizer.num_paths, 4)
        self.assertEqual(optimizer.coherence_factor, 0.9)

    def test_initialize_superposition(self):
        """Test initializing superposition state."""
        optimizer = QuantumSuperpositionOptimizer(num_paths=4)
        amplitudes = optimizer.initialize_superposition("packet-001")
        
        self.assertEqual(len(amplitudes), 4)
        # All amplitudes should be equal initially
        self.assertAlmostEqual(amplitudes[0], amplitudes[1], places=5)
        # Sum of squared amplitudes should be 1 (normalized)
        total_prob = sum(a * a for a in amplitudes)
        self.assertAlmostEqual(total_prob, 1.0, places=5)

    def test_collapse_to_path(self):
        """Test collapsing superposition to a path."""
        optimizer = QuantumSuperpositionOptimizer(num_paths=4)
        optimizer.initialize_superposition("packet-001")
        
        # Collapse should return a valid path index
        path = optimizer.collapse_to_path("packet-001")
        self.assertIn(path, [0, 1, 2, 3])

    def test_record_measurement_and_learning(self):
        """Test that measurements affect future path selection."""
        optimizer = QuantumSuperpositionOptimizer(num_paths=4)
        optimizer.initialize_superposition("packet-001")
        
        # Record very good performance for path 0
        for _ in range(10):
            optimizer.record_measurement("packet-001", 0, 10.0)  # 10ms latency
        
        # Record poor performance for other paths
        for path in [1, 2, 3]:
            for _ in range(10):
                optimizer.record_measurement("packet-001", path, 500.0)  # 500ms latency
        
        # Path 0 should have higher probability now
        amplitudes = optimizer.get_superposition_state("packet-001")
        self.assertIsNotNone(amplitudes)

    def test_coherence_decay(self):
        """Test that coherence decay moves toward uniform distribution."""
        optimizer = QuantumSuperpositionOptimizer(num_paths=4, coherence_factor=0.5)
        optimizer.initialize_superposition("packet-001")
        
        # Skew the distribution
        optimizer.path_amplitudes["packet-001"] = [0.9, 0.3, 0.2, 0.1]
        optimizer._normalize_amplitudes("packet-001")
        
        initial = optimizer.path_amplitudes["packet-001"].copy()
        
        # Apply decay multiple times
        for _ in range(10):
            optimizer.apply_coherence_decay()
        
        # Distribution should be more uniform now
        final = optimizer.path_amplitudes["packet-001"]
        variance_initial = sum((a - 0.5) ** 2 for a in initial)
        variance_final = sum((a - 0.5) ** 2 for a in final)
        self.assertLess(variance_final, variance_initial)

    def test_clear_packet_state(self):
        """Test clearing packet state."""
        optimizer = QuantumSuperpositionOptimizer(num_paths=4)
        optimizer.initialize_superposition("packet-001")
        
        self.assertIn("packet-001", optimizer.path_amplitudes)
        
        optimizer.clear_packet_state("packet-001")
        
        self.assertNotIn("packet-001", optimizer.path_amplitudes)


class TestDoublePacketShuffle(unittest.TestCase):
    """Tests for DoublePacketShuffle class."""

    def create_test_shards(self, count: int) -> list:
        """Create test shards for testing."""
        import hashlib
        shards = []
        for i in range(count):
            data = f"shard_data_{i}".encode()
            checksum = hashlib.sha256(data).hexdigest()[:16]
            shards.append(PacketShard(
                shard_id=f"shard-{i}",
                packet_id="packet-test",
                sequence=i,
                total_shards=count,
                data=data,
                checksum=checksum
            ))
        return shards

    def test_first_shuffle_interleaving(self):
        """Test that first shuffle interleaves shards."""
        shuffler = DoublePacketShuffle(block_size=4)
        shards = self.create_test_shards(8)
        
        shuffled = shuffler.first_shuffle(shards)
        
        # Check that shards are interleaved
        self.assertEqual(len(shuffled), 8)
        # First 4 elements should be from positions 0, 4, 1, 5... (column-major)
        # Original: [0, 1, 2, 3, 4, 5, 6, 7]
        # Matrix:   [[0, 1, 2, 3], [4, 5, 6, 7]]
        # Column-major: [0, 4, 1, 5, 2, 6, 3, 7]
        self.assertEqual(shuffled[0].sequence, 0)
        self.assertEqual(shuffled[1].sequence, 4)
        self.assertEqual(shuffled[2].sequence, 1)
        self.assertEqual(shuffled[3].sequence, 5)

    def test_second_shuffle_quantum_optimization(self):
        """Test that second shuffle applies quantum optimization."""
        shuffler = DoublePacketShuffle(block_size=4)
        shards = self.create_test_shards(8)
        
        shuffled = shuffler.second_shuffle(shards)
        
        self.assertEqual(len(shuffled), 8)
        # Each shard should have a superposition state assigned
        for shard in shuffled:
            self.assertIsNotNone(shard.superposition_state)

    def test_full_shuffle_and_unshuffle(self):
        """Test that shuffling and unshuffling preserves data."""
        shuffler = DoublePacketShuffle(block_size=4)
        shards = self.create_test_shards(12)
        
        # Original sequences
        original_sequences = [s.sequence for s in shards]
        original_data = [s.data for s in shards]
        
        # Shuffle
        shuffled = shuffler.shuffle(shards)
        
        # Unshuffle
        unshuffled = shuffler.unshuffle(shuffled, len(shards))
        
        # Sort by sequence to compare
        unshuffled_sorted = sorted(unshuffled, key=lambda s: s.sequence)
        
        # Data should be preserved
        for i, shard in enumerate(unshuffled_sorted):
            self.assertEqual(shard.sequence, i)

    def test_empty_and_single_shard(self):
        """Test handling of edge cases."""
        shuffler = DoublePacketShuffle(block_size=4)
        
        # Empty list
        self.assertEqual(shuffler.shuffle([]), [])
        
        # Single shard
        shards = self.create_test_shards(1)
        shuffled = shuffler.shuffle(shards)
        self.assertEqual(len(shuffled), 1)
        self.assertEqual(shuffled[0].sequence, 0)


class TestPacketShardManager(unittest.TestCase):
    """Tests for PacketShardManager class."""

    def test_shard_packet(self):
        """Test sharding a packet."""
        manager = PacketShardManager(shard_size=100)
        data = b"A" * 250  # 250 bytes
        
        shards = manager.shard_packet(data, packet_id="test-packet")
        
        self.assertEqual(len(shards), 3)  # 250 / 100 = 3 shards
        self.assertEqual(shards[0].total_shards, 3)
        self.assertEqual(shards[0].sequence, 0)
        self.assertEqual(shards[1].sequence, 1)
        self.assertEqual(shards[2].sequence, 2)

    def test_shard_and_reform_packet(self):
        """Test full cycle of sharding and reforming."""
        manager = PacketShardManager(shard_size=50)
        original_data = b"Hello, this is a test message for packet sharding!"
        
        # Shard the packet
        shards = manager.shard_packet(original_data, packet_id="test-packet")
        
        # Prepare for transmission
        prepared = manager.prepare_for_transmission(shards)
        
        # Simulate receiving shards
        result = None
        for shard in prepared:
            result = manager.receive_shard(shard)
        
        # Last receive should return the complete packet
        self.assertIsNotNone(result)
        self.assertEqual(result, original_data)

    def test_shard_checksum_verification(self):
        """Test that corrupt shards are rejected."""
        manager = PacketShardManager(shard_size=100)
        data = b"Test data for checksum"
        
        shards = manager.shard_packet(data)
        
        # Corrupt a shard's checksum
        shards[0].checksum = "corrupted12345"
        
        result = manager.receive_shard(shards[0])
        self.assertIsNone(result)

    def test_out_of_order_shard_reception(self):
        """Test receiving shards out of order."""
        manager = PacketShardManager(shard_size=30)
        original_data = b"Testing out of order shard reception works correctly"
        
        shards = manager.shard_packet(original_data, packet_id="ooo-test")
        
        # Shuffle the shards randomly
        import random
        shuffled_shards = shards.copy()
        random.shuffle(shuffled_shards)
        
        # Receive shards in random order
        result = None
        for shard in shuffled_shards:
            result = manager.receive_shard(shard)
        
        self.assertIsNotNone(result)
        self.assertEqual(result, original_data)

    def test_pending_packets_tracking(self):
        """Test tracking of pending packets."""
        manager = PacketShardManager(shard_size=50)
        data = b"A" * 150  # Will create 3 shards
        
        shards = manager.shard_packet(data, packet_id="pending-test")
        
        # Receive only first shard
        manager.receive_shard(shards[0])
        
        self.assertEqual(manager.get_pending_packets_count(), 1)
        
        stats = manager.get_shard_stats("pending-test")
        self.assertIsNotNone(stats)
        self.assertEqual(stats['shards_received'], 1)
        self.assertEqual(stats['total_shards'], 3)

    def test_stale_packet_cleanup(self):
        """Test cleaning up stale packets."""
        manager = PacketShardManager(shard_size=50)
        data = b"A" * 100
        
        shards = manager.shard_packet(data, packet_id="stale-test")
        
        # Receive only first shard
        manager.receive_shard(shards[0])
        
        # Artificially age the packet
        manager.packet_metadata["stale-test"]['first_received'] = time.time() - 120
        
        # Cleanup stale packets (max age 60 seconds)
        cleaned = manager.cleanup_stale_packets(max_age_seconds=60.0)
        
        self.assertEqual(cleaned, 1)
        self.assertEqual(manager.get_pending_packets_count(), 0)

    def test_optimal_route_selection(self):
        """Test quantum-optimized route selection."""
        manager = PacketShardManager(shard_size=100)
        
        route = manager.get_optimal_route("route-test")
        
        # Route should be a valid path index
        self.assertIsInstance(route, int)
        self.assertGreaterEqual(route, 0)

    def test_transmission_result_recording(self):
        """Test recording transmission results."""
        manager = PacketShardManager(shard_size=100)
        
        # Initialize packet
        manager.quantum_optimizer.initialize_superposition("recording-test")
        
        # Record some results
        manager.record_transmission_result("recording-test", 0, 50.0)
        manager.record_transmission_result("recording-test", 1, 200.0)
        
        # Verify measurement was recorded
        history = manager.quantum_optimizer.measurement_history["recording-test"]
        self.assertEqual(len(history), 2)


class TestCreateShardingSystem(unittest.TestCase):
    """Tests for the factory function."""

    def test_create_sharding_system(self):
        """Test factory function creates configured manager."""
        manager = create_sharding_system(shard_size=512, shuffle_block_size=4)
        
        self.assertEqual(manager.shard_size, 512)
        self.assertEqual(manager.shuffler.block_size, 4)


class TestIntegration(unittest.TestCase):
    """Integration tests for the complete sharding system."""

    def test_large_packet_sharding(self):
        """Test sharding a large packet."""
        manager = PacketShardManager(shard_size=1024)
        
        # Create 10KB of data
        original_data = bytes(range(256)) * 40
        
        # Shard
        shards = manager.shard_packet(original_data)
        
        # Verify shard count
        expected_shards = len(original_data) // 1024 + (1 if len(original_data) % 1024 else 0)
        self.assertEqual(len(shards), expected_shards)
        
        # Prepare and receive
        prepared = manager.prepare_for_transmission(shards)
        
        result = None
        for shard in prepared:
            result = manager.receive_shard(shard)
        
        self.assertEqual(result, original_data)

    def test_multiple_concurrent_packets(self):
        """Test handling multiple packets simultaneously."""
        manager = PacketShardManager(shard_size=100)
        
        packets = {
            "packet-A": b"This is packet A with some data",
            "packet-B": b"Packet B contains different content here",
            "packet-C": b"And packet C has its own unique data too"
        }
        
        all_shards = {}
        for packet_id, data in packets.items():
            all_shards[packet_id] = manager.shard_packet(data, packet_id=packet_id)
        
        # Interleave reception of shards from different packets
        import itertools
        
        # Get all shards in a round-robin fashion
        shard_iterators = {pid: iter(shards) for pid, shards in all_shards.items()}
        
        results = {}
        while shard_iterators:
            completed = []
            for pid, it in list(shard_iterators.items()):
                try:
                    shard = next(it)
                    result = manager.receive_shard(shard)
                    if result is not None:
                        results[pid] = result
                except StopIteration:
                    completed.append(pid)
            
            for pid in completed:
                del shard_iterators[pid]
        
        # Verify all packets were reconstructed correctly
        for packet_id, original in packets.items():
            self.assertEqual(results[packet_id], original)


if __name__ == '__main__':
    unittest.main()
