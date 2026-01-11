#!/bin/bash
# Test script for Buster Cluster - Autonomous Distribution System

echo "======================================"
echo "Buster Cluster Test Suite"
echo "======================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counter
TESTS_PASSED=0
TESTS_FAILED=0

# Helper function to run tests
# Note: This uses eval for flexibility in test commands. All commands are 
# hardcoded in this test script and not from user input.
run_test() {
    local test_name="$1"
    local command="$2"
    local expected_exit="$3"
    
    echo -n "Test: $test_name... "
    
    # Run the hardcoded command
    bash -c "$command" > /tmp/buster_test_output.txt 2>&1
    local actual_exit=$?
    
    if [ "$actual_exit" -eq "$expected_exit" ]; then
        echo -e "${GREEN}PASSED${NC}"
        ((TESTS_PASSED++))
        return 0
    else
        echo -e "${RED}FAILED${NC}"
        echo "  Expected exit code: $expected_exit, Got: $actual_exit"
        echo "  Output:"
        head -5 /tmp/buster_test_output.txt | sed 's/^/    /'
        ((TESTS_FAILED++))
        return 1
    fi
}

# Helper function to check output content
# Note: Commands are hardcoded in this test script.
check_output() {
    local test_name="$1"
    local command="$2"
    local expected_content="$3"
    
    echo -n "Test: $test_name... "
    
    # Run the hardcoded command
    bash -c "$command" > /tmp/buster_test_output.txt 2>&1
    
    if grep -q -F -- "$expected_content" /tmp/buster_test_output.txt; then
        echo -e "${GREEN}PASSED${NC}"
        ((TESTS_PASSED++))
        return 0
    else
        echo -e "${RED}FAILED${NC}"
        echo "  Expected to find: $expected_content"
        echo "  Output:"
        head -10 /tmp/buster_test_output.txt | sed 's/^/    /'
        ((TESTS_FAILED++))
        return 1
    fi
}

echo "--- Python Syntax Check ---"
run_test "Python syntax validation" "python3 -m py_compile buster_cluster.py" 0

echo ""
echo "--- Help and CLI Tests ---"
check_output "Help output" "python3 buster_cluster.py --help" "Buster Cluster"
check_output "Help shows cluster arg" "python3 buster_cluster.py --help" "--cluster"
check_output "Help shows node-id arg" "python3 buster_cluster.py --help" "--node-id"
check_output "Help shows autonomous arg" "python3 buster_cluster.py --help" "--autonomous"

echo ""
echo "--- Status Mode Tests ---"
check_output "Status output (JSON)" "python3 buster_cluster.py --cluster test --node-id test1 --use-sample-networks --status-only" "cluster_name"
check_output "Status shows networks" "python3 buster_cluster.py --cluster test --node-id test1 --use-sample-networks --status-only" "registered_networks"
check_output "Status shows GCP network" "python3 buster_cluster.py --cluster test --node-id test1 --use-sample-networks --status-only" "gcp-us-central1"

echo ""
echo "--- Module Import Test ---"
run_test "Module import" "python3 -c 'import buster_cluster; print(\"Import OK\")'" 0

echo ""
echo "--- Class Instantiation Tests ---"
run_test "BusterCluster class" "python3 -c 'from buster_cluster import BusterCluster; bc = BusterCluster(\"test\", \"node1\"); print(bc.cluster_name)'" 0
run_test "SecurityAssessor class" "python3 -c 'from buster_cluster import SecurityAssessor; sa = SecurityAssessor(); print(\"OK\")'" 0
run_test "NetworkSpeedAnalyzer class" "python3 -c 'from buster_cluster import NetworkSpeedAnalyzer; na = NetworkSpeedAnalyzer(); print(\"OK\")'" 0
run_test "AutonomousDecisionEngine class" "python3 -c 'from buster_cluster import AutonomousDecisionEngine; de = AutonomousDecisionEngine(); print(\"OK\")'" 0

echo ""
echo "--- CloudNetwork Tests ---"
run_test "CloudNetwork creation" "python3 -c '
from buster_cluster import CloudNetwork, SecurityLevel, NetworkStatus
cn = CloudNetwork(
    network_id=\"test\",
    name=\"Test Network\",
    region=\"us-central1\",
    provider=\"gcp\",
    endpoint=\"test.example.com\"
)
assert cn.network_id == \"test\"
assert cn.security_level == SecurityLevel.MEDIUM
print(\"OK\")
'" 0

run_test "CloudNetwork to_dict" "python3 -c '
from buster_cluster import CloudNetwork
cn = CloudNetwork(
    network_id=\"test\",
    name=\"Test Network\",
    region=\"us-central1\",
    provider=\"gcp\",
    endpoint=\"test.example.com\"
)
d = cn.to_dict()
assert \"network_id\" in d
assert \"security_level\" in d
print(\"OK\")
'" 0

echo ""
echo "--- Security Assessor Tests ---"
run_test "Security assessment" "python3 -c '
from buster_cluster import SecurityAssessor, CloudNetwork, SecurityLevel
sa = SecurityAssessor()
cn = CloudNetwork(
    network_id=\"test\",
    name=\"Test Network\",
    region=\"us-central1\",
    provider=\"gcp\",
    endpoint=\"test.example.com\"
)
level, findings = sa.assess_network(cn)
assert isinstance(level, SecurityLevel)
assert isinstance(findings, list)
print(\"OK\")
'" 0

run_test "TLS security bonus" "python3 -c '
from buster_cluster import SecurityAssessor, CloudNetwork, SecurityLevel
sa = SecurityAssessor()
cn_tls = CloudNetwork(
    network_id=\"test-tls\",
    name=\"TLS Network\",
    region=\"us-central1\",
    provider=\"gcp\",
    endpoint=\"wss://test.example.com\"
)
cn_plain = CloudNetwork(
    network_id=\"test-plain\",
    name=\"Plain Network\",
    region=\"us-central1\",
    provider=\"gcp\",
    endpoint=\"ws://test.example.com\"
)
level_tls, _ = sa.assess_network(cn_tls)
level_plain, _ = sa.assess_network(cn_plain)
assert level_tls.value >= level_plain.value, f\"TLS should be >= plain: {level_tls.value} vs {level_plain.value}\"
print(\"OK\")
'" 0

echo ""
echo "--- Decision Engine Tests ---"
run_test "Decision engine initialization" "python3 -c '
from buster_cluster import AutonomousDecisionEngine
de = AutonomousDecisionEngine(security_weight=0.6, performance_weight=0.4)
assert de.security_weight == 0.6
assert de.performance_weight == 0.4
print(\"OK\")
'" 0

run_test "Network scoring" "python3 -c '
from buster_cluster import AutonomousDecisionEngine, CloudNetwork, SecurityLevel
de = AutonomousDecisionEngine()
cn = CloudNetwork(
    network_id=\"test\",
    name=\"Test Network\",
    region=\"us-central1\",
    provider=\"gcp\",
    endpoint=\"test.example.com\"
)
performance = {\"overall_score\": 80}
score = de.calculate_network_score(cn, SecurityLevel.HIGH, performance)
assert 0 <= score <= 100, f\"Score should be 0-100: {score}\"
print(f\"Score: {score}\")
'" 0

run_test "Optimal network selection" "python3 -c '
from buster_cluster import AutonomousDecisionEngine, CloudNetwork, SecurityLevel
de = AutonomousDecisionEngine()
networks = [
    CloudNetwork(network_id=\"n1\", name=\"Net1\", region=\"r1\", provider=\"gcp\", endpoint=\"e1\"),
    CloudNetwork(network_id=\"n2\", name=\"Net2\", region=\"r2\", provider=\"aws\", endpoint=\"e2\")
]
security = {\"n1\": SecurityLevel.HIGH, \"n2\": SecurityLevel.LOW}
performance = {\"n1\": {\"overall_score\": 90}, \"n2\": {\"overall_score\": 50}}
optimal = de.decide_optimal_network(networks, security, performance)
assert optimal is not None
assert optimal.network_id == \"n1\", f\"Expected n1, got {optimal.network_id}\"
print(\"OK\")
'" 0

echo ""
echo "--- Async Tests ---"
run_test "Async speed analyzer" "python3 -c '
import asyncio
from buster_cluster import NetworkSpeedAnalyzer, CloudNetwork

async def test():
    na = NetworkSpeedAnalyzer()
    cn = CloudNetwork(
        network_id=\"test\",
        name=\"Test Network\",
        region=\"us-central1\",
        provider=\"gcp\",
        endpoint=\"test.example.com\"
    )
    latency = await na.measure_latency(cn)
    assert latency > 0, f\"Latency should be positive: {latency}\"
    bandwidth = await na.measure_bandwidth(cn)
    assert bandwidth > 0, f\"Bandwidth should be positive: {bandwidth}\"
    print(f\"Latency: {latency:.2f}ms, Bandwidth: {bandwidth:.2f}Mbps\")

asyncio.run(test())
'" 0

run_test "Async optimization cycle" "python3 -c '
import asyncio
from buster_cluster import BusterCluster, create_sample_networks

async def test():
    cluster = BusterCluster(cluster_name=\"test\", node_id=\"node1\")
    for network in create_sample_networks():
        cluster.register_network(network)
    
    result = await cluster.optimization_cycle_task()
    assert result.cycle_id == 1
    assert result.decisions_made >= 0
    print(f\"Cycle {result.cycle_id}: {result.decisions_made} decisions\")

asyncio.run(test())
'" 0

echo ""
echo "--- Integration Tests ---"
run_test "Full cluster status" "python3 -c '
from buster_cluster import BusterCluster, create_sample_networks
cluster = BusterCluster(cluster_name=\"test\", node_id=\"node1\")
for network in create_sample_networks():
    cluster.register_network(network)
status = cluster.get_status()
assert status[\"cluster_name\"] == \"test\"
assert status[\"node_id\"] == \"node1\"
assert status[\"registered_networks\"] == 4
print(\"OK\")
'" 0

run_test "Custom network registration" "python3 -c '
from buster_cluster import BusterCluster, CloudNetwork
cluster = BusterCluster(cluster_name=\"custom\", node_id=\"node1\")
network = CloudNetwork(
    network_id=\"custom-net\",
    name=\"Custom Network\",
    region=\"custom-region\",
    provider=\"private\",
    endpoint=\"custom.local\"
)
cluster.register_network(network)
assert \"custom-net\" in cluster.networks
cluster.unregister_network(\"custom-net\")
assert \"custom-net\" not in cluster.networks
print(\"OK\")
'" 0

echo ""
echo "======================================"
echo "Test Summary"
echo "======================================"
echo -e "Passed: ${GREEN}${TESTS_PASSED}${NC}"
echo -e "Failed: ${RED}${TESTS_FAILED}${NC}"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}All tests passed!${NC}"
    exit 0
else
    echo -e "${RED}Some tests failed!${NC}"
    exit 1
fi
